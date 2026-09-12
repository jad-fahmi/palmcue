# PalmCue

PalmCue is a webcam-based presentation controller that lets you navigate slides, zoom, point, and interact with presentations using hand gestures.

It is built in Python and designed to work with existing presentation software rather than replacing it.

## Features

* Hand tracking using a standard webcam
* Slide navigation with hand gestures
* Optional low-latency wrist flicks in Expressive mode
* Personal gestures taught with a guided countdown
* Virtual presentation pointer
* Gesture-based zoom
* Conservative recognition that ignores ambiguous hand shapes
* Configurable gesture activation area
* Reliable and Showcase gesture modes
* Designed to work without keeping a webcam preview on screen

## Showcase Gestures

PalmCue includes an optional Showcase mode for more expressive presentation controls.

| Gesture                     | Action                |
| --------------------------- | --------------------- |
| Two-finger swipe left/right | Previous / next slide |
| Five-finger expansion       | Zoom in               |
| Five-finger contraction     | Zoom out              |
| Index finger                | Pointer               |
| Pinch                       | Click                 |
| Closed fist                 | No presentation action |

Showcase mode can be disabled in favor of more conservative gestures when reliability is the priority.

## Supported Presentations

PalmCue is intended to work with applications such as:

* Microsoft PowerPoint
* Google Slides
* Canva Presentations
* PDF viewers
* Browser-based presentation tools

Compatibility depends on the keyboard and mouse controls supported by the target application.

## Requirements

* Python 3
* Webcam

Core dependencies will include:

* MediaPipe
* OpenCV
* NumPy

Additional dependencies may be added as development progresses.

## Installation

The Windows release includes an installer and a portable ZIP in `dist/`. Users do
not need Python, a terminal, or a separate model download. The installer is per
user and does not require administrator access. For source development, use the
locked environment described in `docs/ENGINEERING.md`.

From source, clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/palmcue.git
cd palmcue
```

Then run `uv sync` and launch `uv run palmcue`. This is only for development;
normal users should launch PalmCue from the Start menu or the extracted portable
folder.

## Usage

Start PalmCue, select your webcam and gesture profile, then launch your presentation normally.

PalmCue runs alongside the presentation and translates recognized hand gestures into presentation controls.

For presentations, the controller can remain hidden or minimized so the audience only sees the slide deck.

## Gesture Modes

### Reliable

Uses simpler gestures designed for consistent recognition.

### Showcase

Uses more expressive gestures such as two-finger slide navigation and five-finger continuous zoom.

Showcase mode is optional.

### Personal

If the built-in gestures do not suit the way you move, choose **Personal** in
Preferences. Select **Teach Next** or **Teach Previous**, wait for the three-second
countdown, and make one natural motion. PalmCue stores the motion on your computer
and recognizes its direction and scale while you present.

Lowering your hand or moving it out of view resets the current motion. It does not
lock presentation controls, and there is no open-palm unlock pose before your next
command.

## Status

The first presentation-ready Windows build is implemented. It includes webcam
tracking, conservative gesture recognition, guided practice, configuration,
pointer, guarded presentation input, optional Showcase gestures,
recovery messaging, offline packaging, and a signed-model checksum. Hardware and
individual presentation-app acceptance still need to be checked on the machine
where it will be used; rehearse with the actual deck first.

## Demo

Demo media will be added once the first presentation-ready version is complete.

## Contributing

The project is still early in development. Contribution guidelines will be added once the core implementation stabilizes.

## License

PalmCue is licensed under the [MIT License](LICENSE).
