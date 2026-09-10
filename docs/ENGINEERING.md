# Engineering notes

Windows 10/11 x64 is the first supported delivery target. Python and Qt are bundled
with the desktop application. Users never install a runtime or download a model.

The pipeline is deliberately separated:

1. Camera + MediaPipe produce observations, on a worker thread.
2. Pure landmark geometry identifies a pose, without OS or UI dependencies.
3. A deterministic temporal controller applies holds, release gates, motion
   thresholds, activation bounds and lock state.
4. An action adapter sends short keyboard/mouse events to the selected window.
5. Qt owns settings, onboarding, practice, feedback and lifecycle.

Safety defaults: start locked, one clearly visible hand, deliberate unlock,
one event per held gesture, tracking loss relocks, practice never sends input.
No recording, network service, telemetry or custom trained classifier.

Implementation sequence: runnable foundation; settings; pose geometry; temporal
controls; Showcase motion; Windows actions; camera/tracking; desktop practice;
presentation integration; packaging; final verification and documentation.
Each step is reviewed and tested before committing. Hardware and actual slide
application acceptance checks are recorded separately from automated tests.
