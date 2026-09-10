from palmcue.controller import Action, Event
from palmcue.ui.widgets import GesturePreview, PracticeDeck, Preview


def test_practice_widgets_render_without_camera(qtbot):
    for widget in (Preview(), PracticeDeck(), GesturePreview("open")):
        qtbot.addWidget(widget)
        widget.show()
        assert not widget.grab().isNull()


def test_practice_deck_wraps_locally(qtbot):
    deck = PracticeDeck()
    qtbot.addWidget(deck)
    deck.apply(Event(Action.PREVIOUS))
    assert deck.slide == 3
    deck.apply(Event(Action.NEXT))
    assert deck.slide == 0
