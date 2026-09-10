# Third-party software

PalmCue is MIT licensed. Its standalone distribution includes separately licensed
components. Full bundled notices are in the adjacent `licenses` folder.

| Component | License | Upstream/source |
| --- | --- | --- |
| CPython | Python Software Foundation license | https://www.python.org/downloads/source/ |
| Qt, PySide6, Shiboken6 | LGPL v3 (with applicable Qt exceptions) | https://download.qt.io/official_releases/QtForPython/ |
| MediaPipe and hand landmark model | Apache 2.0 | https://github.com/google-ai-edge/mediapipe |
| OpenCV | Apache 2.0, bundled third-party notices | https://github.com/opencv/opencv |
| NumPy | BSD-3-Clause, bundled third-party notices | https://github.com/numpy/numpy |
| PyInstaller bootloader | GPL with distribution exception | https://github.com/pyinstaller/pyinstaller |

Qt libraries are dynamically loaded from the `_internal/PySide6` directory. Users
may replace them with compatible modified builds and may reverse engineer the
application for debugging those modifications under the LGPL. PalmCue imposes no
additional restriction on that right. Matching Qt/PySide source releases are
available from the upstream download archive linked above; the exact dependency
versions are recorded in `uv.lock` in PalmCue's source repository. Qt itself:
https://download.qt.io/official_releases/qt/

The original MediaPipe model bundle is included unmodified. Its versioned URL and
SHA-256 are recorded in `scripts/fetch_model.py`. No custom model training is used.

Other dependencies and their bundled licenses are preserved by the build script.
The source of PalmCue, including build scripts, is available at
https://github.com/jad-fahmi/palmcue .
