"""Tray, emergency shortcut, and a small non-interactive presentation pointer."""

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from palmcue.ui.hud import PresentationHUD
from palmcue.ui.theme import app_icon


class StopShortcut(QAbstractNativeEventFilter):
    ID = 0x5043

    def __init__(self, backend, callback):
        super().__init__()
        self.api, self.callback = backend.api, callback
        self.api.RegisterHotKey.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            wintypes.UINT,
            wintypes.UINT,
        ]
        self.api.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self.registered = bool(self.api.RegisterHotKey(None, self.ID, 0x4003, 0x20))
        if self.registered:
            QApplication.instance().installNativeEventFilter(self)

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x0312 and msg.wParam == self.ID:
            self.callback()
            return True, 0
        return False, 0

    def close(self):
        if self.registered:
            QApplication.instance().removeNativeEventFilter(self)
            self.api.UnregisterHotKey(None, self.ID)
            self.registered = False


class PointerOverlay(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(36, 36)
        self.expiry = QTimer(self)
        self.expiry.setSingleShot(True)
        self.expiry.timeout.connect(self.hide)

    def reveal(self):
        position = QCursor.pos()
        self.move(position.x() - 18, position.y() - 18)
        self.show()
        self.expiry.start(350)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("white"), 2))
        painter.setBrush(QColor(235, 109, 66, 200))
        painter.drawEllipse(QPointF(18, 18), 9, 9)
        painter.end()


class Desktop:
    def __init__(self, window, backend, stop):
        self.window = window
        self.overlay = PointerOverlay()
        self.hud = PresentationHUD()
        self.shortcut = StopShortcut(backend, stop)
        self.tray = QSystemTrayIcon(app_icon(), window)
        self._state = ""
        self.tray.setToolTip("PalmCue · waiting for a presentation")
        menu = QMenu(window)
        menu.addAction("Open PalmCue", self.open)
        menu.addAction("Stop presenting", stop)
        menu.addAction("Stop camera", window.runtime.stop_camera)
        menu.addSeparator()
        menu.addAction("Quit PalmCue", window.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.open()

    def open(self):
        self.window.runtime.stop_presenting()
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    def status(self, state):
        if state != self._state:
            self._state = state
            color = {"ready": "#21654f", "locked": "#98702c", "stopped": "#607570"}[state]
            self.tray.setIcon(app_icon(color))

    def close(self):
        self.shortcut.close()
        self.overlay.close()
        self.hud.close()
        self.tray.hide()
