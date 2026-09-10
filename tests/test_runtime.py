import time

from palmcue.camera import Frame
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
