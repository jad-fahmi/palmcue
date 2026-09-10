import hashlib
from pathlib import Path

import palmcue


def test_bundled_model_integrity():
    path = Path(palmcue.__file__).parent / "assets" / "hand_landmarker.task"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
    )


def test_real_model_loads_and_rejects_blank_frame():
    import mediapipe as mp
    import numpy as np
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions

    path = Path(palmcue.__file__).parent / "assets" / "hand_landmarker.task"
    with HandLandmarker.create_from_options(
        HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(path)))
    ) as detector:
        result = detector.detect(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=np.zeros((480, 640, 3), dtype=np.uint8))
        )
    assert not result.hand_landmarks
