"""AI subsystem configuration for GestureOS.

Settings specific to feature extraction, model inference, and the
hybrid detection pipeline live here rather than in constants.py
to keep AI concerns isolated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


FEATURE_COUNT: Final[int] = 61

AI_ENABLED: Final[bool] = True
AI_MODEL_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "assets" / "models" / "gesture_model.pkl"
)
AI_CONFIDENCE_THRESHOLD: Final[float] = 0.7
AI_INFERENCE_TIMEOUT_MS: Final[int] = 10

DEFAULT_PROFILE: Final[str] = "default"

# ── Dataset Storage ────────────────────────────────────────────
DATASET_DIR: Final[Path] = (
    Path(__file__).resolve().parents[1] / "datasets"
)

# ── Gesture Recorder ───────────────────────────────────────────
RECORDER_WINDOW_NAME: Final[str] = "GestureOS — Record Gestures"
RECORDER_CAMERA_INDEX: Final[int] = 0
RECORDER_CAMERA_WIDTH: Final[int] = 640
RECORDER_CAMERA_HEIGHT: Final[int] = 480

# Gesture-pose labels (describe hand shape, not action)
# Initial training set: 9 labels (NO_HAND, POINTING, PINCH_INDEX, PINCH_MIDDLE,
#   TWO_FINGER_UP, OPEN_HAND, FIST, THREE_FINGER_PINCH, PEACE)
# Reserved (excluded from initial training): PINCH_PINKY
# Dynamic gestures (SWIPE_RIGHT, SWIPE_LEFT) are temporal — excluded from static dataset.
RECORDER_LABEL_MAP: Final[dict[int, str]] = {
    ord("0"): "NO_HAND",
    ord("1"): "POINTING",
    ord("2"): "PINCH_INDEX",
    ord("3"): "PINCH_MIDDLE",
    ord("4"): "TWO_FINGER_UP",
    ord("5"): "OPEN_HAND",
    ord("6"): "FIST",
    ord("7"): "THREE_FINGER_PINCH",
    ord("8"): "PINCH_PINKY",
    ord("9"): "PEACE",
}

RECORDER_RECORD_KEY: Final[int] = ord(" ")
RECORDER_TOGGLE_CONTINUOUS_KEY: Final[int] = ord("r")
RECORDER_SUMMARY_KEY: Final[int] = ord("s")
RECORDER_UNDO_KEY: Final[int] = ord("u")
RECORDER_QUIT_KEY: Final[int] = ord("q")
RECORDER_AUTO_SAVE_INTERVAL: Final[int] = 50

# ── Data Augmenter ─────────────────────────────────────────────
AUGMENT_N_VARIATIONS: Final[int] = 4
# Feature extractor schema version — bump on breaking feature changes
FEATURE_EXTRACTOR_SCHEMA_VERSION: Final[int] = 1

AUGMENT_JITTER_STD: Final[float] = 0.015
AUGMENT_SCALE_MIN: Final[float] = 0.90
AUGMENT_SCALE_MAX: Final[float] = 1.10
AUGMENT_FEATURE_DROPOUT_PROB: Final[float] = 0.05
