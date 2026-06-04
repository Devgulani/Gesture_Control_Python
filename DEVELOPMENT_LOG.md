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
