# Development Log

## 2026-06-04 - MVP Architecture and Implementation

### Initial Architecture Decisions

- Chose a modular OOP structure with separate packages for tracking, gestures, controllers, utilities, and configuration.
- Kept `main.py` as an application manager instead of placing webcam, gesture, and mouse logic in one file.
- Centralized all sensitivity thresholds, camera settings, overlay styling, cooldowns, and smoothing values in `configs/constants.py`.
- Used normalized MediaPipe landmark coordinates for gesture detection so thresholds are less dependent on camera resolution.
- Used pixel coordinates only for visualization and screen-mapping support.

### Alternatives Considered

- A procedural single-file prototype was rejected because it would be harder to extend with volume, brightness, analytics, or custom gesture modules.
- A GUI framework was rejected because the MVP explicitly requires only an OpenCV webcam window.
- A machine-learning gesture classifier was deferred because the MVP gestures can be implemented reliably with landmark geometry and state tracking.
- Multi-hand tracking was deferred to avoid expanding gesture ambiguity in the MVP.

### Benefits

- Clear separation of concerns keeps the main loop easy to read.
- Future modules can be added by introducing new controllers or gesture recognizers without replacing the webcam pipeline.
- Centralized constants make camera tuning and gesture calibration straightforward.
- Cooldown and held-pinch state reduce accidental repeated clicks.

### Tradeoffs

- Rule-based gesture recognition is simpler and explainable, but it may require threshold tuning across different hands, cameras, and lighting conditions.
- PyAutoGUI is portable and minimal, but OS-level security settings can affect mouse-control permissions.
- The scroll gesture uses a simple two-finger vertical offset, which is easy to implement but may need refinement after real-world testing.

### Features Implemented

- Webcam initialization and frame capture
- One-hand MediaPipe tracking
- Landmark extraction into typed `Point` objects
- Landmark visualization
- FPS counter
- OpenCV status overlay
- Index-finger cursor control
- Cursor smoothing and dead-zone handling
- Camera-to-screen coordinate mapping with configurable margins
- Left-click thumb-index pinch detection
- Right-click thumb-middle pinch detection
- Held-pinch protection and click cooldowns
- Two-finger scroll detection
- Scroll cooldown
- Closed-fist exit gesture with 2-second hold
- Safe webcam release and OpenCV window cleanup
- Keyboard exit with `Q`

### Files Created

- `main.py`
- `requirements.txt`
- `README.md`
- `DEVELOPMENT_LOG.md`
- `configs/__init__.py`
- `configs/constants.py`
- `trackers/__init__.py`
- `trackers/hand_tracker.py`
- `gestures/__init__.py`
- `gestures/gesture_detector.py`
- `controllers/__init__.py`
- `controllers/mouse_controller.py`
- `utils/__init__.py`
- `utils/helpers.py`
- `assets/.gitkeep`

### Dependencies Added

- `opencv-python`: webcam capture, rendering, and OpenCV UI window
- `mediapipe`: real-time hand landmark detection
- `pyautogui`: cursor movement, clicking, and scrolling
- `numpy`: distance calculations and numeric helpers

### Changes Made

- Created the requested clean folder organization.
- Implemented the MVP gesture-control pipeline.
- Added documentation for usage, structure, architecture, data flow, troubleshooting, and roadmap.
- Added dependency rationale and version recommendations.

### Future Tasks

- Calibrate gesture thresholds on multiple webcams and lighting conditions.
- Add automated unit tests for geometry-based gesture detection.
- Add optional configuration loading while preserving constants as defaults.
- Add volume, brightness, screenshot, media, presentation, and gaming controllers in later phases.
- Add analytics, user profiles, and AI-based gesture recognition in later phases.

## 2026-06-04 - MediaPipe 0.10.35 Compatibility Refactor

### Compatibility Audit

- Verified the local environment reports MediaPipe `0.10.35`.
- Verified top-level `mediapipe` exposes `tasks`, `Image`, and `ImageFormat`.
- Verified top-level `mediapipe` does not expose `solutions`.
- Verified the supported hand API is `mediapipe.tasks.python.vision.HandLandmarker`.
- Verified MediaPipe Tasks supports `IMAGE`, `VIDEO`, and `LIVE_STREAM` running modes.

### Root Cause

The previous tracker used the legacy API:

```python
import mediapipe as mp
mp.solutions.hands.Hands(...)
```

MediaPipe `0.10.35` in the current Python 3.14.3 environment is packaged around the Tasks API and does not provide `mp.solutions`. This caused startup to fail before webcam processing began.

### Chosen Solution

