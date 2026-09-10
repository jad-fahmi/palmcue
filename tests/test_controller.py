from palmcue.controller import Action, Controller
from palmcue.geometry import Observation, Point, Pose


def obs(pose, x=0.5, y=0.5, spread=2.0):
    return Observation(pose, Point(x, y), Point(x, y), spread)


def feed(c, pose, start, duration, **kwargs):
    events = []
    for i in range(round(duration / 0.05) + 1):
        events += c.update(obs(pose, **kwargs), round(start + i * 0.05, 5))
    return [e.action for e in events]


def ready():
    c = Controller()
    assert feed(c, Pose.OPEN, 0, 1.4) == [Action.UNLOCK]
    feed(c, Pose.UNKNOWN, 1.45, 0.5)
    return c


def test_start_locked_and_deliberate_unlock():
    c = Controller()
    assert feed(c, Pose.TWO, 0, 2) == []
    assert c.locked
    assert feed(c, Pose.OPEN, 2.05, 0.5) == []
    feed(c, Pose.UNKNOWN, 2.6, 0.1)
    assert feed(c, Pose.OPEN, 2.75, 1.4) == [Action.UNLOCK]


def test_one_command_until_neutral_release():
    c = ready()
    assert feed(c, Pose.TWO, 2, 3) == [Action.NEXT]
    assert feed(c, Pose.THREE, 5.05, 1.2) == []
    feed(c, Pose.UNKNOWN, 6.3, 0.3)
    assert feed(c, Pose.THREE, 6.65, 1.0) == [Action.PREVIOUS]


def test_no_accumulated_dwell_across_missing_frames():
    c = ready()
    assert feed(c, Pose.TWO, 2, 0.6) == []
    c.update(None, 2.65, 0)
    assert feed(c, Pose.TWO, 2.7, 0.6) == []


def test_loss_stall_and_multiple_hands_lock():
    for timestamp, observation, hands in [
        (3, None, 0),
        (3, obs(Pose.TWO), 1),
        (2, obs(Pose.TWO), 2),
    ]:
        c = ready()
        assert c.update(observation, timestamp, hands) == []
        assert c.locked


def test_outside_area_cannot_unlock_but_can_lock():
    c = Controller()
    assert feed(c, Pose.OPEN, 0, 2, x=0.1) == []
    assert c.locked
    c = ready()
    assert feed(c, Pose.FIST, 2, 0.4, x=0.1) == [Action.LOCK]


def test_brief_and_moving_poses_do_not_fire():
    c = ready()
    assert feed(c, Pose.TWO, 2, 0.4) == []
    assert feed(c, Pose.THREE, 2.45, 0.4) == []
    assert feed(c, Pose.TWO, 2.9, 0.5) == []
    assert feed(c, Pose.TWO, 3.45, 0.5, x=0.6) == []


def test_time_reversal_fails_closed():
    c = ready()
    assert c.update(obs(Pose.TWO), 0) == []
    assert c.locked


def test_open_palm_is_an_obvious_release_gesture():
    c = ready()
    assert feed(c, Pose.TWO, 2, 1) == [Action.NEXT]
    feed(c, Pose.OPEN, 3.05, 0.7)
    assert feed(c, Pose.TWO, 3.8, 1) == [Action.NEXT]
