import queue

from palmcue.camera import CameraService, _latest


def test_mailbox_keeps_only_latest_frame():
    mailbox = queue.Queue(1)
    _latest(mailbox, 1)
    _latest(mailbox, 2)
    _latest(mailbox, 3)
    assert mailbox.get_nowait() == 3
    assert mailbox.empty()


def test_idle_service_never_opens_camera():
    service = CameraService()
    assert service.poll() == (None, [])
    service.stop()
    service.stop()
