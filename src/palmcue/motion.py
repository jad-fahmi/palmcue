"""Optional motion recognizers; each starts with a stationary preparation period."""

import math

from palmcue.geometry import Observation, Pose


class WristFlick:
    """Low-latency horizontal intent from a briefly prepared open hand."""

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.anchor: Observation | None = None
        self.since = 0.0
        self.armed = False

    def update(self, obs: Observation, now: float) -> str | None:
        if obs.pose != Pose.OPEN:
            self.reset()
            return None
        if self.anchor is None:
            self.anchor, self.since = obs, now
            return None
        dx = obs.center.x - self.anchor.center.x
        dy = obs.center.y - self.anchor.center.y
        elapsed = now - self.since
        if not self.armed:
            if math.hypot(dx, dy) > 0.025:
                self.anchor, self.since = obs, now
            elif elapsed >= 0.08:
                self.anchor, self.since, self.armed = obs, now, True
            return None
        if elapsed > 0.55 or abs(dy) > 0.065:
            self.reset()
            return None
        speed = abs(dx) / max(elapsed, 1e-6)
        # Scale travel to the visible hand, bounded for near and distant cameras.
        travel = max(0.075, min(0.12, obs.scale * 0.65))
        if abs(dx) >= travel and abs(dx) > 2.4 * abs(dy) and speed >= 0.30:
            self.reset()
            return "next" if dx > 0 else "previous"
        return None


class Motion:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.anchor: Observation | None = None
        self.since = 0.0
        self.armed = False

    def update(self, obs: Observation, now: float, zoom: bool) -> str | None:
        if obs.pose not in (Pose.TWO, Pose.OPEN):
            self.reset()
            return None
        if self.anchor is None or self.anchor.pose != obs.pose:
            self.anchor, self.since, self.armed = obs, now, False
            return None
        dx, dy = obs.center.x - self.anchor.center.x, obs.center.y - self.anchor.center.y
        if not self.armed:
            if math.hypot(dx, dy) > 0.035:
                self.anchor, self.since = obs, now
            elif now - self.since >= 0.25:
                self.anchor, self.since, self.armed = obs, now, True
            return None
        if obs.pose == Pose.TWO:
            if abs(dy) > 0.07 or now - self.since > 1.0:
                self.reset()
            elif abs(dx) >= 0.16 and abs(dx) > 2.5 * abs(dy):
                self.reset()
                return "next" if dx > 0 else "previous"
        elif zoom:
            # Reject whole-hand translation, depth changes and sudden scale jumps.
            ratio = obs.scale / max(self.anchor.scale, 1e-6)
            if math.hypot(dx, dy) > 0.06 or not 0.85 < ratio < 1.15:
                self.reset()
            elif now - self.since >= 0.35:
                change = obs.spread / max(self.anchor.spread, 1e-6)
                if change > 1.22 or change < 0.78:
                    self.anchor, self.since = obs, now
                    return "zoom_in" if change > 1 else "zoom_out"
        return None
