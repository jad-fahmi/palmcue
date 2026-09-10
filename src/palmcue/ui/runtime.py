"""GUI-thread coordinator: lifecycle, fresh observations, and practice feedback."""

import time

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QCursor, QImage

from palmcue.actions import Dispatcher, OutputBlocked
from palmcue.camera import CameraService
from palmcue.controller import Action, Controller
from palmcue.session import Session


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
        self.session = None
        self.backend = None
        self.auto_armed = True
        self.last_auto_check = 0.0
        self.automatic_session = False
        self.desktop = None
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.poll)
        self.timer.start()
        window.camera_button.clicked.connect(self.toggle_camera)
        window.lock_button.clicked.connect(self.pause_gestures)
        window.scan_button.clicked.connect(lambda: self.start_camera(scan=True))
        window.refresh_targets.setEnabled(False)
        window.preview.debug = window.settings.debug_preview

    def connect_desktop(self, backend):
        from palmcue.ui.desktop import Desktop

        self.backend = backend
        self.session = Session(Dispatcher(backend))
        self.desktop = Desktop(self.window, backend, self.stop_presenting)
        self.window.refresh_targets.setEnabled(True)
        self.window.refresh_targets.clicked.connect(self.refresh_targets)
        self.window.present_button.clicked.connect(lambda: self.start_presenting())
        self.window.stop_button.clicked.connect(self.stop_presenting)
        self.window.targets.currentIndexChanged.connect(self.update_present_controls)
        self.refresh_targets()
        if not self.desktop.shortcut.registered:
            self.window.show_notice(
                "Ctrl + Alt + Space is already used by another app. "
                "Use the tray menu to stop presenting."
            )

    def refresh_targets(self):
        combo = self.window.targets
        combo.clear()
        for target in self.backend.windows():
            combo.addItem(target.title, target)
        if combo.count() == 0:
            combo.addItem("Open your slideshow, then refresh", None)
        self.update_present_controls()

    def update_present_controls(self):
        self.window.present_camera_button.setText(
            "Stop camera"
            if self.fresh
            else "Cancel camera setup"
            if self.running
            else "Start camera"
        )
        busy = bool(self.session and (self.session.active or self.session.pending))
        self.window.present_button.setEnabled(
            self.fresh and not busy and self.window.targets.currentData() is not None
        )
        self.window.stop_button.setEnabled(busy)
        self.window.targets.setEnabled(not busy)
        self.window.refresh_targets.setEnabled(not busy)
        if not self.session or not self.fresh:
            self.window.session_step.setText("Start your camera to get ready")
        elif self.session.pending:
            self.window.session_step.setText("Step 3 · Bring your slideshow to the front")
        elif self.session.active and self.controller.locked:
            self.window.session_step.setText("Presentation ready · show your next gesture")
        elif self.session.active:
            self.window.session_step.setText("Presenting · hold two fingers for next slide")
        elif self.window.settings.auto_present or self.window.targets.currentData() is None:
            self.window.session_step.setText(
                "Camera ready · open your slides in fullscreen"
                if self.window.settings.auto_present
                else "Step 2 · Select your slideshow window"
            )
        else:
            self.window.session_step.setText("Step 3 · Start presenting")

    def start_presenting(self, target=None, automatic=False):
        target = target or self.window.targets.currentData()
        if not self.session or not self.fresh or target is None:
            return
        self.auto_armed = False
        self.automatic_session = automatic
        self.lock()
        self.session.start(target, time.monotonic())
        self.window.session_status.setText(
            "Fullscreen presentation detected · starting in 5 seconds"
            if automatic
            else "Switch to your slides · starting in 5 seconds"
        )
        self.window.session_step.setText(
            "Automatic · bring your slideshow to the front"
            if automatic
            else "Step 3 · Bring your slideshow to the front"
        )
        self.update_present_controls()
        self.window.showMinimized()
        if self.desktop and self.window.settings.presentation_feedback:
            self.desktop.hud.reset()
            self.desktop.hud.place(QCursor.pos())
            self.desktop.hud.display("Starting in 5…", "Keep your slideshow in front")

    def stop_presenting(self):
        was_busy = bool(self.session and (self.session.active or self.session.pending))
        if self.session:
            self.session.stop()
            self.controller.end_presentation()
            self.lock()
            self.window.session_status.setText("Stopped · your slides are untouched")
            self.update_present_controls()
        if self.desktop:
            self.desktop.hud.reset()
            if was_busy and self.window.settings.presentation_feedback:
                self.desktop.hud.display(
                    "PalmCue · Stopped", "Open PalmCue to start again", temporary=True
                )
            self.desktop.overlay.hide()
            self.desktop.tray.setToolTip("PalmCue · presentation stopped")
            self.desktop.status("stopped")
        self.auto_armed = False
        self.automatic_session = False

    def toggle_camera(self):
        if self.running:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self, scan=False):
        self.stop_camera()
        self.auto_armed = True
        self.window.show_notice("")
        self.window.session_status.setText("Connecting your camera…")
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
        self.stop_presenting()
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
        if self.session:
            self.update_present_controls()

    def lock(self):
        self.controller.lock()
        self.window.gesture_status.setText("Hold an open palm to unlock")
        self.window.progress.setValue(0)
        self.window.deck.pointer = None
        self.window.deck.update()
        if self.desktop:
            self.desktop.overlay.hide()

    def pause_gestures(self):
        self.controller.presentation_mode = False
        self.lock()

    def reconfigure(self, changes):
        if set(changes) <= {"presentation_feedback", "debug_preview", "onboarding_done"}:
            if self.desktop and not self.window.settings.presentation_feedback:
                self.desktop.hud.reset()
            return
        self.stop_presenting()
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
        if self.session:
            now = time.monotonic()
            self.auto_start_if_needed(now)
            was_active = self.session.active
            message = self.session.tick(now, self.fresh and now - self.last_frame < 0.7)
            if message:
                if self.session.active and not was_active:
                    self.controller.begin_presentation()
                elif not self.session.active:
                    self.controller.end_presentation()
                self.window.session_status.setText(message)
                if self.desktop and self.window.settings.presentation_feedback:
                    self.desktop.hud.reset()
                    if not self.session.active:
                        self.desktop.hud.display("PalmCue · Paused", message, temporary=True)
            if self.session.pending:
                seconds = max(1, int(self.session.deadline - now) + 1)
                self.window.session_status.setText(
                    f"Switch to your slides · starting in {seconds}s"
                )
                if self.desktop and self.window.settings.presentation_feedback:
                    self.desktop.hud.display(
                        f"Starting in {seconds}…", "Keep your slideshow in front", (5 - seconds) / 5
                    )
            self.update_present_controls()
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
        if self.window.session_status.text() in ("Connecting your camera…", "Your camera is off."):
            self.window.session_status.setText(
                "Camera connected · fullscreen slides will start a countdown"
            )
        self.window.camera_button.setText("Stop camera")
        self.window.camera_badge.setText("CAMERA ON")
        if (
            self.session
            and not self.session.active
            and not self.session.pending
            and not self.window.settings.auto_present
        ):
            self.window.session_status.setText("Camera ready · select your slideshow below")
        if self.window.isVisible() and self.window.stack.currentIndex() == 0:
            self.window.preview.image = QImage(
                frame.rgb, frame.width, frame.height, frame.width * 3, QImage.Format.Format_RGB888
            ).copy()
            self.window.preview.landmarks = (
                frame.landmarks if self.window.settings.debug_preview else ()
            )
            self.window.preview.update()
        if self.session and self.session.pending:
            self.lock()
            events = []
        else:
            events = self.controller.update(frame.observation, frame.captured, frame.hands)
        self.window.gesture_status.setText(self.controller.hint)
        self.window.progress.setValue(round(self.controller.progress * 100))
        for event in events:
            self.handle_event(event)
        if self.desktop and self.session.active and self.window.settings.presentation_feedback:
            hint = self.controller.hint
            if frame.hands == 0:
                hint = (
                    "Raise your hand into view"
                    if self.controller.locked
                    else "Ready when you are · raise your hand for a cue"
                )
            elif frame.hands > 1:
                hint = "Show just one hand"
            elif hint == "Move your hand inside the marked area":
                hint = (
                    "Move your hand toward the "
                    + {
                        "center": "center of the camera view",
                        "wide": "center of the camera view",
                        "left": "left side of the mirrored camera view",
                        "right": "right side of the mirrored camera view",
                    }[self.window.settings.area]
                )
            self.desktop.hud.feedback(self.controller.locked, hint, self.controller.progress)
        if self.desktop:
            state = "locked" if self.controller.locked else "ready"
            mode = "Presenting" if self.session.active else "Practice"
            self.desktop.tray.setToolTip(f"PalmCue · {mode} · controls {state}")
            self.desktop.status(state if self.session.active else "stopped")
            if self.controller.locked:
                self.desktop.overlay.hide()
        pose = frame.observation.pose.value if frame.observation else "No clear hand"
        self.window.diagnostics.setText(
            f"Camera {frame.camera + 1} · {frame.width} × {frame.height}\n"
            f"Frame age: {round((now - frame.captured) * 1000)} ms · Hands: {frame.hands}\n"
            f"Pose: {pose} · Locked: {self.controller.locked}"
        )

    def auto_start_if_needed(self, now=None):
        """Start a guarded session when a supported app enters true fullscreen."""
        if not self.session or not self.window.settings.auto_present or not self.fresh:
            return
        now = time.monotonic() if now is None else now
        if now - self.last_auto_check < 0.5 or now - self.last_frame > 0.7:
            return
        self.last_auto_check = now
        detector = getattr(self.backend, "fullscreen_presentation", None)
        target = detector() if detector else None
        if self.automatic_session and (self.session.active or self.session.pending):
            selected = self.session.pending or self.session.dispatcher.target
            if target != selected:
                self.stop_presenting()
                message = (
                    "Slides left fullscreen or lost focus. Return to fullscreen to start again."
                )
                self.window.session_status.setText(message)
                if self.desktop and self.window.settings.presentation_feedback:
                    self.desktop.hud.display("PalmCue · Paused", message, temporary=True)
                self.auto_armed = target is None
                return
        if target is None:
            self.auto_armed = True
            return
        if self.auto_armed and not self.session.active and not self.session.pending:
            self.start_presenting(target, automatic=True)

    def handle_event(self, event):
        if self.session and self.session.active:
            try:
                self.session.send(event)
                if (
                    self.desktop
                    and self.window.settings.presentation_feedback
                    and event.action not in (Action.POINTER, Action.LOCK, Action.UNLOCK)
                ):
                    self.desktop.hud.acknowledge(event.action.value)
                if event.action == Action.POINTER and self.desktop:
                    self.desktop.overlay.reveal()
            except (OutputBlocked, OSError) as error:
                self.stop_presenting()
                self.window.session_status.setText(str(error))
                self.window.show_notice(str(error))
        else:
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
        if self.desktop:
            self.desktop.close()
