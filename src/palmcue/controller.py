"""Time-based gesture state machine; all timestamps are monotonic seconds."""

import math
from dataclasses import dataclass
from enum import StrEnum

from palmcue.geometry import Observation, Point, Pose
from palmcue.learned import GestureLibrary, LearnedMatcher
from palmcue.motion import Motion, WristFlick
from palmcue.settings import Settings


class Action(StrEnum):
    NEXT = "Next slide"
    PREVIOUS = "Previous slide"
    POINTER = "Pointer"
    CLICK = "Click"
    ZOOM_IN = "Zoom in"
    ZOOM_OUT = "Zoom out"
    LOCK = "Controls locked"
    UNLOCK = "Controls ready"


@dataclass(frozen=True)
class Event:
    action: Action
    position: Point | None = None


AREAS = {
    "center": (0.20, 0.15, 0.80, 0.90),
    "left": (0.05, 0.15, 0.48, 0.90),
    "right": (0.52, 0.15, 0.95, 0.90),
    "wide": (0.08, 0.10, 0.92, 0.92),
}


class Controller:
    def __init__(self, settings: Settings | None = None, learned: GestureLibrary | None = None):
        self.settings = settings or Settings()
        self.locked = True
        self.progress = 0.0
        self.hint = "Hold an open palm to unlock"
        self._last_time: float | None = None
        self._last_seen: float | None = None
        self._pose = Pose.UNKNOWN
        self._since = 0.0
        self._origin: Observation | None = None
        self._latched = False
        self._release_since: float | None = None
        self._cooldown = 0.0
        self._pointer: Point | None = None
        self._point_time = -math.inf
        self._motion = Motion()
        self._flick = WristFlick()
        self._learned = LearnedMatcher(learned) if learned else None
        self.presentation_mode = False

    def begin_presentation(self) -> None:
        """Presentation sessions are ready immediately and stay ready through ambiguity."""
        self.lock()
        self.presentation_mode = True
        self.locked = False
        self.hint = "Ready · show two fingers for next slide"

    def end_presentation(self) -> None:
        self.presentation_mode = False
        self.lock()

    def lock(self) -> None:
        self.locked = True
        self._reset_candidate()
        self._latched = False
        self._pointer = None
        self._point_time = -math.inf
        self.hint = "Hold an open palm to unlock"

    def _reset_candidate(self) -> None:
        self._pose = Pose.UNKNOWN
        self._origin = None
        self._release_since = None
        self.progress = 0.0
        self._motion.reset()
        self._flick.reset()
        if self._learned:
            self._learned.reset()

    def _release_latch(self, now: float) -> None:
        if not self._latched:
            return
        if self._release_since is None:
            self._release_since = now
        elif now - self._release_since >= 0.2:
            self._latched = False

    def update(self, obs: Observation | None, now: float, hands: int = 1) -> list[Event]:
        if not math.isfinite(now) or (self._last_time is not None and now <= self._last_time):
            self.lock()
            return []
        gap = self._last_time is not None and now - self._last_time > 0.35
        self._last_time = now
        if gap:
            if self.presentation_mode:
                self._reset_candidate()
            else:
                self.lock()
        if hands > 1:
            if not self.presentation_mode:
                self.lock()
            self.hint = "Use just one hand"
            return []
        if obs is None or hands != 1:
            release_since = self._release_since
            self._reset_candidate()
            self._release_since = release_since
            self._release_latch(now)
            self._pointer = None
            self._point_time = -math.inf
            if not self.presentation_mode and (
                self._last_seen is None or now - self._last_seen > 0.7
            ):
                self.lock()
            self.hint = "Relax or lower your hand, then show the next gesture"
            return []
        self._last_seen = now
        if self.presentation_mode and self.locked:
            self.locked = False
            self.hint = "Ready · show two fingers for next slide"
        left, top, right, bottom = AREAS[self.settings.area]
        inside = left <= obs.center.x <= right and top <= obs.center.y <= bottom
        # Fist is always allowed to lock, even outside the activation area.
        if not inside and obs.pose != Pose.FIST:
            self._reset_candidate()
            self._point_time = -math.inf
            self._pointer = None
            self.hint = "Move your hand inside the marked area"
            return []
        if (
            self.settings.mode == "learned"
            and self._learned
            and not self._latched
            and now >= self._cooldown
        ):
            result = self._learned.update(obs, now)
            self.hint = "Make one of your taught motions"
            if result:
                return self._fire(Action.NEXT if result == "next" else Action.PREVIOUS, now)
            return []
        if obs.pose != self._pose or self._origin is None:
            self._motion.reset()
            self._pose = obs.pose
            self._since = now
            self._origin = obs
            self.progress = 0.0
        held = now - self._since
        motion = math.hypot(
            obs.center.x - self._origin.center.x, obs.center.y - self._origin.center.y
        )
        if obs.pose == Pose.FIST:
            if self.presentation_mode:
                self._release_latch(now)
                self.hint = "Relax your hand, then show the next gesture"
                self.progress = 0
                return []
            self.hint = "Hold your fist to pause"
            self.progress = min(1.0, held / 0.3)
            if held >= 0.3 and not self.locked:
                self.presentation_mode = False
                self.lock()
                return [Event(Action.LOCK)]
            return []
        if self.locked:
            self.hint = "Hold an open palm still to unlock"
            if obs.pose == Pose.OPEN:
                if motion > 0.045:
                    self._since, self._origin = now, obs
                    held = 0
                self.progress = min(1.0, held / 1.3)
                if held >= 1.3:
                    self.locked = False
                    self._latched = False
                    self._cooldown = now + 0.5
                    self.hint = "Ready for your first command"
                    return [Event(Action.UNLOCK)]
            return []
        if obs.pose == Pose.UNKNOWN or (
            not self.presentation_mode and self._latched and obs.pose == Pose.OPEN
        ):
            self._release_latch(now)
            self.hint = "Ready for your next gesture"
            self.progress = 0
            return []
        self._release_since = None
        if self._latched:
            self.hint = "Relax or lower your hand before the next command"
            return []
        if now < self._cooldown:
            return []
        if self.settings.mode == "showcase" and obs.pose in (Pose.OPEN, Pose.TWO):
            self.hint = "Flick your wrist left or right"
            result = self._flick.update(obs, now)
            if result:
                return self._fire(Action.NEXT if result == "next" else Action.PREVIOUS, now)
            return []
        if obs.pose == Pose.POINT and self.settings.pointer:
            self.hint = "Point with your index finger"
            if held < 0.2:
                return []
            x = min(1.0, max(0.0, (obs.pointer.x - left) / (right - left)))
            y = min(1.0, max(0.0, (obs.pointer.y - top) / (bottom - top)))
            previous = self._pointer or Point(x, y)
            self._pointer = Point(
                previous.x + 0.28 * (x - previous.x), previous.y + 0.28 * (y - previous.y)
            )
            self._point_time = now
            return [Event(Action.POINTER, self._pointer)]
        if obs.pose == Pose.PINCH and self.settings.click and self.settings.pointer:
            self.hint = "Hold the pinch to click"
            if held >= 0.25 and now - self._point_time < 0.8:
                return self._fire(Action.CLICK, now)
            return []
        if self.settings.mode == "reliable" and obs.pose in (Pose.TWO, Pose.THREE):
            self.hint = "Hold still for " + (
                "next slide" if obs.pose == Pose.TWO else "previous slide"
            )
            if motion > 0.045:
                self._since, self._origin = now, obs
                held = 0
            self.progress = min(1.0, held / self.settings.hold_seconds)
            if held >= self.settings.hold_seconds:
                return self._fire(Action.NEXT if obs.pose == Pose.TWO else Action.PREVIOUS, now)
        if self.settings.mode == "showcase":
            self.hint = "Hold two fingers briefly, then swipe left or right"
            result = self._motion.update(obs, now, self.settings.zoom)
            if result in ("next", "previous"):
                return self._fire(Action.NEXT if result == "next" else Action.PREVIOUS, now)
            if result in ("zoom_in", "zoom_out"):
                self.hint = "Zoom in" if result == "zoom_in" else "Zoom out"
                return [Event(Action.ZOOM_IN if result == "zoom_in" else Action.ZOOM_OUT)]
        return []

    def _fire(self, action: Action, now: float) -> list[Event]:
        self._latched = True
        self._cooldown = now + 0.65
        self.progress = 1.0
        self.hint = action.value
        return [Event(action)]
