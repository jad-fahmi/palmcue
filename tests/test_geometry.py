import math

import pytest

from palmcue.geometry import Point, Pose, angle, classify


def hand(extended=(), thumb=False):
    p = [Point(0.5, 0.8) for _ in range(21)]
    p[1:5] = [Point(0.43, 0.72), Point(0.39, 0.65), Point(0.43, 0.61), Point(0.47, 0.64)]
    if thumb:
        p[1:5] = [Point(0.43, 0.72), Point(0.36, 0.65), Point(0.30, 0.59), Point(0.24, 0.53)]
    for n, base in enumerate((5, 9, 13, 17)):
        x = 0.40 + n * 0.065
        p[base] = Point(x, 0.60)
        p[base + 1] = Point(x, 0.48)
        p[base + 2] = Point(x, 0.39 if n in extended else 0.55)
        p[base + 3] = Point(x, 0.30 if n in extended else 0.65)
    return p


@pytest.mark.parametrize(
    "fingers,thumb,pose",
    [
        ((), False, Pose.FIST),
        ((0,), False, Pose.POINT),
        ((0, 1), False, Pose.TWO),
        ((0, 1), True, Pose.THREE),
        ((0, 1, 2), False, Pose.UNKNOWN),
        ((0, 1, 2, 3), True, Pose.OPEN),
        ((1, 3), False, Pose.UNKNOWN),
    ],
)
def test_poses_and_mirrors(fingers, thumb, pose):
    points = hand(fingers, thumb)
    assert classify(points).pose == pose
    assert classify([Point(1 - p.x, p.y, p.z) for p in points]).pose == pose
    # In-plane rotation must not change the pose.
    rotated = [Point(0.5 + (p.y - 0.5) / (4 / 3), 0.5 - (p.x - 0.5) * (4 / 3)) for p in points]
    assert classify(rotated).pose == pose


def test_invalid_and_clipped_hands():
    assert classify([]) is None
    p = hand()
    p[8] = Point(math.nan, 0.4)
    assert classify(p) is None
    p[8] = Point(0, 0.4)
    assert classify(p) is None
    assert classify([Point(0.5, 0.5)] * 21) is None
    assert angle(Point(0, 0), Point(0, 0), Point(1, 1)) == 0


def test_closed_fist_with_thumb_touching_index_is_not_a_click():
    points = hand()
    points[4] = points[8]
    assert classify(points).pose == Pose.FIST


def test_deliberate_pinch_above_knuckles():
    points = hand((0,))
    points[4] = Point(points[8].x + 0.015, points[8].y)
    assert classify(points).pose == Pose.PINCH
