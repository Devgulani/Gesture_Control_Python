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

## 2026-06-06 - Phase 3: Mode System and New Controllers

### Architecture Changes

- Created `controllers/base_controller.py`: abstract base class defining `handle_gesture(gesture, landmarks)` interface and `ControllerStatus`/`OverlayData` data classes.
- Created `modes/mode_manager.py`: orchestrates mode state, routes gestures to the active controller, handles mode transitions, and manages global gestures (exit, screenshot).
- Refactored `controllers/mouse_controller.py` to extend `BaseController`. Changed `handle_gesture` signature to accept `(gesture, landmarks)` instead of `(gesture, index_tip)`. Removed local `ControllerStatus` class in favor of the shared one from `base_controller.py`.
- Updated `main.py`: replaced direct `MouseController` usage with `ModeManager`. Overlay rendering now collects structured data from all controllers via `get_overlay_data()`. Added volume bar rendering in Volume Mode.
- Introduced `modes/` package for mode management code.

### GestureDetector Enhancements

Extended `GestureDetector` with new detection methods:

- `_is_open_hand()`: all five finger tips far from wrist -> returns `OPEN_HAND`, then `OPEN_HAND_HELD` after 1 second hold.
- `_is_peace_sign()`: index+middle extended, ring+pinky curled, fingers aligned vertically -> returns `PEACE_SIGN`, then `PEACE_HELD` after 1 second hold.
- `_is_three_finger_pinch()`: thumb, index, and middle tips all close together -> returns `THREE_FINGER_PINCH`, then `SCREENSHOT_READY` after brief hold.
- `_detect_swipe()`: wrist x-coordinate delta between frames with cooldown -> `SWIPE_RIGHT` / `SWIPE_LEFT`.
- Added generic `hold_progress` field to `GestureResult` for overlay progress display.
- Added `_reset_hold_timers()` to cleanly manage concurrent hold timers.
- Detection priority: fist (exit) > three-finger pinch (screenshot) > open hand (volume mode) > peace sign (media mode) > right pinch > left pinch > scroll > swipe > move. This ordering prevents conflicts between mode activation gestures and existing mouse gestures.

### New Controllers

- `controllers/volume_controller.py`: maps thumb-index normalized distance to system volume percentage (0-100%). Uses `pycaw` for Windows audio API with graceful fallback if unavailable. Smoothing and cooldown prevent jitter.
- `controllers/media_controller.py`: maps open palm -> play/pause, swipe right -> next track, swipe left -> previous track via `pyautogui.press()` media keys. Cooldown prevents repeated triggers.
- `controllers/screenshot_controller.py`: captures and saves screenshots via `pyautogui.screenshot()` to `assets/screenshots/screenshot_YYYYMMDD_HHMMSS.png`. Cooldown prevents rapid captures.

### Mode Switching Design

- Mouse -> Volume: open hand held 1 second
- Volume -> Mouse: open hand held 1 second
- Mouse -> Media: peace sign held 1 second
- Media -> Mouse: peace sign held 1 second
- Mode switch gestures are mode-aware: open hand in Media mode routes to MediaController (play/pause); peace sign in Volume mode routes to VolumeController (no-op).

### Constants Added

Added to `configs/constants.py`:

- `MODE_ACTIVATION_HOLD_SECONDS`: 1.0s hold for mode switching
- `VOLUME_SMOOTHING_FACTOR`, `VOLUME_MIN_DISTANCE`, `VOLUME_MAX_DISTANCE`, `VOLUME_COOLDOWN_SECONDS`: volume control tuning
- `MEDIA_COOLDOWN_SECONDS`: 0.5s debounce for media actions
- `SWIPE_THRESHOLD`, `SWIPE_COOLDOWN_SECONDS`: swipe detection tuning
- `SCREENSHOT_COOLDOWN_SECONDS`: 2.0s cooldown between screenshots
- `SCREENSHOT_HOLD_SECONDS`: 0.3s hold for screenshot activation
- `THREE_FINGER_PINCH_THRESHOLD`: distance threshold for three-finger pinch
- `OPEN_HAND_FINGER_TIP_TO_WRIST_THRESHOLD`: minimum distance for open hand detection
- `VOLUME_BAR_*`: volume bar overlay styling
- `SCREENSHOTS_DIR`: screenshots output directory

