# GestureOS

GestureOS is a real-time Python computer vision project for touchless computer control. It uses a webcam to detect one hand, tracks MediaPipe hand landmarks, recognizes a focused MVP set of gestures, and maps those gestures to mouse movement, clicks, scrolling, and safe application exit.

The project is designed as a professional portfolio codebase: small modules, clear responsibilities, type hints, centralized configuration, and documentation that supports future expansion without turning the MVP into a monolith.

## Features

- Real-time one-hand detection from webcam input
- MediaPipe landmark rendering in the OpenCV camera window
- FPS, active gesture, system status, and mouse mode overlays
- Index-finger cursor movement with coordinate mapping and smoothing
- Thumb-index pinch left click with held-pinch protection and cooldown
- Thumb-middle pinch right click with held-pinch protection and cooldown
- Two-finger vertical scroll gesture with rate limiting
- Closed-fist hold exit gesture with safe webcam and OpenCV cleanup
- Keyboard exit with `Q`

## Screenshots

Screenshots will be added after running GestureOS on a machine with webcam access.

## Tech Stack

| Dependency | Recommended Version | Purpose |
| --- | --- | --- |
| Python | 3.11+ | Runtime language for the application |
| OpenCV | `opencv-python>=4.9.0` | Webcam capture, frame display, drawing text overlays |
| MediaPipe | `mediapipe>=0.10.14` | Hand landmark detection and landmark visualization |
| PyAutoGUI | `pyautogui>=0.9.54` | Mouse movement, clicking, and scrolling |
| NumPy | `numpy>=1.26.0` | Numeric distance calculations and frame-compatible data handling |

No GUI toolkit, web framework, or unnecessary dependency is included. The only user interface is the OpenCV webcam window.

## Installation

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Confirm that your webcam is connected and available to desktop applications.

## How To Run

```powershell
python main.py
```

Controls:

- Move cursor: raise one hand and move the index fingertip.
- Left click: pinch thumb and index finger.
- Right click: pinch thumb and middle finger.
- Scroll: extend index and middle fingers, offset vertically to choose direction.
- Exit: hold a closed fist for 2 seconds or press `Q`.

## Project Structure

```text
GestureOS/
|-- main.py
|-- requirements.txt
|-- README.md
|-- DEVELOPMENT_LOG.md
|-- trackers/
|   |-- __init__.py
|   `-- hand_tracker.py
|-- controllers/
|   |-- __init__.py
|   `-- mouse_controller.py
|-- gestures/
|   |-- __init__.py
|   `-- gesture_detector.py
|-- utils/
|   |-- __init__.py
|   `-- helpers.py
|-- configs/
|   |-- __init__.py
|   `-- constants.py
`-- assets/
    `-- .gitkeep
```

## System Architecture

GestureOS separates camera, gesture, control, and rendering concerns:

- `HandTracker` owns webcam access, MediaPipe initialization, landmark extraction, coordinate conversion, and landmark drawing.
- `GestureDetector` owns gesture recognition, normalized finger-distance calculations, gesture classification, and exit-hold state.
- `MouseController` owns cursor mapping, smoothing, PyAutoGUI actions, click cooldowns, scroll cooldowns, and held-pinch protection.
- `GestureOSApplication` in `main.py` owns the main loop, module coordination, overlay rendering, lifecycle, and shutdown.
- `configs/constants.py` owns configurable thresholds, camera settings, UI colors, cooldown values, and smoothing parameters.
- `utils/helpers.py` owns shared data objects and small reusable helpers.

The modules are deliberately narrow so future controllers, analytics, profiles, and gesture engines can be added without rewriting the MVP loop.

## Data Flow

```text
Webcam frame
  -> HandTracker.read_frame()
  -> HandTracker.process_frame()
  -> normalized landmark map
  -> GestureDetector.detect()
  -> GestureResult
  -> MouseController.handle_gesture()
  -> PyAutoGUI mouse action
  -> GestureOSApplication overlay rendering
  -> OpenCV window
```

## Future Roadmap

These features are documented for future phases and are not implemented in the MVP:

- Volume Control
- Brightness Control
- Screenshot Gesture
- Media Controls
- Presentation Mode
- Gaming Mode
- Air Drawing Recognition
- Custom Gesture Training
- Gesture Macros
- Gesture Analytics
- Multi-Hand Support
- User Profiles
- AI-Based Gesture Recognition

## Troubleshooting

- Webcam does not open: close other camera apps, check OS permissions, and verify `CAMERA_INDEX` in `configs/constants.py`.
- Cursor jumps too quickly: lower `CURSOR_SMOOTHING_FACTOR` or increase `CURSOR_DEAD_ZONE_PX`.
- Clicks trigger too easily: reduce `PINCH_DISTANCE_THRESHOLD` or increase click cooldowns.
- Scroll direction feels inverted: switch the sign handling in `MouseController._scroll()`.
- PyAutoGUI failsafe triggers: avoid moving the cursor to the top-left screen corner, or adjust PyAutoGUI behavior in `MouseController` after reviewing safety implications.
- MediaPipe install issues: use Python 3.11 and upgrade `pip` before installing dependencies.

## License

No license has been selected yet. Add a license before publishing or accepting external contributions.
