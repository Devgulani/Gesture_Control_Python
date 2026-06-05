# GestureOS

GestureOS is a real-time Python computer vision project for touchless computer control. It uses a webcam to detect one hand, tracks MediaPipe hand landmarks, recognizes a focused MVP set of gestures, and maps those gestures to mouse movement, clicks, scrolling, and safe application exit.

The project is designed as a professional portfolio codebase: small modules, clear responsibilities, type hints, centralized configuration, and documentation that supports future expansion without turning the MVP into a monolith.

## Features

- Real-time one-hand detection from webcam input
- MediaPipe landmark rendering in the OpenCV camera window
- FPS, frame processing time, camera resolution, detection confidence, active gesture, system status, and mouse mode overlays
- Index-finger cursor movement with coordinate mapping and smoothing
- Thumb-index pinch left click with held-pinch protection and cooldown
- Thumb-middle pinch right click with held-pinch protection and cooldown
- Two-finger vertical scroll gesture with rate limiting
- Closed-fist hold exit gesture with safe webcam and OpenCV cleanup
- Keyboard exit with `Q`

## Controls

| Gesture | Action | Mode |
| --- | --- | --- |
| Index finger raised and moved | Move cursor | Mouse |
| Thumb + index pinch | Left click | Mouse |
| Thumb + middle pinch | Right click | Mouse |
| Index + middle fingers extended, index above middle | Scroll up | Mouse |
| Index + middle fingers extended, middle above index | Scroll down | Mouse |
| Closed fist held for 2 seconds | Exit application | Global |
| `Q` key | Exit application | Global |

Mouse mode is the current MVP mode. It enables pointer movement, clicking, and scrolling from one tracked hand. Global controls are always available while the OpenCV window is running.

## Screenshots

Screenshots will be added after running GestureOS on a machine with webcam access.

## Tech Stack

| Dependency | Recommended Version | Purpose |
| --- | --- | --- |
| Python | 3.14.3 | Runtime used by the current project environment |
| OpenCV | `opencv-python>=4.13.0` | Webcam capture, frame display, drawing text overlays |
| MediaPipe | `mediapipe==0.10.35` | Tasks-based hand landmark detection and landmark visualization |
| PyAutoGUI | `pyautogui>=0.9.54` | Mouse movement, clicking, and scrolling |
| NumPy | `numpy>=2.4.0` | Numeric distance calculations and frame-compatible data handling |

No GUI toolkit, web framework, or unnecessary dependency is included. The only user interface is the OpenCV webcam window.

## Compatibility Notes

GestureOS currently targets Python 3.14.3 with MediaPipe 0.10.35. This MediaPipe build does not expose the legacy `mp.solutions` namespace, so the tracker uses the supported MediaPipe Tasks Vision API:

```text
mediapipe.tasks.python.vision.HandLandmarker
```

The Tasks API requires a model asset. Place the official `hand_landmarker.task` file at:

```text
assets/models/hand_landmarker.task
```

If the model file is missing, GestureOS raises a clear startup error before opening the webcam.

## Performance

GestureOS now defaults to `640x480` because MediaPipe inference cost scales with frame size. This is the best default for responsive pointer control and should usually feel faster than `1280x720`.

Supported capture settings are configured in `configs/constants.py`:

| Resolution | Recommended Use | Expected Behavior |
| --- | --- | --- |
| `640x480` | Default performance mode | Lowest latency, best chance of 45-60 FPS |
| `960x540` | Balanced mode | Better image detail with moderate latency |
| `1280x720` | Quality mode | Best visual detail, highest inference cost |

Performance-related settings:

- `CAMERA_WIDTH` and `CAMERA_HEIGHT`: active capture resolution.
- `CAMERA_TARGET_FPS`: requested camera FPS.
- `CAMERA_BUFFER_SIZE`: capture buffer size, kept low to reduce stale frames.
- `CURSOR_SMOOTHING_FACTOR`: higher values follow the hand faster; lower values reduce jitter.
- `CURSOR_DEAD_ZONE_PX`: filters tiny cursor movements.
- `ENABLE_LANDMARK_DRAWING`: turns landmark drawing on or off.
- `LANDMARK_DRAW_INTERVAL_FRAMES`: can draw landmarks less often if rendering becomes a bottleneck.

Expected FPS depends heavily on CPU, webcam driver, lighting, and background load. On typical laptop hardware, `640x480` should be the first setting to try for 45-60 FPS. If tracking is stable and CPU headroom remains, move to `960x540`; use `1280x720` only when visual detail matters more than cursor latency.

Performance tuning guide:

1. Start with `640x480`.
2. Keep the hand well lit and inside the camera frame.
3. Increase `CURSOR_SMOOTHING_FACTOR` if the pointer feels slow.
4. Decrease `CURSOR_SMOOTHING_FACTOR` or increase `CURSOR_DEAD_ZONE_PX` if the pointer jitters.
5. Disable or reduce landmark drawing if rendering becomes expensive.
6. Avoid other apps that are using the same webcam.

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

3. Add the MediaPipe hand landmarker model:

   ```text
   assets/models/hand_landmarker.task
   ```

   Official model URL:

   ```text
   https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
   ```

4. Confirm that your webcam is connected and available to desktop applications.

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
|-- CONTROLS.md
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
    |-- .gitkeep
    `-- models/
        `-- .gitkeep
```

## System Architecture

GestureOS separates camera, gesture, control, and rendering concerns:

- `HandTracker` owns webcam access, MediaPipe initialization, landmark extraction, coordinate conversion, and landmark drawing.
- MediaPipe integration uses the Tasks `HandLandmarker` in `VIDEO` mode instead of the unsupported legacy `mp.solutions.hands.Hands` API.
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

Runtime diagnostics shown in the OpenCV window:

- FPS
- Frame processing time in milliseconds
- Active camera resolution
- Detection confidence when MediaPipe reports handedness confidence
- Active gesture
- Mouse mode
- System status

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

Reserved future gestures:

- Thumbs Up: custom action
- OK Sign: macro trigger
- Peace Sign: presentation mode
- Rock Sign: gaming mode
- Air Circle: open browser
- Air Triangle: open VS Code

## Troubleshooting

- Webcam does not open: close other camera apps, check OS permissions, and verify `CAMERA_INDEX` in `configs/constants.py`.
- Low FPS: use `640x480`, close other webcam consumers, and reduce landmark drawing frequency.
- Cursor feels slow: increase `CURSOR_SMOOTHING_FACTOR` in small steps such as `0.05`.
- Cursor jumps too quickly: lower `CURSOR_SMOOTHING_FACTOR` or increase `CURSOR_DEAD_ZONE_PX`.
- Clicks trigger too easily: reduce `PINCH_DISTANCE_THRESHOLD` or increase click cooldowns.
- Scroll direction feels inverted: switch the sign handling in `MouseController._scroll()`.
- PyAutoGUI failsafe triggers: avoid moving the cursor to the top-left screen corner, or adjust PyAutoGUI behavior in `MouseController` after reviewing safety implications.
- MediaPipe install issues: use Python 3.14.3 with `mediapipe==0.10.35` for this project state and upgrade `pip` before installing dependencies.
- `module 'mediapipe' has no attribute 'solutions'`: install/use MediaPipe 0.10.35 with the current Tasks-based tracker; do not use legacy `mp.solutions` code in this environment.
- Missing model file: download `hand_landmarker.task` and place it in `assets/models/`.

## License

No license has been selected yet. Add a license before publishing or accepting external contributions.
