"""GUI-thread coordinator: lifecycle, fresh observations, and practice feedback."""

import time

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QImage

from palmcue.camera import CameraService
from palmcue.controller import Action, Controller


class Runtime(QObject):
    def __init__(self, window, camera=None):
        super().__init__(window)
        self.window = window
        self.camera = camera or CameraService()
        self.controller = Controller(window.settings)
        self.running = False
        self.started = 0.0
        self.last_frame = 0.0
        self.fresh = False
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.poll)
        self.timer.start()
        window.camera_button.clicked.connect(self.toggle_camera)
        window.lock_button.clicked.connect(self.lock)
        window.scan_button.clicked.connect(lambda: self.start_camera(scan=True))
        window.refresh_targets.setEnabled(False)

    def toggle_camera(self):
        if self.running:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self, scan=False):
        self.stop_camera()
        self.window.show_notice("")
        self.running = True
        self.started = time.monotonic()
        self.window.camera_button.setText("Cancel camera setup")
        self.window.camera_badge.setText("CONNECTING")
        self.window.camera_status.setText("Looking for an available camera…")
        self.window.preview.message = "Finding your camera…"
        self.window.preview.detail = "This may take a few seconds."
        self.window.preview.update()
        try:
            self.camera.start(self.window.settings.camera, self.window.settings.mirror, scan)
        except (OSError, RuntimeError):
            self.camera_error("The camera could not start. Close other camera apps and retry.")

    def stop_camera(self):
        self.running = False
        self.fresh = False
        self.last_frame = 0.0
        self.lock()
        self.camera.stop()
        self.window.camera_button.setText("Start camera")
        self.window.camera_badge.setText("CAMERA OFF")
        self.window.preview.image = QImage()
        self.window.preview.message = "Your camera is off"
        self.window.preview.detail = "Start when you're ready. Nothing is recorded."
        self.window.preview.update()

    def lock(self):
        self.controller.lock()
        self.window.gesture_status.setText("Hold an open palm to unlock")
        self.window.progress.setValue(0)
        self.window.deck.pointer = None
        self.window.deck.update()

    def reconfigure(self, changes):
        self.controller = Controller(self.window.settings)
        self.lock()
        if self.running and any(key in changes for key in ("camera", "mirror")):
            self.start_camera()

    def camera_error(self, message):
        self.stop_camera()
        self.window.show_notice(message)
        self.window.camera_status.setText(message)
        self.window.camera_button.setText("Retry camera")
        self.window.preview.message = "Let's reconnect your camera"
        self.window.preview.detail = "Check the connection and camera access, then retry."
        self.window.preview.update()

    def poll(self):
        if not self.running:
            return
        now = time.monotonic()
        frame, messages = self.camera.poll()
        for kind, value in messages:
            if kind == "error":
                self.camera_error(str(value))
                return
            if kind == "status":
                self.window.camera_status.setText(str(value))
            if kind == "diagnostic":
                self.window.diagnostics.setText(str(value))
            if kind == "cameras":
                self.update_cameras(value)
        if frame is None:
            if self.last_frame and now - self.last_frame > 0.7:
                self.fresh = False
                self.lock()
                self.window.camera_status.setText("Waiting for the camera · controls locked")
            if now - (self.last_frame or self.started) > (4 if self.last_frame else 25):
                self.camera_error(
                    "The camera is not responding. Reconnect it, close other "
                    "camera apps, and retry."
                )
            return
        # Never dispatch delayed input after inference, GUI stalls, or suspend/resume.
        if now - frame.captured > 0.3 or frame.captured > now:
            self.fresh = False
            self.lock()
            if now - (self.last_frame or self.started) > 5:
                self.camera_error(
                    "The camera is too slow for safe controls. Close busy apps "
                    "or try another webcam."
                )
            return
        self.last_frame = frame.captured
        self.fresh = True
        self.window.camera_button.setText("Stop camera")
        self.window.camera_badge.setText("CAMERA ON")
        if self.window.isVisible() and self.window.stack.currentIndex() == 0:
            self.window.preview.image = QImage(
                frame.rgb, frame.width, frame.height, frame.width * 3, QImage.Format.Format_RGB888
            ).copy()
            self.window.preview.update()
        events = self.controller.update(frame.observation, frame.captured, frame.hands)
        self.window.gesture_status.setText(self.controller.hint)
        self.window.progress.setValue(round(self.controller.progress * 100))
        for event in events:
            self.handle_event(event)
        pose = frame.observation.pose.value if frame.observation else "No clear hand"
        self.window.diagnostics.setText(
            f"Camera {frame.camera + 1} · {frame.width} × {frame.height}\n"
            f"Frame age: {round((now - frame.captured) * 1000)} ms · Hands: {frame.hands}\n"
            f"Pose: {pose} · Locked: {self.controller.locked}"
        )

    def handle_event(self, event):
        self.window.deck.apply(event)
        if event.action != Action.POINTER:
            self.window.last_action.setText(event.action.value)

    def update_cameras(self, indices):
        combo = self.window.cameras
        current = self.window.settings.camera
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Automatic · find an available webcam", -1)
        for index in indices:
            combo.addItem(f"Camera {index + 1}", index)
        if current >= 0 and current not in indices:
            combo.addItem(f"Camera {current + 1} · unavailable", current)
        combo.setCurrentIndex(max(0, combo.findData(current)))
        combo.blockSignals(False)

    def close(self):
        self.timer.stop()
        self.stop_camera()
