"""Local, deterministic motion teaching and matching."""

import json
import math
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from palmcue.geometry import Observation


@dataclass(frozen=True)
class MotionTemplate:
    center_x: float
    center_y: float
    tip_x: float
    tip_y: float
    duration: float

    @property
    def vector(self):
        return (self.center_x, self.center_y, self.tip_x, self.tip_y)


class GestureLibrary:
    def __init__(self, path: Path):
        self.path = path
        self.templates: dict[str, MotionTemplate] = {}
        self.load()

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for action in ("next", "previous"):
                values = data.get(action)
                if isinstance(values, dict):
                    self.templates[action] = MotionTemplate(**values)
        except (OSError, ValueError, TypeError):
            self.templates = {}

    def save(self, action: str, template: MotionTemplate):
        self.templates[action] = template
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({name: asdict(value) for name, value in self.templates.items()}, indent=2),
            encoding="utf-8",
        )


class MotionRecorder:
    def __init__(self):
        self.samples: list[tuple[float, Observation]] = []

    def add(self, now: float, observation: Observation | None):
        if observation is not None:
            self.samples.append((now, observation))

    def finish(self) -> MotionTemplate | None:
        if len(self.samples) < 4:
            return None
        start_time, start = self.samples[0]

        def travel(sample):
            _, observation = sample
            return math.hypot(
                observation.center.x - start.center.x,
                observation.center.y - start.center.y,
            ) + math.hypot(
                observation.pointer.x - start.pointer.x,
                observation.pointer.y - start.pointer.y,
            )

        end_time, end = max(self.samples[1:], key=travel)
        scale = max(0.06, (start.scale + end.scale) / 2)
        template = MotionTemplate(
            (end.center.x - start.center.x) / scale,
            (end.center.y - start.center.y) / scale,
            (end.pointer.x - start.pointer.x) / scale,
            (end.pointer.y - start.pointer.y) / scale,
            max(0.1, end_time - start_time),
        )
        if math.sqrt(sum(value * value for value in template.vector)) < 0.45:
            return None
        return template


class LearnedMatcher:
    def __init__(self, library: GestureLibrary):
        self.library = library
        self.samples = deque(maxlen=30)

    def reset(self):
        self.samples.clear()

    def update(self, observation: Observation | None, now: float) -> str | None:
        if observation is None:
            self.reset()
            return None
        self.samples.append((now, observation))
        while self.samples and now - self.samples[0][0] > 1.2:
            self.samples.popleft()
        if len(self.samples) < 4:
            return None
        for started, start in self.samples:
            elapsed = now - started
            if elapsed < 0.08:
                continue
            scale = max(0.06, (start.scale + observation.scale) / 2)
            vector = (
                (observation.center.x - start.center.x) / scale,
                (observation.center.y - start.center.y) / scale,
                (observation.pointer.x - start.pointer.x) / scale,
                (observation.pointer.y - start.pointer.y) / scale,
            )
            winner, score = None, 0.0
            magnitude = math.sqrt(sum(value * value for value in vector))
            for action, template in self.library.templates.items():
                target = template.vector
                target_magnitude = math.sqrt(sum(value * value for value in target))
                similarity = sum(a * b for a, b in zip(vector, target, strict=True)) / max(
                    1e-6, magnitude * target_magnitude
                )
                if magnitude >= target_magnitude * 0.55 and similarity > score:
                    winner, score = action, similarity
            if winner and score >= 0.88:
                self.reset()
                return winner
        return None
