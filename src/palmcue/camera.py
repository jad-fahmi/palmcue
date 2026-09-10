"""Capture and tracking live in a disposable process, isolated from the GUI.

A single-slot mailbox prevents stale frames from accumulating. Frames are never
saved. A stalled driver can be stopped without terminating the desktop interface.
"""

import multiprocessing as mp
import queue
import time
from dataclasses import dataclass
from pathlib import Path

from palmcue.geometry import Observation, Point, classify


@dataclass
class Frame:
    captured: float
    observation: Observation | None
    hands: int
    rgb: bytes
    width: int
    height: int
    camera: int
    landmarks: tuple[Point, ...] = ()


def _latest(mailbox, value):
    try:
        mailbox.put_nowait(value)
    except queue.Full:
        try:
            mailbox.get_nowait()
        except queue.Empty:
            pass
        try:
            mailbox.put_nowait(value)
        except queue.Full:
            pass


def _capture(mailbox, messages, stop, index: int, mirror: bool, scan: bool):
    cap = detector = None
    try:
        import cv2
        import mediapipe as mediapipe
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            HandLandmarker,
            HandLandmarkerOptions,
            RunningMode,
        )

        model = Path(__file__).parent / "assets" / "hand_landmarker.task"
        if not model.is_file():
            messages.put(("error", "PalmCue's hand tracking file is missing. Reinstall PalmCue."))
            return
        messages.put(("status", "Looking for your camera…"))
        available = []
        indices = range(6) if index < 0 or scan else [index]
        for candidate in indices:
            if stop.is_set():
                return
            probe = cv2.VideoCapture(candidate, cv2.CAP_DSHOW)
            if probe.isOpened():
                ok, _ = probe.read()
                if ok:
                    available.append(candidate)
                    if not scan:
                        cap, index = probe, candidate
                        break
            probe.release()
        messages.put(("cameras", available))
        if cap is None and available:
            index = index if index in available else available[0]
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap is None or not cap.isOpened():
            messages.put(
                (
                    "error",
                    "No camera is available. Connect a webcam, close other camera "
                    "apps, and allow desktop camera access in Windows Settings. Then retry.",
                )
            )
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        detector = HandLandmarker.create_from_options(
            HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model)),
                running_mode=RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7,
            )
        )
        messages.put(("status", "Camera ready · everything stays on this computer"))
        previous_ms = 0
        failures = 0
        while not stop.is_set():
            ok, bgr = cap.read()
            captured = time.monotonic()
            if not ok:
                failures += 1
                if failures >= 5:
                    messages.put(
                        ("error", "The camera disconnected. Reconnect it and choose Retry.")
                    )
                    break
                stop.wait(0.03)
                continue
            failures = 0
            if mirror:
                bgr = cv2.flip(bgr, 1)
            # Bound inference and IPC costs even if a driver ignores the requested size.
            height, width = bgr.shape[:2]
            if width > 640:
                bgr = cv2.resize(bgr, (640, round(height * 640 / width)))
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            height, width = rgb.shape[:2]
            stamp = max(previous_ms + 1, int(captured * 1000))
            previous_ms = stamp
            result = detector.detect_for_video(
                mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=rgb), stamp
            )
            hands = len(result.hand_landmarks)
            landmarks = tuple(Point(p.x, p.y, p.z) for hand in result.hand_landmarks for p in hand)
            observation = None
            if hands == 1:
                observation = classify(
                    [Point(p.x, p.y, p.z) for p in result.hand_landmarks[0]], width / height
                )
            _latest(
                mailbox,
                Frame(captured, observation, hands, rgb.tobytes(), width, height, index, landmarks),
            )
    except Exception as error:
        messages.put(
            (
                "error",
                "Hand tracking could not start. Restart PalmCue or reinstall it if this continues.",
            )
        )
        messages.put(("diagnostic", f"{type(error).__name__}: {error}"))
    finally:
        if detector is not None:
            detector.close()
        if cap is not None:
            cap.release()


class CameraService:
    def __init__(self):
        self.process = None
        self.mailbox = self.messages = self.stop_event = None

    def start(self, index=-1, mirror=True, scan=False):
        self.stop()
        ctx = mp.get_context("spawn")
        self.mailbox, self.messages, self.stop_event = ctx.Queue(1), ctx.Queue(), ctx.Event()
        self.process = ctx.Process(
            target=_capture,
            args=(self.mailbox, self.messages, self.stop_event, index, mirror, scan),
            daemon=True,
        )
        self.process.start()

    def poll(self) -> tuple[Frame | None, list[tuple[str, object]]]:
        frame, messages = None, []
        if self.mailbox is not None:
            try:
                frame = self.mailbox.get_nowait()
            except queue.Empty:
                pass
            while True:
                try:
                    messages.append(self.messages.get_nowait())
                except queue.Empty:
                    break
        return frame, messages

    def stop(self):
        if self.process is not None:
            self.stop_event.set()
            self.process.join(timeout=0.15)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=0.3)
            self.process.close()
            self.process = None
            for mailbox in (self.mailbox, self.messages):
                mailbox.close()
                mailbox.cancel_join_thread()
            self.mailbox = self.messages = self.stop_event = None
