import pytest
from test_actions import RecordingBackend

from palmcue.actions import Dispatcher, OutputBlocked, Target
from palmcue.controller import Action, Event
from palmcue.session import Session


def test_countdown_cannot_send_input_and_focus_loss_disarms():
    backend = RecordingBackend()
    session = Session(Dispatcher(backend))
    session.start(Target(123, 42, "Slides"), 0)
    assert session.tick(4, True) == ""
    with pytest.raises(OutputBlocked):
        session.send(Event(Action.NEXT))
    assert not backend.sent
    assert session.tick(5, True)
    assert session.active
    session.send(Event(Action.NEXT))
    backend.active = 789
    assert session.tick(5.1, True)
    assert not session.active
    assert session.dispatcher.target is None
    assert len(backend.sent) == 1


def test_tracking_loss_and_cancel_require_new_session():
    session = Session(Dispatcher(RecordingBackend()))
    session.start(Target(123, 42, "Slides"), 0)
    session.tick(5, False)
    assert not session.active
    session.start(Target(123, 42, "Slides"), 6)
    session.stop()
    session.tick(12, True)
    assert not session.active
