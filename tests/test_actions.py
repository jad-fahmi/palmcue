import pytest

from palmcue.actions import Dispatcher, OutputBlocked, Target
from palmcue.controller import Action, Event


class RecordingBackend:
    active = 123
    pid = 42
    modifiers = False

    def __init__(self):
        self.sent = []

    def foreground(self):
        return self.active

    def process(self, handle):
        return self.pid

    def modifiers_down(self):
        return self.modifiers

    def key(self, code, control=False):
        self.sent.append((code, control))


def test_no_input_without_selected_foreground_target():
    backend = RecordingBackend()
    d = Dispatcher(backend)
    with pytest.raises(OutputBlocked):
        d.dispatch(Event(Action.NEXT))
    d.target = Target(123, 42, "Slides")
    d.dispatch(Event(Action.NEXT))
    assert backend.sent == [(0x27, False)]
    backend.active = 456
    with pytest.raises(OutputBlocked):
        d.dispatch(Event(Action.PREVIOUS))
    assert d.target is None
    assert len(backend.sent) == 1


def test_reused_window_handle_and_modifiers_are_rejected():
    for pid, modifiers in [(43, False), (42, True)]:
        backend = RecordingBackend()
        backend.pid, backend.modifiers = pid, modifiers
        d = Dispatcher(backend)
        d.target = Target(123, 42, "Slides")
        with pytest.raises(OutputBlocked):
            d.dispatch(Event(Action.NEXT))
        assert not backend.sent
