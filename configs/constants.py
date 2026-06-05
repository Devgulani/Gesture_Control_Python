"""Application-wide constants for GestureOS.

All tunable values live here so gesture sensitivity, smoothing, and UI
behavior can be adjusted without changing core logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Tuple


APP_NAME: Final[str] = "GestureOS"
WINDOW_NAME: Final[str] = "GestureOS - Touchless Control"

CAMERA_INDEX: Final[int] = 0
SUPPORTED_CAMERA_RESOLUTIONS: Final[Tuple[Tuple[int, int], ...]] = (
    (640, 480),
    (960, 540),
    (1280, 720),
)
CAMERA_WIDTH: Final[int] = 640
CAMERA_HEIGHT: Final[int] = 480
CAMERA_TARGET_FPS: Final[int] = 60
CAMERA_BUFFER_SIZE: Final[int] = 1
FRAME_FLIP_HORIZONTAL: Final[bool] = True

MAX_NUM_HANDS: Final[int] = 1
MODEL_COMPLEXITY: Final[int] = 1
MIN_DETECTION_CONFIDENCE: Final[float] = 0.7
MIN_TRACKING_CONFIDENCE: Final[float] = 0.7
MIN_HAND_PRESENCE_CONFIDENCE: Final[float] = 0.7
HAND_LANDMARKER_MODEL_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "models"
    / "hand_landmarker.task"
)

CURSOR_DEAD_ZONE_PX: Final[int] = 3
CURSOR_SMOOTHING_FACTOR: Final[float] = 0.45
CURSOR_BOUNDARY_MARGIN_RATIO: Final[float] = 0.12

LEFT_CLICK_COOLDOWN_SECONDS: Final[float] = 0.45
RIGHT_CLICK_COOLDOWN_SECONDS: Final[float] = 0.65
SCROLL_COOLDOWN_SECONDS: Final[float] = 0.08

PINCH_DISTANCE_THRESHOLD: Final[float] = 0.055
SCROLL_DISTANCE_THRESHOLD: Final[float] = 0.075
FIST_FINGER_TIP_TO_WRIST_THRESHOLD: Final[float] = 0.22
EXIT_HOLD_SECONDS: Final[float] = 2.0

SCROLL_AMOUNT: Final[int] = 5
FPS_AVERAGING_WINDOW: Final[int] = 10
ENABLE_LANDMARK_DRAWING: Final[bool] = True
LANDMARK_DRAW_INTERVAL_FRAMES: Final[int] = 1

OVERLAY_ORIGIN: Final[Tuple[int, int]] = (20, 34)
OVERLAY_LINE_HEIGHT: Final[int] = 27
OVERLAY_FONT_SCALE: Final[float] = 0.62
OVERLAY_FONT_THICKNESS: Final[int] = 2
OVERLAY_PANEL_WIDTH: Final[int] = 500
OVERLAY_TEXT_COLOR: Final[Tuple[int, int, int]] = (235, 245, 255)
OVERLAY_ACCENT_COLOR: Final[Tuple[int, int, int]] = (72, 219, 251)
OVERLAY_WARNING_COLOR: Final[Tuple[int, int, int]] = (0, 195, 255)
OVERLAY_SUCCESS_COLOR: Final[Tuple[int, int, int]] = (80, 220, 120)
OVERLAY_BACKGROUND_COLOR: Final[Tuple[int, int, int]] = (18, 24, 32)

EXIT_KEY: Final[int] = ord("q")
