from dataclasses import replace

from palmcue.controller import Action
from palmcue.geometry import Pose
from palmcue.motion import Motion
from test_controller import feed, obs, ready


def test_swipe_requires_preparation_and_release():
    c = ready()
    c.settings = replace(c.settings, mode="showcase")
    feed(c, Pose.TWO, 2, 0.35)
    assert c.update(obs(Pose.TWO, x=0.68), 2.4)[0].action == Action.NEXT
    assert feed(c, Pose.TWO, 2.45, 1, x=0.4) == []


def test_reject_unprepared_and_diagonal_motion():
    for x, y in [(0.7, 0.5), (0.7, 0.7)]:
        m = Motion()
        m.update(obs(Pose.TWO), 0, False)
        assert m.update(obs(Pose.TWO, x=x, y=y), 0.1, False) is None
    m = Motion()
    for t in (0, 0.1, 0.3):
        m.update(obs(Pose.TWO), t, False)
    assert m.update(obs(Pose.TWO, x=0.7, y=0.65), 0.5, False) is None


def test_zoom_is_optional_normalized_and_rate_limited():
    m = Motion()
    for t in (0, 0.1, 0.3):
        m.update(obs(Pose.OPEN), t, True)
    assert m.update(obs(Pose.OPEN, spread=2.6), 0.7, False) is None
    assert m.update(obs(Pose.OPEN, spread=2.6), 0.75, True) == "zoom_in"
    assert m.update(obs(Pose.OPEN, spread=3.4), 0.8, True) is None
    assert m.update(obs(Pose.OPEN, spread=1.8), 1.2, True) == "zoom_out"


def test_click_requires_recent_pointer_and_release():
    c = ready()
    c.settings = replace(c.settings, click=True)
    assert feed(c, Pose.PINCH, 2, 0.4) == []
    assert Action.POINTER in feed(c, Pose.POINT, 2.45, 0.3)
    assert feed(c, Pose.PINCH, 2.8, 1) == [Action.CLICK]
