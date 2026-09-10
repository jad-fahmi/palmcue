"""Presentation feedback that never takes focus or intercepts slide clicks."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QVBoxLayout, QWidget


class PresentationHUD(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(360)
        self.setStyleSheet(
            "QWidget { background: #153d3c; color: #f4faf4; font-family: 'Segoe UI'; }"
            "QLabel { background: transparent; }"
            "QLabel#title { font-size: 18px; font-weight: 600; }"
            "QLabel#detail { font-size: 13px; color: #cee0d9; }"
            "QLabel#footer { font-size: 11px; color: #a7c6ba; }"
            "QProgressBar { background: #355651; border: none; max-height: 5px; }"
            "QProgressBar::chunk { background: #c3dd93; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        self.title = QLabel("PalmCue · Locked")
        self.title.setObjectName("title")
        self.detail = QLabel("Hold an open palm to unlock")
        self.detail.setObjectName("detail")
        self.detail.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.footer = QLabel("Fist to lock · Ctrl + Alt + Space to stop")
        self.footer.setObjectName("footer")
        for widget in (self.title, self.detail, self.progress, self.footer):
            layout.addWidget(widget)
        self.expiry = QTimer(self)
        self.expiry.setSingleShot(True)
        self.expiry.timeout.connect(self.hide)
        self.confirmation = QTimer(self)
        self.confirmation.setSingleShot(True)

    def place(self, point=None):
        screen = QApplication.screenAt(point) if point is not None else None
        screen = screen or QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            self.adjustSize()
            self.move(area.right() - self.width() - 20, area.top() + 20)

    def display(self, title, detail, progress=0, temporary=False):
        self.expiry.stop()
        self.title.setText(title)
        self.detail.setText(detail)
        self.progress.setValue(round(max(0, min(1, progress)) * 100))
        self.adjustSize()
        self.show()
        if temporary:
            self.expiry.start(5000)

    def feedback(self, locked, hint, progress):
        if locked:
            self.confirmation.stop()
        if not self.confirmation.isActive():
            self.display("PalmCue · Locked" if locked else "PalmCue · Ready", hint, progress)

    def acknowledge(self, action):
        self.display(action, "Command sent · relax your hand before the next cue", 1)
        self.confirmation.start(1200)

    def reset(self):
        self.confirmation.stop()
        self.expiry.stop()
        self.hide()