- Refactored `trackers/hand_tracker.py` to use `vision.HandLandmarker`.
- Configured the landmarker with `vision.RunningMode.VIDEO`.
- Converted OpenCV BGR frames to contiguous SRGB `mediapipe.Image` objects.
- Preserved the existing `LandmarkMap` output so gesture and mouse modules remain unchanged.
- Reused the Tasks drawing utilities and hand connection definitions for landmark rendering.
- Added `HAND_LANDMARKER_MODEL_PATH` and `MIN_HAND_PRESENCE_CONFIDENCE` to `configs/constants.py`.

### Benefits

- Removes all dependency on unsupported `mp.solutions` APIs.
- Keeps existing architecture and gesture logic intact.
- Aligns hand tracking with the installed MediaPipe 0.10.35 package.
- Produces the same normalized landmark shape required by existing gesture detection.

### Tradeoffs

- MediaPipe Tasks requires an external `hand_landmarker.task` model asset.
- Startup now validates that the model exists and raises a clear setup error if it is missing.
- The model asset is stored under `assets/models/` rather than bundled through Python package imports.

### Files Changed

- `trackers/hand_tracker.py`
- `configs/constants.py`
- `requirements.txt`
- `README.md`
- `DEVELOPMENT_LOG.md`
- `assets/models/.gitkeep`

### Verification

- Compiled all project Python modules successfully.
- Constructed `GestureOSApplication` successfully with MediaPipe 0.10.35.
- Opened the webcam through `HandTracker.start()`.
- Processed 60 webcam frames at `(720, 1280, 3)`.
- Detected all 21 hand landmarks during the probe.
- Confirmed no unsupported `mp.solutions` or `solutions.hands.Hands` references remain in source code.
- Downloaded `assets/models/hand_landmarker.task` for local verification and ignored `assets/models/*.task` in `.gitignore` to avoid committing runtime model binaries.

## 2026-06-05 - Performance and Documentation Optimization

### Bottlenecks Identified

- The default camera resolution was `1280x720`, which increases MediaPipe inference work and can hold FPS near 30 on typical laptop hardware.
- Cursor smoothing used a conservative `0.25` smoothing factor, which reduced jitter but added noticeable pointer lag.
- PyAutoGUI retained default pause and duration behavior, which can add small delays to repeated mouse actions.
- Runtime diagnostics did not show frame processing time, active camera resolution, or detection confidence, making tuning harder.
- Controls were documented only as a short README list, with no dedicated `CONTROLS.md`.

### Optimizations Applied

- Changed the default camera resolution to `640x480`.
- Added supported camera resolution presets in `configs/constants.py`: `640x480`, `960x540`, and `1280x720`.
- Added `CAMERA_TARGET_FPS` and `CAMERA_BUFFER_SIZE` constants.
- Requested low camera buffering with `cv2.CAP_PROP_BUFFERSIZE`.
- Added active camera resolution tracking to `HandTracker`.
- Added frame processing time diagnostics to the OpenCV overlay.
- Added MediaPipe handedness confidence display when available.
- Made landmark drawing configurable with `ENABLE_LANDMARK_DRAWING` and `LANDMARK_DRAW_INTERVAL_FRAMES`.
- Reduced overlay font size and line height to keep the expanded diagnostics compact.
- Changed `Point` to a slotted frozen dataclass to reduce per-frame object overhead.
- Increased `CURSOR_SMOOTHING_FACTOR` from `0.25` to `0.45` for lower perceived latency.
- Reduced `CURSOR_DEAD_ZONE_PX` from `5` to `3` for finer pointer response.
- Disabled PyAutoGUI pause and minimum duration in `MouseController`.

### Before And After Performance Notes

- Before: user-reported average runtime performance was approximately 30 FPS with functional but slower-than-desired cursor response.
- After: code defaults to performance-oriented `640x480`, requests 60 FPS capture, reduces cursor smoothing lag, lowers capture buffering, and exposes diagnostics for live tuning.
- A local webcam benchmark attempt during this update stalled inside the camera driver and timed out without reliable numeric output. Earlier verification confirmed webcam and hand landmark detection worked, and this change was compile-verified after optimization.

### Documentation Updates

- Added an early README Controls section with a gesture/action/mode table.
- Added README Performance, recommended camera settings, expected FPS ranges, and tuning guidance.
- Added runtime diagnostics documentation.
- Added reserved future gestures to README.
- Created `CONTROLS.md` to document implemented controls, thresholds, cooldowns, modes, troubleshooting, and reserved gestures.

### Files Changed

- `configs/constants.py`
- `controllers/mouse_controller.py`
- `main.py`
- `trackers/hand_tracker.py`
- `utils/helpers.py`
- `README.md`
- `CONTROLS.md`
- `DEVELOPMENT_LOG.md`
