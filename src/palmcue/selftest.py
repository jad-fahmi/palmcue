"""Packaging diagnostics, intentionally separate from normal desktop startup."""

import json
import time
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory


def run(report_path: Path, camera=False) -> int:
    report = {"ok": False, "checks": []}
    window = None
    try:
        import mediapipe as mp
        import numpy as np
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
        from PySide6.QtWidgets import QApplication

        from palmcue.ui.window import MainWindow
        from palmcue.windows import WindowsBackend

        app = QApplication([])
        model = Path(__file__).parent / "assets/hand_landmarker.task"
        with HandLandmarker.create_from_options(
            HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(model)))
        ) as detector:
            result = detector.detect(
                mp.Image(
                    image_format=mp.ImageFormat.SRGB, data=np.zeros((480, 640, 3), dtype=np.uint8)
                )
            )
            assert not result.hand_landmarks
        report["checks"].append("Bundled model loads and rejects a blank image")
        with TemporaryDirectory(prefix="palmcue-check-") as temp:
            window = MainWindow(Path(temp) / "preferences.json")
            # Native APIs are inspected only. No keyboard/mouse commands are sent.
            backend = WindowsBackend()
            report["window_count"] = len(backend.windows())
            for page in range(5):
                window.navigate(page)
                window.resize(1120, 800)
                app.processEvents()
                assert not window.grab().isNull()
            report["checks"].append("All five desktop pages render")
            if camera:
                window.runtime.start_camera()
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline and not window.runtime.fresh:
                    app.processEvents()
                    if not window.runtime.running:
                        raise RuntimeError(window.notice.text())
                    time.sleep(0.03)
                if not window.runtime.fresh:
                    raise RuntimeError("No fresh frame received from the camera subprocess")
                report["checks"].append("Frozen camera subprocess delivers fresh observations")
            window.close()
            app.processEvents()
        report["ok"] = True
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        if window is not None:
            window.runtime.close()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1
