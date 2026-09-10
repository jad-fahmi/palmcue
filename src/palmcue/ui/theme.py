from pathlib import Path

from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap

STYLE = """
QWidget { color: #203537; font-family: 'Segoe UI'; font-size: 14px; }
QMainWindow, QScrollArea, QStackedWidget, QWidget#page { background: #f5f6f2; }
QWidget#sidebar { background: #153d3c; }
QLabel#brand { color: #f4faf4; font-size: 28px; font-weight: 700; }
QLabel#tagline { color: #b7d4ca; font-size: 12px; }
QPushButton#nav { background: transparent; color: #cee0d9; text-align: left;
                 border: none; border-radius: 9px; padding: 13px 16px; }
QPushButton#nav:checked { background: #2b5652; color: white; font-weight: 600; }
QPushButton#nav:hover { background: #244d49; }
QLabel#eyebrow { color: #48786b; font-size: 11px; font-weight: 700; }
QLabel#heading { font-size: 30px; font-weight: 650; color: #173f3b; }
QLabel#subheading { font-size: 18px; font-weight: 600; }
QLabel#muted { color: #607570; }
QFrame#card { background: white; border: 1px solid #dfe7e0; border-radius: 14px; }
QFrame#banner { background: #e4eee3; border: 1px solid #cfdfcf; border-radius: 14px; }
QLabel#notice { background: #fff2d9; color: #70501c; border-radius: 8px; padding: 12px; }
QLabel#badge { background: #e4eee3; color: #255447; border-radius: 12px;
              padding: 6px 12px; font-weight: 600; font-size: 12px; }
QPushButton { background: white; border: 1px solid #c5d4cb; border-radius: 8px;
              padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #edf4ec; border-color: #618e7c; }
QPushButton:pressed { background: #d7e7d8; }
QPushButton:focus { border: 2px solid #508d77; }
QPushButton#primary { background: #21654f; color: white; border-color: #21654f; }
QPushButton#primary:hover { background: #184e3d; }
QPushButton#danger { color: #91413a; border-color: #d7aaa3; }
QPushButton:disabled { background: #e8ece7; color: #8a9791; border-color: #dce3dc; }
QComboBox { background: white; border: 1px solid #c5d4cb; border-radius: 7px;
            padding: 9px 12px; min-height: 20px; }
QComboBox QAbstractItemView { background: white; selection-background-color: #dbeadb; }
QCheckBox { spacing: 10px; padding: 7px 0; }
QCheckBox::indicator { width: 20px; height: 20px; border: 1px solid #96b09e;
                       border-radius: 5px; background: white; }
QCheckBox::indicator:checked { background: #21654f; border: 4px solid #b5d3bd; }
QSlider::groove:horizontal { height: 6px; background: #dce6dc; border-radius: 3px; }
QSlider::handle:horizontal { background: #21654f; width: 18px; margin: -6px 0;
                            border-radius: 9px; }
QProgressBar { border: none; background: #e4ebe3; height: 7px; border-radius: 3px; }
QProgressBar::chunk { background: #508b63; border-radius: 3px; }
QToolTip { background: #173f3b; color: white; padding: 8px; border: none; }
QScrollBar:vertical { background: transparent; width: 9px; }
QScrollBar::handle:vertical { background: #c0d0c3; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def app_icon(color=None) -> QIcon:
    asset = Path(__file__).resolve().parents[1] / "assets/app-icon.svg"
    if asset.is_file():
        icon = QIcon(str(asset))
        if color is None:
            return icon
        pix = icon.pixmap(128, 128)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#ffffff"), 5))
        painter.setBrush(QColor(color))
        painter.drawEllipse(88, 88, 32, 32)
        painter.end()
        return QIcon(pix)
    color = color or "#21654f"
    pix = QPixmap(128, 128)
    pix.fill(QColor("transparent"))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(QPen(QColor(color)))
    p.drawRoundedRect(3, 3, 122, 122, 28, 28)
    p.setPen(QColor("#e7f0d3"))
    p.setFont(QFont("Segoe UI", 65, QFont.Weight.DemiBold))
    p.drawText(33, 94, "P")
    p.setBrush(QColor("#c3dd93"))
    p.setPen(QColor("#c3dd93"))
    p.drawEllipse(87, 80, 15, 15)
    p.end()
    return QIcon(pix)
