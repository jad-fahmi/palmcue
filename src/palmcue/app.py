"""Desktop entry point. Importing the package never starts a camera."""

import multiprocessing
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication

from palmcue.ui.window import MainWindow


def main() -> None:
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setApplicationName("PalmCue")
    app.setOrganizationName("PalmCue")
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
    window = MainWindow(path / "preferences.json")
    try:
        from palmcue.windows import WindowsBackend

        window.runtime.connect_desktop(WindowsBackend())
    except OSError as error:
        window.show_notice(str(error))
    window.show()
    sys.exit(app.exec())
