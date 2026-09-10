"""Conservative, scale-independent hand geometry. No UI or tracking imports."""

import math
from dataclasses import dataclass
from enum import StrEnum


class Pose(StrEnum):
    UNKNOWN = "Relax your hand"
    OPEN = "Open palm"
    FIST = "Closed fist"
    POINT = "Index finger"
    TWO = "Two fingers"
    THREE = "Three fingers"
    PINCH = "Pinch"


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class Observation:
    pose: Pose
    center: Point
    pointer: Point
    spread: float = 0.0
    scale: float = 0.1


def distance(a: Point, b: Point) -> float:
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)


def angle(a: Point, b: Point, c: Point) -> float:
    ab = (a.x - b.x, a.y - b.y, a.z - b.z)
    cb = (c.x - b.x, c.y - b.y, c.z - b.z)
    length = distance(a, b) * distance(c, b)
    if length < 1e-9:
        return 0
    return math.degrees(math.acos(max(-1, min(1, sum(x*y for x, y in zip(ab, cb)) / length))))


def classify(points: list[Point], aspect: float = 4 / 3) -> Observation | None:
    """Input uses normalized image coordinates; x and z are width-relative.

    Ambiguous joints stay UNKNOWN instead of being rounded to the nearest pose.
    Handedness scores are deliberately not used as detection confidence.
    """
    if len(points) != 21 or not all(
        math.isfinite(v) for p in points for v in (p.x, p.y, p.z)
    ):
        return None
    if any(not (0.015 < p.x < 0.985 and 0.015 < p.y < 0.985) for p in points):
        return None
    p = [Point(v.x * aspect, v.y, v.z * aspect) for v in points]
    scale = distance(p[0], p[9])
    if not 0.065 < scale < 0.65 or distance(p[5], p[17]) < scale * 0.35:
        return None
    extended, folded = [], []
    for base in (5, 9, 13, 17):
        joint = angle(p[base], p[base + 1], p[base + 3])
        reach = distance(p[base + 3], p[0]) / max(distance(p[base + 1], p[0]), 1e-6)
        extended.append(joint > 155 and reach > 1.15)
        folded.append(joint < 125 and reach < 1.1)
    thumb_open = (angle(p[2], p[3], p[4]) > 145
                  and distance(p[4], p[5]) / scale > 0.65)
    pinch = distance(p[4], p[8]) / scale < 0.25
    pose = Pose.UNKNOWN
    # Pinch is intentionally limited to folded other fingers to avoid open-palm clicks.
    if pinch and all(folded[1:]):
        pose = Pose.PINCH
    elif all(folded) and not thumb_open:
        pose = Pose.FIST
    elif all(extended) and thumb_open:
        pose = Pose.OPEN
    elif extended[0] and all(folded[1:]) and not thumb_open:
        pose = Pose.POINT
    elif all(extended[:2]) and all(folded[2:]) and not thumb_open:
        pose = Pose.TWO
    elif all(extended[:3]) and folded[3] and not thumb_open:
        pose = Pose.THREE
    center = Point(sum(points[i].x for i in (0, 5, 9, 13, 17)) / 5,
                   sum(points[i].y for i in (0, 5, 9, 13, 17)) / 5)
    spread = sum(distance(p[a], p[b]) for a, b in ((4, 8), (8, 12), (12, 16), (16, 20)))
    return Observation(pose, center, points[8], spread / scale, scale)
