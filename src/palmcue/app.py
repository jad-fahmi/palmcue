"""Desktop entry point. Importing the package never starts a camera."""

import multiprocessing
import sys
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths
from PySide6.QtWidgets import QApplication, QMessageBox

from palmcue.ui.window import MainWindow


def main() -> None:
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setApplicationName("PalmCue")
    app.setOrganizationName("PalmCue")
    instance_lock = QLockFile(str(Path(tempfile.gettempdir()) / "PalmCue-session.lock"))
    instance_lock.setStaleLockTime(0)
    if not instance_lock.tryLock(100):
        QMessageBox.information(
            None,
            "PalmCue is already open",
            "Look for PalmCue in the taskbar or the system tray beside the clock.",
        )
        return
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
    window = MainWindow(path / "preferences.json")
    try:
        from palmcue.windows import WindowsBackend

        window.runtime.connect_desktop(WindowsBackend())
    except OSError as error:
        window.show_notice(str(error))

    def report_error(kind, value, tb):
        window.runtime.stop_camera()
        window.diagnostics.setText("".join(traceback.format_exception(kind, value, tb)))
        window.show_notice(
            "Something interrupted PalmCue. Controls and camera have stopped. "
            "Try starting the camera again, or restart PalmCue."
        )
        window.showNormal()

    sys.excepthook = report_error
    app.aboutToQuit.connect(window.runtime.close)
    window.show()
    result = app.exec()
    instance_lock.unlock()
    sys.exit(result)