### Dependencies Added

- `pycaw`: Windows Core Audio API for system volume control
- `comtypes`: COM interop required by pycaw

### Files Created

- `controllers/base_controller.py`
- `controllers/volume_controller.py`
- `controllers/media_controller.py`
- `controllers/screenshot_controller.py`
- `modes/__init__.py`
- `modes/mode_manager.py`

### Files Modified

- `main.py`
- `controllers/mouse_controller.py`
- `gestures/gesture_detector.py`
- `configs/constants.py`
- `requirements.txt`
- `README.md`
- `CONTROLS.md`
- `DEVELOPMENT_LOG.md`

### Verification

- Compiled all project Python modules successfully.
- All imports resolve correctly with and without optional dependencies.
- Mode switching logic verified: Mouse -> Volume -> Mouse and Mouse -> Media -> Mouse transitions work correctly.
- Mode-gated switching verified: open hand in Media mode does not switch to Volume; peace sign in Volume mode does not switch to Media.
- GestureResult hold_progress tracking verified for open hand, peace sign, and three-finger pinch.
- Controller interface compatibility verified: all controllers implement `handle_gesture(gesture, landmarks)` and `get_overlay_data()`.
- Exit gesture and Q key remain functional as global controls.
- All existing mouse controls preserved with identical behavior in Mouse Mode.
- Performance: new gestures add negligible per-frame overhead (one additional distance check per new detection method).

## 2026-06-06 - .gitignore Hygiene and Folder Tracking

### Changes Made

- Replaced `assets/screenshots/` (which completely hid the directory) with `assets/screenshots/*` + `!assets/screenshots/.gitkeep`. This ignores runtime screenshots while keeping the folder tracked in git.
- Replaced `assets/models/*.task` (which only ignored `.task` files) with `assets/models/*` + `!assets/models/.gitkeep`. This ignores all model downloads (`.task`, `.tflite`, etc.) while keeping the folder tracked.
- Created `assets/screenshots/.gitkeep` so the screenshot output folder exists in fresh clones.
- Added common patterns: `*.tmp`, `*.temp`, `*.bak` (temp files); `*.db`, `*.sqlite3` (local databases); `.cursor/`, `.opencode/` (editor config); `.ipynb_checkpoints/` (Jupyter artifacts).
- Preserved all existing rules unchanged.

### Verification

Confirmed via `git check-ignore` and `git add --dry-run`:

- `.venv/`, `__pycache__/`, `.vscode/`, `.idea/` — all ignored
- `assets/screenshots/photo.png` — ignored by `assets/screenshots/*`
- `assets/models/hand_landmarker.task` — ignored by `assets/models/*`
- `assets/screenshots/.gitkeep` — not ignored, can be added to git
- `assets/.gitkeep` and `assets/models/.gitkeep` — already tracked in git index
- `*.tmp`, `*.bak`, `*.db`, etc. — all ignored correctly

## 2026-06-06 - Bug Fixes and UX Improvements

### Exit Gesture Reliability Fix

**Root cause**: `_fist_started_at` was reset to `time.perf_counter()` on every frame fist was detected, so `_detect_exit_hold()` always computed `hold_duration ≈ 0`. The 2-second hold could never accumulate.

**Fix**: Only set `_fist_started_at` when it is `None` (first frame of fist detection). Jitter protection added: if fist is briefly lost (< 150ms gap), the hold timer continues rather than resetting. Improved `_is_fist()` with dual validation — finger-fold check (tip y > mcp y) plus distance-to-wrist check — for robust detection across hand sizes and lighting conditions.

### Mode Switch Hold Duration

Increased from 1s to 2s (`MODE_SWITCH_HOLD_SECONDS`) to reduce accidental switches. Old constant `MODE_ACTIVATION_HOLD_SECONDS` renamed everywhere.

### Mode Switch Cooldown

