"""Developer/build utility. The desktop app never invokes this script."""

import hashlib
from pathlib import Path
from urllib.request import urlopen

URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
       "hand_landmarker/float16/1/hand_landmarker.task")
DEST = Path(__file__).resolve().parents[1] / "src/palmcue/assets/hand_landmarker.task"
SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"


def main():
    with urlopen(URL, timeout=120) as response:
        data = response.read(16_000_000)
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError("The model checksum did not match the pinned version")
    DEST.write_bytes(data)
    print(f"Model: {len(data)} bytes; SHA256 {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
