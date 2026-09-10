import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from palmcue.controller import AREAS, Action, Event
from palmcue.geometry import Point


def label(text, kind="", wrap=True):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if kind:
        widget.setObjectName(kind)
    return widget


def card():
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    return frame, layout


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 230)
        self.image = QImage()
        self.area = "center"
        self.message = "Your camera is off"
        self.detail = "Start when you're ready. Nothing is recorded."
        self.setAccessibleName("Camera preview and gesture activation area")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#193b3d"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 12, 12)
        if not self.image.isNull():
            size = self.image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            rect = QRectF(
                (self.width() - size.width()) / 2,
                (self.height() - size.height()) / 2,
                size.width(),
                size.height(),
            )
            p.drawImage(rect, self.image)
            left, top, right, bottom = AREAS[self.area]
            box = QRectF(
                rect.left() + left * rect.width(),
                rect.top() + top * rect.height(),
                (right - left) * rect.width(),
                (bottom - top) * rect.height(),
            )
            p.setPen(QPen(QColor("#c7ec98"), 2, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(box, 12, 12)
        else:
            p.setPen(QColor("#eff5e8"))
            p.setFont(QFont("Segoe UI", 17, QFont.Weight.DemiBold))
            p.drawText(
                self.rect().adjusted(20, 0, -20, -15), Qt.AlignmentFlag.AlignCenter, self.message
            )
            p.setFont(QFont("Segoe UI", 10))
            p.setPen(QColor("#b6d0c4"))
            p.drawText(
                self.rect().adjusted(20, 55, -20, 0),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self.detail,
            )
        p.end()


class PracticeDeck(QWidget):
    SLIDES = [
        ("Make room\nfor your ideas.", "01 / A confident beginning"),
        ("A little movement.\nA clear message.", "02 / Keep the story moving"),
        ("Stay in\nthe moment.", "03 / Connect with your audience"),
        ("You've got this.", "04 / Take it to your presentation"),
    ]

    def __init__(self):
        super().__init__()
        self.setMinimumSize(280, 210)
        self.slide = 0
        self.zoom = 1.0
        self.pointer: Point | None = None
        self.clicked = False
        self.setAccessibleName("Practice slides. Gestures here never control other apps.")

    def apply(self, event: Event):
        if event.action == Action.NEXT:
            self.slide = (self.slide + 1) % len(self.SLIDES)
        elif event.action == Action.PREVIOUS:
            self.slide = (self.slide - 1) % len(self.SLIDES)
        elif event.action == Action.POINTER:
            self.pointer = event.position
        elif event.action == Action.ZOOM_IN:
            self.zoom = min(1.4, self.zoom + 0.1)
        elif event.action == Action.ZOOM_OUT:
            self.zoom = max(0.7, self.zoom - 0.1)
        elif event.action == Action.CLICK:
            self.clicked = True
            QTimer.singleShot(350, self.clear_click)
        self.update()

    def clear_click(self):
        self.clicked = False
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#e5ecd9"))
        p.drawRoundedRect(self.rect(), 12, 12)
        p.setBrush(QColor("#d2e0bd"))
        p.drawEllipse(QPointF(self.width() * 0.93, self.height() * 0.18), 78, 78)
        p.setPen(QColor("#426b52"))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(22, 32, "PALMCUE / PRACTICE")
        p.setPen(QColor("#244c3a"))
        p.setFont(QFont("Segoe UI", round(22 * self.zoom), QFont.Weight.DemiBold))
        p.drawText(
            self.rect().adjusted(22, 50, -20, -40),
            Qt.AlignmentFlag.AlignVCenter,
            self.SLIDES[self.slide][0],
        )
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(22, self.height() - 20, self.SLIDES[self.slide][1])
        if self.pointer:
            p.setBrush(QColor("#e6734c" if self.clicked else "#21654f"))
            p.setPen(QPen(QColor("white"), 2))
            p.drawEllipse(
                QPointF(self.pointer.x * self.width(), self.pointer.y * self.height()),
                12 if self.clicked else 7,
                12 if self.clicked else 7,
            )
        p.end()


class GesturePreview(QWidget):
    """Simple animated hand silhouettes; no camera/model needed to learn controls."""

    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.phase = 0.0
        self.setFixedSize(108, 108)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

    def animate(self):
        if self.isVisible():
            self.phase += 0.05
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(54, 56)
        if self.kind == "swipe":
            p.translate(math.sin(self.phase * 2) * 13, 0)
        if self.kind == "zoom":
            p.scale(1 + math.sin(self.phase * 2) * 0.12, 1 + math.sin(self.phase * 2) * 0.12)
        p.setBrush(QColor("#d9e9cd"))
        p.setPen(QPen(QColor("#3d7454"), 2))
        p.drawRoundedRect(QRectF(-22, -2, 44, 37), 13, 13)
        count = {
            "open": 4,
            "two": 2,
            "three": 3,
            "point": 1,
            "fist": 0,
            "pinch": 1,
            "swipe": 2,
            "zoom": 4,
        }[self.kind]
        for i in range(4):
            height = (35, 43, 38, 29)[i] if i < count else 9
            p.drawRoundedRect(QRectF(-22 + i * 11, -height, 10, height + 12), 5, 5)
        if count == 4:
            p.drawRoundedRect(QRectF(-36, 0, 13, 28), 6, 6)
        elif self.kind == "pinch":
            p.drawEllipse(QRectF(-28, -25, 22, 20))
        else:
            p.drawRoundedRect(QRectF(-24, 12, 28, 11), 5, 5)
        p.end()