Added `MODE_SWITCH_COOLDOWN_SECONDS = 1.5s` between mode switches to prevent rapid oscillation. Overlay shows remaining cooldown. Mode-switch gestures are ignored during cooldown.

### Volume Transition Lock

When entering/exiting Volume Mode, `VolumeController` enters a `_transition_locked` state for `VOLUME_TRANSITION_DELAY = 0.75s`, preventing the hand shape from being interpreted as a volume-setting gesture during the transition. `ModeManager` also locks state during transitions via `_lock_state()`.

### Cursor Freeze During Click Lock

During pinches (left/right), the cursor position is frozen at the pre-pinch location. A `CLICK_LOCK_DURATION = 0.3s` freeze persists after pinch release to prevent cursor jump. Smoothed coordinates are preserved throughout the lock.

### Scroll Speed Increase

`SCROLL_AMOUNT` increased from 5 to 15. `SCROLL_COOLDOWN_SECONDS` reduced from 0.08 to 0.04. Combined effect: significantly faster scrolling with each gesture.

### Overlay Diagnostics

- Mode lock state and reason displayed when active
- Mode switch cooldown countdown
- Exit progress now shows "Exit Gesture Detected — Holding X.X / 2.0s"
- Transition messages ("Volume Mode activated", "Mouse Mode activated") shown briefly

### Code Quality

All tunable values centralized in `configs/constants.py` (no magic numbers). Added `FIST_FINGER_FOLD_THRESHOLD`, `FIST_HOLD_JITTER_THRESHOLD`, `CLICK_LOCK_DURATION`, `MODE_SWITCH_COOLDOWN_SECONDS`, `VOLUME_TRANSITION_DELAY`. Renamed `MODE_ACTIVATION_HOLD_SECONDS` to `MODE_SWITCH_HOLD_SECONDS`.

### Files Modified

- `configs/constants.py`
- `gestures/gesture_detector.py`
- `controllers/mouse_controller.py`
- `controllers/volume_controller.py`
- `modes/mode_manager.py`
- `main.py`
- `README.md`
- `CONTROLS.md`
- `DEVELOPMENT_LOG.md`

## 2026-06-08 - Phase 1A: AI Foundation Layer

### Architecture Decisions

- Created a minimal AI subsystem that runs silently alongside the existing rule-based pipeline with zero behavioral changes.
- Followed the approved AI Architecture Design Document and Implementation Roadmap to ensure forward compatibility with future phases.
- Chose a passive integration pattern: the AI bridge receives landmarks every frame but never injects results into the gesture pipeline.
- Feature extraction uses a pre-allocated NumPy array to minimize per-frame allocation overhead.

### Design Constraints Honored

- **AI must be optional:** The bridge starts safely regardless of model availability. No model loading occurs in Phase 1A.
- **Rule-based remains the source of truth:** The gesture pipeline is completely unchanged. AI data is stored but unused.
- **Minimal footprint:** Only 8 new files, ~300 lines of code total. No new runtime dependencies.
- **Profile system decoupled from core:** ProfileManager stores settings independently; controllers never import profile modules directly.

### Feature Extractor Design

Implemented a 104-element feature vector with three components:

1. **Raw normalized coordinates (63 values):** All 21 MediaPipe landmarks as (x, y, z) triples in normalized space.
2. **Hand size (1 value):** Euclidean distance from wrist (landmark 0) to middle finger MCP (landmark 9). Used as a normalization reference for size invariance.
3. **Wrist-relative coordinates (40 values):** Landmarks 1-20 expressed as (x, y) offsets from the wrist, divided by hand size for scale invariance.

Invariance properties:
- **Hand size:** All wrist-relative coordinates are divided by the hand size scalar.
- **Camera distance:** MediaPipe already provides normalized (0-1) coordinates.
- **Screen resolution:** No pixel coordinates enter the feature vector.

### Files Created

