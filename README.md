# PalmCue

PalmCue is a webcam-based presentation controller that lets you navigate slides, zoom, point, and interact with presentations using hand gestures.

It is built in Python and designed to work with existing presentation software rather than replacing it.

## Features

* Hand tracking using a standard webcam
* Slide navigation with hand gestures
* Virtual presentation pointer
* Gesture-based zoom
* Lock/unlock controls to prevent accidental input
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
| Closed fist                 | Lock controls         |

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

PalmCue is currently under development.

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/palmcue.git
cd palmcue
```

Set up the Python environment and install the project dependencies once the initial release is available.

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

## Status

PalmCue is currently in active development.

Planned initial functionality:

* [ ] Webcam input
* [ ] Hand landmark tracking
* [ ] Gesture recognition
* [ ] Slide navigation
* [ ] Control lock
* [ ] Pointer control
* [ ] Five-finger zoom
* [ ] Showcase gesture mode
* [ ] Calibration
* [ ] Configuration
* [ ] Minimal desktop interface

## Demo

Demo media will be added once the first presentation-ready version is complete.

## Contributing

The project is still early in development. Contribution guidelines will be added once the core implementation stabilizes.

## License

PalmCue is licensed under the [MIT License](LICENSE).
