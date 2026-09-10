"""Desktop entry point. Importing the package never starts a camera."""

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("PalmCue")
    app.setOrganizationName("PalmCue")
    window = QMainWindow()
    window.setWindowTitle("PalmCue")
    window.resize(960, 700)
    window.setCentralWidget(QLabel("PalmCue\nYour presentation. At your fingertips."))
    window.show()
    sys.exit(app.exec())