- `configs/ai_config.py` — AI subsystem configuration constants
- `ai/__init__.py` — AI package marker
- `ai/features/__init__.py` — Features subpackage marker
- `ai/features/extractor.py` — FeatureExtractor class (104-element vector)
- `ai/bridge.py` — AiGestureBridge (non-blocking, thread-safe buffer)
- `profiles/__init__.py` — Profiles package marker
- `profiles/profile_manager.py` — ProfileManager + Profile dataclass
- `profiles/profiles/default.json` — Default user profile

### Files Modified

- `configs/constants.py` — Added `PROFILES_DIR` constant
- `main.py` — Integrated AiGestureBridge and ProfileManager initialization and lifecycle
- `README.md` — Updated architecture diagram, project structure, added AI Foundation section

### Verification

- All new modules compile and pass import verification.
- FeatureExtractor produces correct 104-element float32 vector for valid 21-landmark input.
- FeatureExtractor returns None for empty or partial landmark maps (graceful degradation).
- AiGestureBridge start/stop lifecycle verified (is_running state transitions correct).
- AiGestureBridge caches latest features thread-safely; returns None after stop().
- ProfileManager creates default profile on first run; round-trips save/load correctly.
- Full application imports successfully with all new modules.
- Existing gesture pipeline completely untouched — no behavioral regression possible.
- No new dependencies added to requirements.txt.

### Recommended Phase 1B Tasks

- Implement GestureRecorder with OpenCV recording UI
- Add DatasetStorage for CSV/JSON export
- Implement DataAugmenter for synthetic training data
- Begin collecting labeled gesture samples (target: 500+ per gesture)

## 2026-06-08 - Phase 1B: FeatureExtractor Refactor

### Architecture Decision

Following a detailed engineering audit that identified 39% feature redundancy, weak camera-distance invariance, and medium overfitting risk from z-coordinates and absolute hand position, the FeatureExtractor was redesigned from a 104-feature schema to a 61-feature schema.

### Changes from Phase 1A

**Removed:**
- All 21 z-coordinates (63 → 0 features) — eliminated camera-distance noise source
- All raw x,y normalised coordinates (42 → 0 features) — redundant with wrist-relative block and carried absolute-position overfitting risk

**Added:**
- 10 fingertip pairwise distances (C(5,2), normalised by hand size) — direct pinch/fist/open-hand signal
- 5 finger extension deltas (tip.y − mcp.y, continuous) — strongest per-gesture signal per audit
- 5 finger bend angle cosines (2D dot product at PIP joint, no z) — rotation-resistant curl information

**Kept:**
- 40 wrist-relative x,y coordinates (simplified: only 20 landmarks × 2, no z)
- 1 hand size scalar

### Feature Count Reduction

| Metric | Phase 1A | Phase 1B | Delta |
|---|---|---|---|
| Total features | 104 | 61 | −41% |
| Redundant features | ~40 | 0 | −100% |
| Overfitting surface | High | Low | Significantly reduced |

### Finger Spread Evaluation

The adjacent fingertip distances (index↔middle, middle↔ring, ring↔pinky) are already included in Group B's C(5,2) combinations. No separate Finger Spread group is needed. The target schema of 61 features is correct.

### Files Modified

- `configs/ai_config.py` — FEATURE_COUNT 104→61, removed unused config flags
- `ai/features/extractor.py` — Complete rewrite with 5-group pipeline
- `tests/test_feature_extractor.py` — Added 17 tests covering all feature groups and edge cases
- `README.md` — Updated feature vector documentation

### Verification

- All 17 tests pass (output shape, empty/partial landmarks, wrist-relative invariance, distance comparisons, extension deltas, angle cosines, hand size validity, determinism)
- Feature extraction benchmark: **0.134 ms** per call (target: <0.5 ms)
- AiGestureBridge requires **zero modifications** — bridge.latest_features.shape = (61,) naturally
- Main application imports successfully with no changes to gesture pipeline
- Existing controls and modes completely unchanged

### Files Created

- `tests/__init__.py` — Test package marker
- `tests/test_feature_extractor.py` — Feature extraction test suite

## 2026-06-08 - Phase 2: Dataset Infrastructure

### Changes

