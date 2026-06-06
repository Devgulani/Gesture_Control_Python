# GestureOS

GestureOS is a real-time Python computer vision project for touchless computer control. It uses a webcam to detect one hand, tracks MediaPipe hand landmarks, recognizes gestures, and maps those gestures to mouse movement, clicks, scrolling, volume control, media playback, and screenshot capture.

The project is designed as a professional portfolio codebase: small modules, clear responsibilities, type hints, centralized configuration, and documentation that supports future expansion without turning the MVP into a monolith.

## Features

- Real-time one-hand detection from webcam input
- MediaPipe landmark rendering in the OpenCV camera window
- FPS, frame processing time, camera resolution, detection confidence, active gesture, system status, and mouse mode overlays
- Index-finger cursor movement with coordinate mapping and smoothing
- Thumb-index pinch left click with held-pinch protection and cooldown
- Thumb-middle pinch right click with held-pinch protection and cooldown
- Two-finger vertical scroll gesture with rate limiting
- **Volume control** via thumb-index distance
- **Media playback control** (play/pause, next, previous)
- **Screenshot capture** via three-finger pinch
- **Mode system**: Mouse, Volume, and Media modes
- Closed-fist hold exit gesture with safe webcam and OpenCV cleanup
- Keyboard exit with `Q`

## Controls

Full control documentation is in `CONTROLS.md`.

### Mouse Mode (Default)

| Gesture | Action |
| --- | --- |
| Index finger raised and moved | Move cursor |
| Thumb + index pinch | Left click |
| Thumb + middle pinch | Right click |
| Index + middle fingers extended, offset vertically | Scroll |
| Open hand held 2s | Switch to Volume Mode |
| Peace sign held 2s | Switch to Media Mode |

### Volume Mode

| Gesture | Action |
| --- | --- |
| Adjust thumb-index distance | Set system volume |
| Open hand held 2s | Return to Mouse Mode |

### Media Mode

| Gesture | Action |
| --- | --- |
| Open palm | Play / Pause |
| Swipe right | Next Track |
| Swipe left | Previous Track |
| Peace sign held 2s | Return to Mouse Mode |

### Global Controls

| Gesture | Action |
| --- | --- |
| Closed fist held for 2 seconds | Exit application |
| Three-finger pinch held briefly | Take screenshot |
| `Q` key | Exit application |

## Tech Stack

| Dependency | Recommended Version | Purpose |
| --- | --- | --- |
| Python | 3.14.3 | Runtime used by the current project environment |
| OpenCV | `opencv-python>=4.13.0` | Webcam capture, frame display, drawing text overlays |
| MediaPipe | `mediapipe==0.10.35` | Tasks-based hand landmark detection and landmark visualization |
| PyAutoGUI | `pyautogui>=0.9.54` | Mouse movement, clicking, scrolling, media keys |
| NumPy | `numpy>=2.4.0` | Numeric distance calculations and frame-compatible data handling |
| pycaw | `pycaw>=20251023` | System audio volume control (Windows) |
| comtypes | `comtypes>=1.4.0` | Windows COM interop for pycaw |

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

Volume control requires Windows with `pycaw`. On other platforms, the volume feature degrades gracefully (status displays but system volume is not changed).

## Performance

GestureOS defaults to `640x480` because MediaPipe inference cost scales with frame size. This is the best default for responsive pointer control and should usually feel faster than `1280x720`.

Supported capture settings are configured in `configs/constants.py`:

| Resolution | Recommended Use | Expected Behavior |
| --- | --- | --- |
| `640x480` | Default performance mode | Lowest latency, best chance of 45-60 FPS |
| `960x540` | Balanced mode | Better image detail with moderate latency |
| `1280x720` | Quality mode | Best visual detail, highest inference cost |

Key performance constants:

- `CAMERA_WIDTH` / `CAMERA_HEIGHT`: active capture resolution.
- `CURSOR_SMOOTHING_FACTOR`: higher values follow the hand faster; lower values reduce jitter.
- `CURSOR_DEAD_ZONE_PX`: filters tiny cursor movements.
- `ENABLE_LANDMARK_DRAWING`: turns landmark drawing on or off.
- `VOLUME_SMOOTHING_FACTOR`: smooths volume changes.

