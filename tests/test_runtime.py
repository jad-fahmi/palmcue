import time

from palmcue.actions import Dispatcher, Target
from palmcue.camera import Frame
from palmcue.session import Session
from palmcue.ui.window import MainWindow


class FakeCamera:
    def __init__(self):
        self.started = False
        self.frame = None
        self.messages = []

    def start(self, *args):
        self.started = True

    def stop(self):
        self.started = False

    def poll(self):
        result = self.frame, self.messages
        self.frame, self.messages = None, []
        return result


class AutoBackend:
    def __init__(self):
        self.target = Target(123, 42, "Canva presentation")
        self.active = self.target.handle

    def fullscreen_presentation(self):
        return self.target

    def foreground(self):
        return self.active

    def process(self, handle):
        return 42

    def modifiers_down(self):
        return False

    def key(self, code, control=False):
        pass


def test_automatic_mode_starts_guarded_countdown(qtbot, tmp_path):
    window = MainWindow(tmp_path / "prefs.json", FakeCamera())
    qtbot.addWidget(window)
    runtime = window.runtime
    backend = AutoBackend()
    runtime.backend = backend
    runtime.session = Session(Dispatcher(backend))
    runtime.fresh = True
    runtime.last_frame = time.monotonic()
    runtime.auto_start_if_needed()
    assert runtime.session.pending
    assert runtime.controller.locked
    assert "Fullscreen presentation detected" in window.session_status.text()


def test_stale_frames_and_errors_lock_controls(qtbot, tmp_path):
    camera = FakeCamera()
    window = MainWindow(tmp_path / "prefs.json", camera)
    qtbot.addWidget(window)
    runtime = window.runtime
    runtime.start_camera()
    runtime.controller.locked = False
    camera.frame = Frame(time.monotonic() - 1, None, 0, b"\x00" * 12, 2, 2, 0)
    runtime.poll()
    assert runtime.controller.locked
    assert not runtime.fresh
    camera.messages = [("error", "Camera disconnected")]
    runtime.poll()
    assert not runtime.running
    assert not camera.started
    assert window.notice.text() == "Camera disconnected"
    assert window.camera_button.text() == "Retry camera"


def test_preferences_restart_camera_only_when_needed(qtbot, tmp_path):
    camera = FakeCamera()
    window = MainWindow(tmp_path / "prefs.json", camera)
    qtbot.addWidget(window)
    window.runtime.start_camera()
    window.runtime.controller.locked = False
    window.update_setting(area="wide")
    assert window.runtime.controller.locked
    assert camera.started
    window.close()
    assert not camera.started
