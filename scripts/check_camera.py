"""Read-only hardware smoke check. No images or input events are saved/sent."""

import multiprocessing
import time

from palmcue.camera import CameraService


def main():
    service = CameraService()
    try:
        service.start()
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            frame, messages = service.poll()
            for kind, value in messages:
                print(kind, value, flush=True)
                if kind == "error":
                    return
            if frame:
                print(
                    f"Frame received: {frame.width}x{frame.height}; "
                    f"latency {time.monotonic() - frame.captured:.3f}s",
                    flush=True,
                )
                return
            time.sleep(0.1)
        print("Camera timed out; no frame received", flush=True)
    finally:
        service.stop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
