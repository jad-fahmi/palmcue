"""Render the desktop and presentation feedback without a camera or desktop input."""

from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication

from palmcue.ui.hud import PresentationHUD
from palmcue.ui.window import MainWindow


def main():
    app = QApplication([])
    output = Path("build/ui-preview")
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="palmcue-preview-") as temp:
        window = MainWindow(Path(temp) / "preferences.json")
        window.runtime.timer.stop()
        window.show()
        for index in range(5):
            window.navigate(index)
            app.processEvents()
            window.grab().save(str(output / f"page-{index}.png"))
        hud = PresentationHUD()
        hud.display("PalmCue · Locked", "Hold an open palm to unlock", 0.65)
        app.processEvents()
        hud.grab().save(str(output / "presentation-feedback.png"))
        hud.close()
        window.close()


if __name__ == "__main__":
    main()
