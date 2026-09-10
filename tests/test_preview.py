from palmcue.geometry import Point
from palmcue.ui.widgets import Preview


def test_debug_preview_draws_landmarks(qtbot):
    preview = Preview()
    qtbot.addWidget(preview)
    preview.resize(400, 300)
    preview.show()
    preview.debug = True
    preview.landmarks = tuple(Point(0.5, 0.5) for _ in range(21))
    assert not preview.grab().isNull()
