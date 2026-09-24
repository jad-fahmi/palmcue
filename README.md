# PalmCue

PalmCue uses a webcam to control presentations with hand gestures. It runs
alongside presentation software and sends keyboard and mouse input only during
an active presentation session.

## Gestures

| Gesture | Action |
| --- | --- |
| Two fingers held briefly | Next slide |
| Thumb, index, and middle finger | Previous slide |
| Index finger | Move the pointer |
| Pinch after pointing | Click (off by default) |
| Open palm or two fingers, then a wrist flick | Navigate in Expressive mode |
| Two fingers held, then a horizontal swipe | Navigate in Expressive mode |
| Open palm spread or contracted | Zoom in Expressive mode (off by default) |
| Taught motion | Next or previous slide in Personal mode |

Practice controls a local sample deck. Presentation controls require an active
session, start after a five-second countdown, and pause when the selected window
loses focus. Camera frames are processed locally and are not saved.

## Windows release

The installer and portable ZIP include Python, Qt, and the hand tracking model.
See [Quick start](docs/QUICK_START.md) for setup and presentation guidance.

## Development

PalmCue supports Python 3.11–3.13. With [uv](https://docs.astral.sh/uv/) installed:

```powershell
uv sync
uv run palmcue
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The Windows distribution is built with `uv run python scripts/build_windows.py`.
See [Engineering notes](docs/ENGINEERING.md) for the application boundaries and
release assumptions.

## License

PalmCue is licensed under the [MIT License](LICENSE). Bundled software notices
are listed in [THIRD_PARTY.md](THIRD_PARTY.md).
