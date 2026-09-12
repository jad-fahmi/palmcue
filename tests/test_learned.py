from palmcue.controller import Action, Controller
from palmcue.geometry import Observation, Point, Pose
from palmcue.learned import GestureLibrary, LearnedMatcher, MotionRecorder
from palmcue.settings import Settings


def observation(center_x, tip_x, center_y=0.5, tip_y=0.3):
    return Observation(
        Pose.UNKNOWN,
        Point(center_x, center_y),
        Point(tip_x, tip_y),
        scale=0.1,
    )


def test_recorded_motion_round_trips_and_matches_early(tmp_path):
    recorder = MotionRecorder()
    for now, x in ((0.0, 0.50), (0.1, 0.51), (0.2, 0.55), (0.3, 0.62)):
        recorder.add(now, observation(x, x + 0.05))
    template = recorder.finish()
    assert template is not None
    path = tmp_path / "motions.json"
    library = GestureLibrary(path)
    library.save("next", template)
    loaded = GestureLibrary(path)
    matcher = LearnedMatcher(loaded)
    assert matcher.update(observation(0.50, 0.55), 1.0) is None
    assert matcher.update(observation(0.51, 0.56), 1.1) is None
    assert matcher.update(observation(0.55, 0.60), 1.2) is None
    assert matcher.update(observation(0.58, 0.63), 1.3) == "next"


def test_tiny_recording_and_opposite_motion_are_rejected(tmp_path):
    recorder = MotionRecorder()
    for now, x in ((0.0, 0.50), (0.1, 0.501), (0.2, 0.502), (0.3, 0.503)):
        recorder.add(now, observation(x, x))
    assert recorder.finish() is None

    path = tmp_path / "motions.json"
    path.write_text("{broken", encoding="utf-8")
    assert GestureLibrary(path).templates == {}


def test_controller_fires_taught_action_without_an_unlock_pose(tmp_path):
    library = GestureLibrary(tmp_path / "motions.json")
    recorder = MotionRecorder()
    for now, x in ((0.0, 0.50), (0.1, 0.51), (0.2, 0.55), (0.3, 0.62)):
        recorder.add(now, observation(x, x + 0.05))
    library.save("next", recorder.finish())

    controller = Controller(Settings(mode="learned"), library)
    controller.begin_presentation()
    events = []
    for now, x in ((1.0, 0.50), (1.1, 0.51), (1.2, 0.55), (1.3, 0.58)):
        events.extend(controller.update(observation(x, x + 0.05), now))

    assert [event.action for event in events] == [Action.NEXT]
    assert not controller.locked
