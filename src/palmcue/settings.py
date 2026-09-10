"""Validated preferences; session state and window handles are never persisted."""

import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass(frozen=True)
class Settings:
    mode: str = "reliable"
    hold_seconds: float = 0.85
    area: str = "center"
    pointer: bool = True
    click: bool = False
    zoom: bool = False
    mirror: bool = True
    camera: int = -1
    onboarding_done: bool = False
    debug_preview: bool = False

    @classmethod
    def from_dict(cls, data: object) -> "Settings":
        if not isinstance(data, dict):
            raise ValueError("Preferences must be an object")
        defaults = asdict(cls())
        result = {}
        for key, default in defaults.items():
            value = data.get(key, default)
            if type(default) is float:
                valid = type(value) in (int, float) and math.isfinite(value)
            else:
                valid = type(value) is type(default)
            result[key] = value if valid else default
        if result["mode"] not in ("reliable", "showcase"):
            result["mode"] = "reliable"
        if result["area"] not in ("center", "left", "right", "wide"):
            result["area"] = "center"
        result["hold_seconds"] = min(1.5, max(0.6, result["hold_seconds"]))
        result["camera"] = min(15, max(-1, result["camera"]))
        return cls(**result)


def load_settings(path: Path) -> tuple[Settings, str]:
    try:
        return Settings.from_dict(json.loads(path.read_text(encoding="utf-8"))), ""
    except FileNotFoundError:
        return Settings(), ""
    except (OSError, ValueError):
        return Settings(), "Your preferences could not be read. Safe defaults are in use."


def save_settings(path: Path, settings: Settings) -> None:
    """Atomic replacement leaves the previous file intact if a write fails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
        ) as stream:
            temp = Path(stream.name)
            json.dump(asdict(settings), stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
