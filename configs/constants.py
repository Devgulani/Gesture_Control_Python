"""Application-wide constants for GestureOS.

All tunable values live here so gesture sensitivity, smoothing, and UI
behavior can be adjusted without changing core logic.
"""

from __future__ import annotations

from typing import Final, Tuple


APP_NAME: Final[str] = "GestureOS"
WINDOW_NAME: Final[str] = "GestureOS - Touchless Control"

CAMERA_INDEX: Final[int] = 0
CAMERA_WIDTH: Final[int] = 1280
CAMERA_HEIGHT: Final[int] = 720
FRAME_FLIP_HORIZONTAL: Final[bool] = True

MAX_NUM_HANDS: Final[int] = 1
MODEL_COMPLEXITY: Final[int] = 1
MIN_DETECTION_CONFIDENCE: Final[float] = 0.7
MIN_TRACKING_CONFIDENCE: Final[float] = 0.7

CURSOR_DEAD_ZONE_PX: Final[int] = 5
CURSOR_SMOOTHING_FACTOR: Final[float] = 0.25
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

OVERLAY_ORIGIN: Final[Tuple[int, int]] = (20, 34)
OVERLAY_LINE_HEIGHT: Final[int] = 32
OVERLAY_FONT_SCALE: Final[float] = 0.75
OVERLAY_FONT_THICKNESS: Final[int] = 2
OVERLAY_TEXT_COLOR: Final[Tuple[int, int, int]] = (235, 245, 255)
OVERLAY_ACCENT_COLOR: Final[Tuple[int, int, int]] = (72, 219, 251)
OVERLAY_WARNING_COLOR: Final[Tuple[int, int, int]] = (0, 195, 255)
OVERLAY_SUCCESS_COLOR: Final[Tuple[int, int, int]] = (80, 220, 120)
OVERLAY_BACKGROUND_COLOR: Final[Tuple[int, int, int]] = (18, 24, 32)

EXIT_KEY: Final[int] = ord("q")
