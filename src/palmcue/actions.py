"""Presentation input policy, independently testable with a recording backend."""

from dataclasses import dataclass
from typing import Protocol

from palmcue.controller import Action, Event


@dataclass(frozen=True)
class Target:
    handle: int
    process: int
    title: str


class Backend(Protocol):
    def foreground(self) -> int: ...
    def process(self, handle: int) -> int: ...
    def modifiers_down(self) -> bool: ...
    def key(self, code: int, control: bool = False) -> None: ...
    def move(self, handle: int, x: float, y: float) -> None: ...
    def click(self, handle: int) -> None: ...


class OutputBlocked(RuntimeError):
    pass


class Dispatcher:
    def __init__(self, backend: Backend):
        self.backend = backend
        self.target: Target | None = None

    def disarm(self) -> None:
        self.target = None

    def check_target(self) -> bool:
        t = self.target
        return bool(t and self.backend.foreground() == t.handle
                    and self.backend.process(t.handle) == t.process)

    def dispatch(self, event: Event) -> None:
        if event.action in (Action.LOCK, Action.UNLOCK):
            return
        if not self.check_target():
            self.disarm()
            raise OutputBlocked("Presentation paused. Switch back and start presenting again.")
        if self.backend.modifiers_down():
            raise OutputBlocked("Release the keyboard keys, then start presenting again.")
        t = self.target
        assert t is not None
        if event.action == Action.NEXT:
            self.backend.key(0x27)
        elif event.action == Action.PREVIOUS:
            self.backend.key(0x25)
        elif event.action == Action.POINTER and event.position:
            self.backend.move(t.handle, event.position.x, event.position.y)
        elif event.action == Action.CLICK:
            self.backend.click(t.handle)
        elif event.action in (Action.ZOOM_IN, Action.ZOOM_OUT):
            self.backend.key(0xBB if event.action == Action.ZOOM_IN else 0xBD, control=True)
