"""GUI-thread coordinator: lifecycle, fresh observations, and practice feedback."""

import time

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QImage

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
        self.desktop = None
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.poll)
        self.timer.start()
        window.camera_button.clicked.connect(self.toggle_camera)
        window.lock_button.clicked.connect(self.lock)
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
        self.window.present_button.clicked.connect(self.start_presenting)
        self.window.stop_button.clicked.connect(self.stop_presenting)
        self.window.targets.currentIndexChanged.connect(self.update_present_controls)
        self.refresh_targets()
        if not self.desktop.shortcut.registered:
            self.window.show_notice(
                "Ctrl + Alt + Space is already used by another app. "
                "Use the tray menu to stop presenting, or your fist to lock."
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
        busy = bool(self.session and (self.session.active or self.session.pending))
        self.window.present_button.setEnabled(
            self.fresh and not busy and self.window.targets.currentData() is not None
        )
        self.window.stop_button.setEnabled(busy)
        self.window.targets.setEnabled(not busy)
        self.window.refresh_targets.setEnabled(not busy)
        if not self.session or not self.fresh:
            self.window.session_step.setText("Step 1 · Start camera in Practice")
        elif self.session.pending:
            self.window.session_step.setText("Step 3 · Bring your slideshow to the front")
        elif self.session.active and self.controller.locked:
            self.window.session_step.setText("Presenting · hold an open palm to unlock")
        elif self.session.active:
            self.window.session_step.setText("Presenting · hold two fingers for next slide")
        elif self.window.targets.currentData() is None:
            self.window.session_step.setText("Step 2 · Select your slideshow window")
        else:
            self.window.session_step.setText("Step 3 · Start presenting")

    def start_presenting(self):
        target = self.window.targets.currentData()
        if not self.session or not self.fresh or target is None:
            return
        self.lock()
        self.session.start(target, time.monotonic())
        self.window.session_status.setText("Switch to your slides · starting in 5 seconds")
        self.window.session_step.setText("Step 3 · Bring your slideshow to the front")
        self.update_present_controls()
        self.window.showMinimized()

    def stop_presenting(self):
        if self.session:
            self.session.stop()
            self.lock()
            self.window.session_status.setText("Stopped · your slides are untouched")
            self.update_present_controls()
        if self.desktop:
            self.desktop.overlay.hide()
            self.desktop.tray.setToolTip("PalmCue · presentation stopped")
            self.desktop.status("stopped")

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

    def reconfigure(self, changes):
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
            message = self.session.tick(now, self.fresh and now - self.last_frame < 0.7)
            if message:
                self.lock()
                self.window.session_status.setText(message)
            if self.session.pending:
                seconds = max(1, int(self.session.deadline - now) + 1)
                self.window.session_status.setText(
                    f"Switch to your slides · starting in {seconds}s"
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
        self.window.camera_button.setText("Stop camera")
        self.window.camera_badge.setText("CAMERA ON")
        if self.session and not self.session.active and not self.session.pending:
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

    def handle_event(self, event):
        if self.session and self.session.active:
            try:
                self.session.send(event)
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
