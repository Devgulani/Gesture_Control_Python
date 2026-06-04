"""Shared utility helpers for GestureOS."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, Tuple, TypeVar

import cv2
import numpy as np

from configs import constants


T = TypeVar("T", int, float)


@dataclass(frozen=True)
class Point:
    """A normalized and pixel coordinate pair for a hand landmark."""

    x: float
    y: float
    z: float
    pixel_x: int
    pixel_y: int


class FPSCounter:
    """Tracks a rolling frames-per-second estimate."""

    def __init__(self, window_size: int = constants.FPS_AVERAGING_WINDOW) -> None:
        """Initialize the counter with a bounded timestamp window."""
        self._timestamps: Deque[float] = deque(maxlen=window_size)

    def update(self) -> float:
        """Record a frame timestamp and return the current rolling FPS."""
        now = time.perf_counter()
        self._timestamps.append(now)
        if len(self._timestamps) < 2:
            return 0.0

        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._timestamps) - 1) / elapsed


def clamp(value: T, minimum: T, maximum: T) -> T:
    """Clamp a numeric value into the inclusive range [minimum, maximum]."""
    return max(minimum, min(value, maximum))


def euclidean_distance(point_a: Point, point_b: Point) -> float:
    """Return 2D normalized distance between two landmarks."""
    return float(np.hypot(point_a.x - point_b.x, point_a.y - point_b.y))


def draw_status_panel(
    frame: np.ndarray,
    rows: Iterable[Tuple[str, Tuple[int, int, int]]],
) -> None:
    """Draw a compact status overlay on the camera frame."""
    rows_list = list(rows)
    x, y = constants.OVERLAY_ORIGIN
    panel_width = 470
    panel_height = constants.OVERLAY_LINE_HEIGHT * len(rows_list) + 22

    cv2.rectangle(
        frame,
        (x - 12, y - 28),
        (x + panel_width, y + panel_height - 28),
        constants.OVERLAY_BACKGROUND_COLOR,
        thickness=-1,
    )

    for index, (text, color) in enumerate(rows_list):
        line_y = y + (index * constants.OVERLAY_LINE_HEIGHT)
        cv2.putText(
            frame,
            text,
            (x, line_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            constants.OVERLAY_FONT_SCALE,
            color,
            constants.OVERLAY_FONT_THICKNESS,
            cv2.LINE_AA,
        )
