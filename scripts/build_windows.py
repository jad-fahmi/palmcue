"""Build the offline desktop bundle, license notices, portable ZIP, and optional installer."""

import argparse
import hashlib
import importlib.metadata as metadata
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iscc", type=Path, help="Optional path to the Inno Setup compiler")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise SystemExit("Build on Windows so the bundle contains Windows libraries.")
    model = ROOT / "src/palmcue/assets/hand_landmarker.task"
    expected = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
    if hashlib.sha256(model.read_bytes()).hexdigest() != expected:
        raise SystemExit("Model checksum mismatch. Run scripts/fetch_model.py.")
    from PySide6.QtWidgets import QApplication

    from palmcue.ui.theme import app_icon

    app = QApplication([])
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    icon = build / "palmcue.ico"
    if not app_icon().pixmap(128, 128).save(str(icon), "ICO"):
        raise SystemExit("Could not create the application icon")
    del app
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--onedir",
        "--name",
        "PalmCue",
        "--icon",
        str(icon),
        "--paths",
        str(ROOT / "src"),
        "--specpath",
        str(build),
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(build / "pyinstaller"),
        "--collect-binaries",
        "mediapipe",
        "--collect-data",
        "mediapipe",
        "--collect-data",
        "palmcue",
        "--exclude-module",
        "pytest",
        "--exclude-module",
        "tkinter",
        str(ROOT / "packaging/launcher.py"),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    bundle = ROOT / "dist/PalmCue"
    for name in ("LICENSE", "THIRD_PARTY.md"):
        shutil.copy2(ROOT / name, bundle / name)
    shutil.copy2(ROOT / "docs/QUICK_START.md", bundle / "Quick start.txt")
    notices = bundle / "licenses"
    notices.mkdir(exist_ok=True)
    for file in (ROOT / "packaging/licenses").glob("*.txt"):
        shutil.copy2(file, notices / file.name)
    # Preserve the actual notices shipped by every resolved runtime dependency.
    from packaging.requirements import Requirement

    visited = set()
    pending = ["palmcue"]
    while pending:
        name = pending.pop()
        dist = metadata.distribution(name)
        canonical = dist.metadata["Name"].lower().replace("_", "-")
        if canonical in visited:
            continue
        visited.add(canonical)
        for requirement in dist.requires or []:
            req = Requirement(requirement)
            if req.marker is None or req.marker.evaluate({"extra": ""}):
                pending.append(req.name)
        for file in dist.files or []:
            if any(word in file.name.lower() for word in ("license", "copying", "notice")):
                source = Path(dist.locate_file(file))
                if source.is_file():
                    target = notices / canonical / str(file).replace("../", "")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copy2(python_license, notices / "Python-LICENSE.txt")
    else:
        raise SystemExit("Python license missing from the build environment")
    shutil.make_archive(
        str(ROOT / "dist/PalmCue-0.1.0-windows-x64"), "zip", ROOT / "dist", "PalmCue"
    )
    if args.iscc:
        subprocess.run([str(args.iscc.resolve()), str(ROOT / "packaging/PalmCue.iss")], check=True)
    print("Build ready in dist/", flush=True)


if __name__ == "__main__":
    main()
