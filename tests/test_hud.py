from PySide6.QtCore import Qt

from palmcue.ui.hud import PresentationHUD


def test_feedback_never_intercepts_presentation_input(qtbot):
    hud = PresentationHUD()
    qtbot.addWidget(hud)
    assert hud.windowFlags() & Qt.WindowType.WindowTransparentForInput
    assert hud.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
    assert hud.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    hud.display("Starting in 3…", "Keep your slides in front", 0.4)
    assert hud.isVisible()
    assert hud.progress.value() == 40
    hud.acknowledge("Next slide")
    hud.feedback(False, "Ready", 0)
    assert hud.title.text() == "Next slide"
    hud.reset()
    hud.feedback(True, "Hold an open palm", 0.5)
    assert hud.title.text() == "PalmCue · Locked"
    assert hud.progress.value() == 50