Expected FPS depends heavily on CPU, webcam driver, lighting, and background load. On typical laptop hardware, `640x480` should be the first setting to try for 45-60 FPS.

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

Gestures are mode-dependent. See `CONTROLS.md` for full details.

## Project Structure

```text
GestureOS/
|-- main.py
|-- requirements.txt
|-- README.md
|-- DEVELOPMENT_LOG.md
|-- CONTROLS.md
|-- modes/
|   |-- __init__.py
|   `-- mode_manager.py
|-- trackers/
|   |-- __init__.py
|   `-- hand_tracker.py
|-- controllers/
|   |-- __init__.py
|   |-- base_controller.py
|   |-- mouse_controller.py
|   |-- volume_controller.py
|   |-- media_controller.py
|   `-- screenshot_controller.py
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
    |-- screenshots/
    `-- models/
```

## System Architecture

GestureOS separates camera, gesture, control, and rendering concerns:

- `HandTracker` owns webcam access, MediaPipe initialization, landmark extraction, coordinate conversion, and landmark drawing.
- `GestureDetector` owns gesture recognition, normalized finger-distance calculations, hold-state tracking, and new gesture detection (open hand, peace sign, three-finger pinch, swipe).
- `BaseController` is the abstract base class for all mode controllers. It defines the `handle_gesture(gesture, landmarks)` interface.
- `MouseController`, `VolumeController`, `MediaController` extend `BaseController` and implement mode-specific actions.
- `ScreenshotController` is a global controller triggered by the three-finger pinch gesture.
- `ModeManager` owns mode state, routes gestures to the active controller, and handles mode transitions.
- `GestureOSApplication` owns the main loop, module coordination, overlay rendering, lifecycle, and shutdown.
- `configs/constants.py` owns configurable thresholds, camera settings, UI colors, cooldown values, and smoothing parameters.

## Data Flow

```text
Webcam frame
  -> HandTracker.read_frame()
  -> HandTracker.process_frame()
  -> normalized landmark map
  -> GestureDetector.detect()
  -> GestureResult
  -> ModeManager.handle_gesture()
    -> (global exit check)
    -> (global screenshot check)
    -> (mode switch check)
    -> active controller handle_gesture()
  -> PyAutoGUI / system action
  -> GestureOSApplication overlay rendering
  -> OpenCV window
```

Runtime diagnostics shown in the OpenCV window:

- FPS
- Frame processing time in milliseconds
- Active camera resolution
- Detection confidence
- Current mode
- Active gesture
- Mode-specific status (volume percentage, media action)
- System status

## Future Roadmap

These features are planned for future phases:

- Presentation Mode
- Gaming Mode
- Air Drawing Recognition
- Custom Gesture Training
- Gesture Macros
- Gesture Analytics
- Multi-Hand Support
- User Profiles
- AI-Based Gesture Recognition

The mode system and `BaseController` interface are designed so these features can be added as new controllers without refactoring existing code.

## Troubleshooting

- Webcam does not open: close other camera apps, check OS permissions, and verify `CAMERA_INDEX` in `configs/constants.py`.
- Low FPS: use `640x480`, close other webcam consumers, and reduce landmark drawing frequency.
- Cursor feels slow: increase `CURSOR_SMOOTHING_FACTOR` in small steps such as `0.05`.
- Cursor jumps too quickly: lower `CURSOR_SMOOTHING_FACTOR` or increase `CURSOR_DEAD_ZONE_PX`.
- Clicks trigger too easily: reduce `PINCH_DISTANCE_THRESHOLD` or increase click cooldowns.
- Volume control does nothing: install `pycaw` and `comtypes` on Windows.
- Media keys not working: ensure your media player supports keyboard media keys.
- Screenshots not saving: verify `assets/screenshots/` exists and is writable.
- Mode not switching: hold the activation gesture steadily for 2 full seconds. Mode switching has a 1.5s cooldown between switches.
- MediaPipe install issues: use Python 3.14.3 with `mediapipe==0.10.35`.
- Missing model file: download `hand_landmarker.task` and place it in `assets/models/`.

## License

No license has been selected yet. Add a license before publishing or accepting external contributions.
