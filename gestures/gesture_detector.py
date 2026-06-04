"""Gesture classification and gesture-state tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from configs import constants
from trackers.hand_tracker import LandmarkMap
from utils.helpers import euclidean_distance


class GestureName(str, Enum):
    """Supported MVP gesture labels."""

    NONE = "No Hand"
    MOVE = "Move Cursor"
    LEFT_CLICK = "Left Click Pinch"
    RIGHT_CLICK = "Right Click Pinch"
    SCROLL_UP = "Scroll Up"
    SCROLL_DOWN = "Scroll Down"
    EXIT_HOLD = "Exit Hold"


@dataclass(frozen=True)
class GestureResult:
    """A classified gesture and associated state flags."""

    name: GestureName
    is_left_pinch: bool = False
    is_right_pinch: bool = False
    is_scrolling: bool = False
    scroll_direction: int = 0
    is_exit_ready: bool = False
    exit_progress: float = 0.0


class GestureDetector:
    """Detects pinch, scroll, and exit gestures from hand landmarks."""

    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    INDEX_MCP = 5
    MIDDLE_TIP = 12
    MIDDLE_MCP = 9
    RING_TIP = 16
    RING_MCP = 13
    PINKY_TIP = 20
    PINKY_MCP = 17

    def __init__(self) -> None:
        """Initialize state needed for hold-based gestures."""
        self._fist_started_at: Optional[float] = None

    def detect(self, landmarks: LandmarkMap) -> GestureResult:
        """Classify the current hand pose."""
        if not self._has_required_landmarks(landmarks):
            self._fist_started_at = None
            return GestureResult(name=GestureName.NONE)

        if self._is_fist(landmarks):
            return self._detect_exit_hold()

        self._fist_started_at = None

        thumb_index_distance = euclidean_distance(
            landmarks[self.THUMB_TIP],
            landmarks[self.INDEX_TIP],
        )
        thumb_middle_distance = euclidean_distance(
            landmarks[self.THUMB_TIP],
            landmarks[self.MIDDLE_TIP],
        )

        is_left_pinch = thumb_index_distance < constants.PINCH_DISTANCE_THRESHOLD
        is_right_pinch = thumb_middle_distance < constants.PINCH_DISTANCE_THRESHOLD

        if is_right_pinch:
            return GestureResult(
                name=GestureName.RIGHT_CLICK,
                is_right_pinch=True,
            )

        if is_left_pinch:
            return GestureResult(
                name=GestureName.LEFT_CLICK,
                is_left_pinch=True,
            )

        scroll_direction = self._detect_scroll_direction(landmarks)
        if scroll_direction > 0:
            return GestureResult(
                name=GestureName.SCROLL_UP,
                is_scrolling=True,
                scroll_direction=scroll_direction,
            )
        if scroll_direction < 0:
            return GestureResult(
                name=GestureName.SCROLL_DOWN,
                is_scrolling=True,
                scroll_direction=scroll_direction,
            )

        return GestureResult(name=GestureName.MOVE)

    def _detect_exit_hold(self) -> GestureResult:
        """Return exit progress while a closed fist is held."""
        now = time.perf_counter()
        if self._fist_started_at is None:
            self._fist_started_at = now

        hold_duration = now - self._fist_started_at
        progress = min(hold_duration / constants.EXIT_HOLD_SECONDS, 1.0)
        return GestureResult(
            name=GestureName.EXIT_HOLD,
            is_exit_ready=hold_duration >= constants.EXIT_HOLD_SECONDS,
            exit_progress=progress,
        )

    def _detect_scroll_direction(self, landmarks: LandmarkMap) -> int:
        """Detect two-finger vertical scrolling with index and middle fingers."""
        index_extended = self._is_finger_extended(
            landmarks,
            self.INDEX_TIP,
            self.INDEX_MCP,
        )
        middle_extended = self._is_finger_extended(
            landmarks,
            self.MIDDLE_TIP,
            self.MIDDLE_MCP,
        )
        ring_extended = self._is_finger_extended(
            landmarks,
            self.RING_TIP,
            self.RING_MCP,
        )
        pinky_extended = self._is_finger_extended(
            landmarks,
            self.PINKY_TIP,
            self.PINKY_MCP,
        )

        if not (index_extended and middle_extended) or ring_extended or pinky_extended:
            return 0

        index_y = landmarks[self.INDEX_TIP].y
        middle_y = landmarks[self.MIDDLE_TIP].y
        vertical_delta = middle_y - index_y

        if vertical_delta > constants.SCROLL_DISTANCE_THRESHOLD:
            return 1
        if vertical_delta < -constants.SCROLL_DISTANCE_THRESHOLD:
            return -1
        return 0

    def _is_fist(self, landmarks: LandmarkMap) -> bool:
        """Return True when all finger tips are close to the wrist."""
        wrist = landmarks[self.WRIST]
        tip_ids = [
            self.INDEX_TIP,
            self.MIDDLE_TIP,
            self.RING_TIP,
            self.PINKY_TIP,
        ]
        return all(
            euclidean_distance(landmarks[tip_id], wrist)
            < constants.FIST_FINGER_TIP_TO_WRIST_THRESHOLD
            for tip_id in tip_ids
        )

    @staticmethod
    def _is_finger_extended(
        landmarks: LandmarkMap,
        tip_id: int,
        base_id: int,
    ) -> bool:
        """Return True when a fingertip is above its base in image coordinates."""
        return landmarks[tip_id].y < landmarks[base_id].y

    @staticmethod
    def _has_required_landmarks(landmarks: LandmarkMap) -> bool:
        """Check that all MediaPipe hand landmarks are present."""
        return all(index in landmarks for index in range(21))
