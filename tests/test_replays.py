import random
from dataclasses import replace

import pytest

from palmcue.controller import Action, Controller
from palmcue.geometry import Observation, Point, Pose


@pytest.mark.parametrize("fps", [15, 24, 30, 60])
def test_hold_sequence_is_independent_of_frame_rate(fps):
    controller = Controller()
    events = []
    for i in range(fps * 8):
        now = i / fps
        pose = Pose.OPEN if now < 2 or 4 < now < 5 else Pose.TWO
        observation = Observation(pose, Point(0.5, 0.5), Point(0.5, 0.4))
        events.extend(controller.update(observation, now))
    assert [event.action for event in events] == [Action.UNLOCK, Action.NEXT, Action.NEXT]


def test_ten_minutes_of_short_noisy_poses_cannot_unlock():
    rng = random.Random(4107)
    controller = Controller()
    poses = list(Pose)
    for frame in range(30 * 60 * 10):
        pose = rng.choice(poses)
        observation = Observation(pose, Point(0.5, 0.5), Point(0.5, 0.4))
        assert controller.update(observation, frame / 30) == []
        assert controller.locked


def test_open_hand_camera_jitter_does_not_become_a_wrist_flick():
    rng = random.Random(9812)
    controller = Controller()
    controller.settings = replace(controller.settings, mode="showcase")
    controller.begin_presentation()
    events = []
    for frame in range(30 * 60):
        observation = Observation(
            Pose.OPEN,
            Point(0.5 + rng.uniform(-0.012, 0.012), 0.5 + rng.uniform(-0.012, 0.012)),
            Point(0.5, 0.4),
        )
        events.extend(controller.update(observation, frame / 30))
    assert events == []