**New Modules:**
- `ai/data/dataset_storage.py` — DatasetStorage: save, load, export (CSV/JSON), train/test split for labeled feature vectors
- `ai/data/data_augmenter.py` — DataAugmenter: jitter, scale variation, feature dropout, and composite `augment_single` / `augment_dataset` pipelines
- `ai/data/gesture_recorder.py` — GestureRecorder: interactive OpenCV tool with live camera feed, label selection (0-9), single-shot and continuous recording modes, undo, and dataset summary
- `tools/record_gestures.py` — Standalone entry point (`python -m tools.record_gestures`)

**Config Updates:**
- `configs/ai_config.py` — Added 15 new constants for dataset paths, recorder keybindings, and augmentation parameters

### Files Created

- `ai/data/__init__.py`
- `ai/data/dataset_storage.py`
- `ai/data/data_augmenter.py`
- `ai/data/gesture_recorder.py`
- `tools/__init__.py`
- `tools/record_gestures.py`
- `tests/test_dataset_storage.py` (15 tests)
- `tests/test_data_augmenter.py` (14 tests)

### Verification

- 46/46 tests pass (15 dataset storage + 14 data augmenter + 17 feature extractor)
- End-to-end integration test: save → load → augment → export pipeline verified
- Bridge compatibility verified — no changes to `ai/bridge.py` or `main.py`
- Application imports successfully with no gesture pipeline modifications

### Storage Layout

```
datasets/
├── dataset_config.json      # version, feature_count
├── LABEL_1/
│   ├── sample_00000001.npy  # (61,) float32
│   ├── sample_00000002.npy
│   └── metadata.json
├── LABEL_2/
│   └── ...
└── ...
```

## 2026-06-08 — Phase 2 Audit Improvements

### Audit Findings Applied

| # | Issue | Resolution |
|---|-------|------------|
| 1 | Labels describe actions not poses | Renamed to gesture-pose labels: `PINCH_INDEX`, `TWO_FINGER_UP`, `FIST`, etc. |
| 2 | No session tracking | Auto-generated UUID4 session ID per recording session, stored in metadata |
| 3 | No profile tracking | Profile ID sourced from `ProfileManager.active.profile_name`, stored in metadata |
| 4 | No FEATURE_COUNT validation | `load_samples()` validates shape[-1] against config; warns on partial mismatch, raises on total mismatch |
| 5 | No feature extractor versioning | `dataset_config.json` now stores `feature_extractor_schema_version`; `_check_schema_version()` warns on mismatch at init |
| 6 | No raw landmark storage | Companion `_lm.npy` files (21×3 float32) stored alongside feature vectors |

### Storage Design Decision: Separate Landmark Files

Chosen **Option A** — separate `sample_00000001_lm.npy` files alongside existing `sample_00000001.npy`:

| Criterion | A: Separate files | B: Combined .npz | C: Per-label HDF5 |
|-----------|-------------------|------------------|-------------------|
| Backward compatible | Yes | No (migration) | No (migration) |
| Incremental writes | Yes (no rewrite) | Yes (no rewrite) | Complex (rewrite = full copy) |
| Targeted landmark load | Yes | Yes (load subset) | Partial (read subset) |
| Human-debuggable | Yes (.npy) | No (.npz) | No (binary) |
| File count at 4000 samples | 8000 files | 4000 files | ~10 files |
| Code complexity | Low | Low | High |

Selected **Option A** for backward compatibility and simple incremental recording. The 2× file count is irrelevant at expected dataset sizes (<1000 samples/gesture).

### Updated Storage Layout

```
datasets/
├── dataset_config.json               # schema_version, feature_count, feature_extractor_version
├── FIST/
│   ├── sample_00000001.npy           # features (61,) float32
│   ├── sample_00000001_lm.npy        # raw landmarks (21, 3) float32
│   └── metadata.json                 # {sample_id: {timestamp, source, session_id, profile_id}}
├── OPEN_HAND/
│   └── ...
└── ...
```

### Files Modified

