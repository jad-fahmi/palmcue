from palmcue.controller import Action, Event
from palmcue.ui.window import MainWindow


def test_practice_is_local_and_preferences_persist(qtbot, tmp_path):
    window = MainWindow(tmp_path / "preferences.json")
    qtbot.addWidget(window)
    window.show()
    window.deck.apply(Event(Action.NEXT))
    assert window.deck.slide == 1
    window.mode.setCurrentIndex(1)
    assert window.settings.mode == "showcase"
    assert not window.hold.isEnabled()
    assert window.zoom_check.isEnabled()
    window.dismiss_welcome()
    assert not window.welcome.isVisible()
    other = MainWindow(tmp_path / "preferences.json")
    qtbot.addWidget(other)
    assert other.settings.mode == "showcase"
    assert other.settings.onboarding_done


def test_every_page_renders(qtbot, tmp_path):
    window = MainWindow(tmp_path / "preferences.json")
    qtbot.addWidget(window)
    window.show()
    for i in range(5):
        window.navigate(i)
        assert not window.grab().isNull()
