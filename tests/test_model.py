import hashlib
from pathlib import Path

import palmcue


def test_bundled_model_integrity():
    path = Path(palmcue.__file__).parent / "assets" / "hand_landmarker.task"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
    )