- `configs/ai_config.py` — Renamed 10 label entries, added `FEATURE_EXTRACTOR_SCHEMA_VERSION`
- `ai/data/dataset_storage.py` — 9 new methods: landmark save/load/path helpers, FEATURE_COUNT validation, schema version check + config update, extended metadata schema
- `ai/data/gesture_recorder.py` — Session ID (uuid4), profile ID (ProfileManager), landmarks passed to storage, label colors updated
- `tests/test_dataset_storage.py` — 9 new tests (landmark storage, session/profile metadata, feature count validation, schema version, label isolation)

### Migration Impact

- **Zero migration required** — all new features are additive (optional parameters, companion files)
- Existing `.npy` files load without change
- Existing `metadata.json` files without `session_id`/`profile_id` load without error (fields are optional)
- Load validation warns but does not block on shape mismatch
- Config file is updated (schema_version `1.0` → `2.0`, new fields added) on first save; read-only access remains safe

### Test Coverage

- **56/56 tests pass** (24 dataset storage + 15 data augmenter + 17 feature extractor)
- Landmark round-trip: save → load_landmarks → validate shape + values
- Session/profile metadata: save → read JSON → assert fields present/absent
- Feature count validation: wrong-shape files are warned and skipped; all-wrong raises ValueError
- Schema version: config.json written with correct fields

## 2026-06-08 — Pre-Phase 3 Dataset Finalization

### Changes

- **Added** `THREE_FINGER_PINCH` to `RECORDER_LABEL_MAP` (key `7`, replacing `PINCH_RING`) and to `_LABEL_COLORS`
- **Finalized 9-label training set** for initial model training
- **Documented label categories** (initial training vs reserved vs excluded)

### Final Training Label Set

| Key | Label | Category | Notes |
|-----|-------|----------|-------|
| `0` | `NO_HAND` | Initial training | Negative class / background |
| `1` | `POINTING` | Initial training | Maps to `GestureName.MOVE` |
| `2` | `PINCH_INDEX` | Initial training | Maps to `GestureName.LEFT_CLICK` |
| `3` | `PINCH_MIDDLE` | Initial training | Maps to `GestureName.RIGHT_CLICK` |
| `4` | `TWO_FINGER_UP` | Initial training | Collapses `SCROLL_UP` + `SCROLL_DOWN` (direction is rule-based) |
| `5` | `OPEN_HAND` | Initial training | Collapses `OPEN_HAND` + `OPEN_HAND_HELD` |
| `6` | `FIST` | Initial training | Maps to `GestureName.EXIT_HOLD` |
| `7` | `THREE_FINGER_PINCH` | Initial training | Maps to `GestureName.SCREENSHOT_READY` |
| `8` | `PINCH_PINKY` | Reserved | Available for recording, excluded from initial training |
| `9` | `PEACE` | Initial training | Collapses `PEACE_SIGN` + `PEACE_HELD` |

### Excluded From Static Dataset

| Gesture | Reason | Future Path |
|---------|--------|-------------|
| `SWIPE_RIGHT` | Temporal (movement, not pose) | Sequence-based / temporal model |
| `SWIPE_LEFT` | Temporal (movement, not pose) | Sequence-based / temporal model |
| `PINCH_RING` | No detector implementation | Add when gesture is implemented |

### Updated Sample Count Recommendations

| Tier | Per Gesture | Total (9 labels) | Sessions Per Gesture |
|------|-------------|------------------|---------------------|
| MVP | 100 | 900 | 3 (30-35 samples each) |
| Minimum viable | 250 | 2250 | 6-8 |
| Production | 500+ | 4500+ | 10-15 |

### Files Modified

- `configs/ai_config.py` — Key `7` changed from `PINCH_RING` to `THREE_FINGER_PINCH`; added training-set comment
- `ai/data/gesture_recorder.py` — `_LABEL_COLORS` updated (added `THREE_FINGER_PINCH`, removed `PINCH_RING`)
- `README.md` — Label table updated with training set column, PINCH_PINKY marked reserved, swipes documented as future targets

### Next Steps (Phase 3)

1. Implement gesture classifier training pipeline
2. Train baseline model on MVP dataset (100 per gesture)
3. Add real-time inference to AiGestureBridge
4. Evaluate accuracy before scaling to production dataset
