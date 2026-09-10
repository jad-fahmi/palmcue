"""Explicit presentation session; practice has no route to desktop input."""

from palmcue.actions import Dispatcher, OutputBlocked, Target
from palmcue.controller import Event


class Session:
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher
        self.pending: Target | None = None
        self.deadline = 0.0
        self.active = False

    def start(self, target: Target, now: float):
        self.stop()
        self.pending = target
        self.deadline = now + 5

    def stop(self):
        self.pending = None
        self.active = False
        self.dispatcher.disarm()

    def tick(self, now: float, fresh: bool) -> str:
        if self.pending and now >= self.deadline:
            self.dispatcher.target = self.pending
            self.pending = None
            if not fresh or not self.dispatcher.check_target():
                self.stop()
                return (
                    "Could not start. Check your camera and bring the selected slides to the front."
                )
            self.active = True
            return "Presenting · hold an open palm to unlock"
        if self.active and (not fresh or not self.dispatcher.check_target()):
            self.stop()
            return "Presentation paused · return to PalmCue and choose Start presenting again."
        return ""

    def send(self, event: Event):
        if not self.active:
            raise OutputBlocked("Start presenting before sending commands.")
        try:
            self.dispatcher.dispatch(event)
        except (OutputBlocked, OSError):
            self.stop()
            raise
