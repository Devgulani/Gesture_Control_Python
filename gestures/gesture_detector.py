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
    """Supported gesture labels."""

    NONE = "No Hand"
    MOVE = "Move Cursor"
    LEFT_CLICK = "Left Click Pinch"
    RIGHT_CLICK = "Right Click Pinch"
    SCROLL_UP = "Scroll Up"
    SCROLL_DOWN = "Scroll Down"
    EXIT_HOLD = "Exit Hold"
    OPEN_HAND = "Open Hand"
    OPEN_HAND_HELD = "Open Hand Held"
    PEACE_SIGN = "Peace Sign"
    PEACE_HELD = "Peace Sign Held"
    THREE_FINGER_PINCH = "Three Finger Pinch"
    SCREENSHOT_READY = "Screenshot Ready"
    SWIPE_RIGHT = "Swipe Right"
    SWIPE_LEFT = "Swipe Left"


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
    hold_progress: float = 0.0


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
        self._open_hand_started_at: Optional[float] = None
        self._peace_sign_started_at: Optional[float] = None
        self._three_finger_pinch_started_at: Optional[float] = None
        self._prev_wrist_x: Optional[float] = None
        self._last_swipe_at: float = 0.0

    def detect(self, landmarks: LandmarkMap) -> GestureResult:
        """Classify the current hand pose."""
        if not self._has_required_landmarks(landmarks):
            self._reset_hold_timers()
            return GestureResult(name=GestureName.NONE)

        if self._is_fist(landmarks):
            if self._fist_started_at is None:
                self._fist_started_at = time.perf_counter()
            self._reset_hold_timers()
            return self._detect_exit_hold()

        if self._fist_started_at is not None:
            now = time.perf_counter()
            if now - self._fist_started_at < constants.FIST_HOLD_JITTER_THRESHOLD:
                return self._detect_exit_hold()
            self._fist_started_at = None

        if self._is_three_finger_pinch(landmarks):
            self._reset_hold_timers(keep_three_finger=True)
            return self._detect_three_finger_pinch_hold()

        self._three_finger_pinch_started_at = None

        if self._is_open_hand(landmarks):
            self._reset_hold_timers(keep_open_hand=True)
            return self._detect_open_hand_hold()

        self._open_hand_started_at = None

        if self._is_peace_sign(landmarks):
            self._reset_hold_timers(keep_peace=True)
            return self._detect_peace_sign_hold()

        self._peace_sign_started_at = None

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
            self._reset_hold_timers()
            return GestureResult(
                name=GestureName.RIGHT_CLICK,
                is_right_pinch=True,
            )

        if is_left_pinch:
            self._reset_hold_timers()
            return GestureResult(
                name=GestureName.LEFT_CLICK,
                is_left_pinch=True,
            )

        scroll_direction = self._detect_scroll_direction(landmarks)
        if scroll_direction > 0:
            self._reset_hold_timers()
            return GestureResult(
                name=GestureName.SCROLL_UP,
                is_scrolling=True,
                scroll_direction=scroll_direction,
            )
        if scroll_direction < 0:
            self._reset_hold_timers()
            return GestureResult(
                name=GestureName.SCROLL_DOWN,
                is_scrolling=True,
                scroll_direction=scroll_direction,
            )

        swipe_direction = self._detect_swipe(landmarks)
        if swipe_direction > 0:
            self._reset_hold_timers()
            return GestureResult(name=GestureName.SWIPE_RIGHT)
        if swipe_direction < 0:
            self._reset_hold_timers()
            return GestureResult(name=GestureName.SWIPE_LEFT)

        self._reset_hold_timers()
        return GestureResult(name=GestureName.MOVE)

    def _detect_exit_hold(self) -> GestureResult:
        """Return exit progress while a closed fist is held."""
        if self._fist_started_at is None:
            self._fist_started_at = time.perf_counter()

        hold_duration = time.perf_counter() - self._fist_started_at
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
        """Return True when all fingers are fully curled into a fist.

        Uses a dual check:
        1. Finger-fold: each fingertip is below its MCP (curled down).
        2. Distance: each fingertip is close to the wrist.
        """
        fold_pairs = [
            (self.INDEX_TIP, self.INDEX_MCP),
            (self.MIDDLE_TIP, self.MIDDLE_MCP),
            (self.RING_TIP, self.RING_MCP),
            (self.PINKY_TIP, self.PINKY_MCP),
        ]
        all_folded = all(
            landmarks[tip].y > landmarks[mcp].y + constants.FIST_FINGER_FOLD_THRESHOLD
            for tip, mcp in fold_pairs
        )

        wrist = landmarks[self.WRIST]
        tip_ids = [tip for tip, _ in fold_pairs]
        all_close = all(
            euclidean_distance(landmarks[tip_id], wrist)
            < constants.FIST_FINGER_TIP_TO_WRIST_THRESHOLD
            for tip_id in tip_ids
        )

        return all_folded and all_close

    @staticmethod
    def _is_finger_extended(
        landmarks: LandmarkMap,
        tip_id: int,
        base_id: int,
    ) -> bool:
        """Return True when a fingertip is above its base in image coordinates."""
        return landmarks[tip_id].y < landmarks[base_id].y

    def _detect_open_hand_hold(self) -> GestureResult:
        """Return open hand progress while held."""
        if self._open_hand_started_at is None:
            self._open_hand_started_at = time.perf_counter()

        hold_duration = time.perf_counter() - self._open_hand_started_at
        progress = min(hold_duration / constants.MODE_SWITCH_HOLD_SECONDS, 1.0)
        is_held = hold_duration >= constants.MODE_SWITCH_HOLD_SECONDS
        return GestureResult(
            name=GestureName.OPEN_HAND_HELD if is_held else GestureName.OPEN_HAND,
            hold_progress=progress,
        )

    def _detect_peace_sign_hold(self) -> GestureResult:
        """Return peace sign progress while held."""
        if self._peace_sign_started_at is None:
            self._peace_sign_started_at = time.perf_counter()

        hold_duration = time.perf_counter() - self._peace_sign_started_at
        progress = min(hold_duration / constants.MODE_SWITCH_HOLD_SECONDS, 1.0)
        is_held = hold_duration >= constants.MODE_SWITCH_HOLD_SECONDS
        return GestureResult(
            name=GestureName.PEACE_HELD if is_held else GestureName.PEACE_SIGN,
            hold_progress=progress,
        )

    def _detect_three_finger_pinch_hold(self) -> GestureResult:
        """Return screenshot progress while three-finger pinch is held."""
        now = time.perf_counter()
        if self._three_finger_pinch_started_at is None:
            self._three_finger_pinch_started_at = now

        hold_duration = now - self._three_finger_pinch_started_at
        progress = min(hold_duration / constants.SCREENSHOT_HOLD_SECONDS, 1.0)
        is_ready = hold_duration >= constants.SCREENSHOT_HOLD_SECONDS
        return GestureResult(
            name=GestureName.SCREENSHOT_READY if is_ready else GestureName.THREE_FINGER_PINCH,
            hold_progress=progress,
        )

    def _is_open_hand(self, landmarks: LandmarkMap) -> bool:
        """Return True when all five fingers are extended (palm open)."""
        wrist = landmarks[self.WRIST]
        tip_ids = [
            self.THUMB_TIP,
            self.INDEX_TIP,
            self.MIDDLE_TIP,
            self.RING_TIP,
            self.PINKY_TIP,
        ]
        return all(
            euclidean_distance(landmarks[tip_id], wrist)
            > constants.OPEN_HAND_FINGER_TIP_TO_WRIST_THRESHOLD
            for tip_id in tip_ids
        )

    def _is_peace_sign(self, landmarks: LandmarkMap) -> bool:
        """Return True when index and middle are extended, ring and pinky are curled."""
        index_extended = self._is_finger_extended(
            landmarks, self.INDEX_TIP, self.INDEX_MCP,
        )
        middle_extended = self._is_finger_extended(
            landmarks, self.MIDDLE_TIP, self.MIDDLE_MCP,
        )
        ring_curled = not self._is_finger_extended(
            landmarks, self.RING_TIP, self.RING_MCP,
        )
        pinky_curled = not self._is_finger_extended(
            landmarks, self.PINKY_TIP, self.PINKY_MCP,
        )
        if not (index_extended and middle_extended and ring_curled and pinky_curled):
            return False

        index_y = landmarks[self.INDEX_TIP].y
        middle_y = landmarks[self.MIDDLE_TIP].y
        vertical_delta = middle_y - index_y
        return abs(vertical_delta) < constants.SCROLL_DISTANCE_THRESHOLD

    def _is_three_finger_pinch(self, landmarks: LandmarkMap) -> bool:
        """Return True when thumb, index, and middle tips are all close together."""
        thumb_index = euclidean_distance(
            landmarks[self.THUMB_TIP], landmarks[self.INDEX_TIP],
        )
        thumb_middle = euclidean_distance(
            landmarks[self.THUMB_TIP], landmarks[self.MIDDLE_TIP],
        )
        index_middle = euclidean_distance(
            landmarks[self.INDEX_TIP], landmarks[self.MIDDLE_TIP],
        )
        threshold = constants.THREE_FINGER_PINCH_THRESHOLD
        return (
            thumb_index < threshold
            and thumb_middle < threshold
            and index_middle < threshold
        )

    def _detect_swipe(self, landmarks: LandmarkMap) -> int:
        """Detect horizontal hand swipe direction using wrist movement."""
        now = time.perf_counter()
        if now - self._last_swipe_at < constants.SWIPE_COOLDOWN_SECONDS:
            return 0

        wrist_x = landmarks[self.WRIST].x
        if self._prev_wrist_x is None:
            self._prev_wrist_x = wrist_x
            return 0

        delta = wrist_x - self._prev_wrist_x
        self._prev_wrist_x = wrist_x

        if abs(delta) > constants.SWIPE_THRESHOLD:
            self._last_swipe_at = now
            return 1 if delta > 0 else -1
        return 0

    def _reset_hold_timers(
        self,
        keep_fist: bool = False,
        keep_open_hand: bool = False,
        keep_peace: bool = False,
        keep_three_finger: bool = False,
    ) -> None:
        """Reset hold timers that are not being kept for the current detection."""
        if not keep_fist:
            self._fist_started_at = None
        if not keep_open_hand:
            self._open_hand_started_at = None
        if not keep_peace:
            self._peace_sign_started_at = None
        if not keep_three_finger:
            self._three_finger_pinch_started_at = None
        if not (keep_fist or keep_open_hand or keep_peace or keep_three_finger):
            self._prev_wrist_x = None

    @staticmethod
    def _has_required_landmarks(landmarks: LandmarkMap) -> bool:
        """Check that all MediaPipe hand landmarks are present."""
        return all(index in landmarks for index in range(21))
