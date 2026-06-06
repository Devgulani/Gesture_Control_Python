"""Media playback control using hand gestures."""

from __future__ import annotations

import logging
import time

import pyautogui

from configs import constants
from controllers.base_controller import BaseController, OverlayData
from gestures.gesture_detector import GestureResult, GestureName
from trackers.hand_tracker import LandmarkMap


class MediaController(BaseController):
    """Controls media playback: play/pause, next track, previous track."""

    def __init__(self) -> None:
        """Initialize media controller state."""
        super().__init__()
        self._last_action_at: float = 0.0
        self._last_action_name: str = ""

    def handle_gesture(
        self,
        gesture: GestureResult,
        landmarks: LandmarkMap,
    ) -> None:
        """Execute media actions based on the detected gesture."""
        now = time.perf_counter()
        if now - self._last_action_at < constants.MEDIA_COOLDOWN_SECONDS:
            self.status.message = f"Media: {self._last_action_name}"
            return

        if not landmarks:
            self.status.message = "No hand detected"
            return

        if gesture.name == GestureName.OPEN_HAND:
            self._play_pause(now)
        elif gesture.name == GestureName.SWIPE_RIGHT:
            self._next_track(now)
        elif gesture.name == GestureName.SWIPE_LEFT:
            self._previous_track(now)

    def get_overlay_data(self) -> OverlayData:
        """Return media action overlay data."""
        return OverlayData(
            message=self.status.message,
            mode_status="Media Mode",
            extra_lines=[
                (f"Media: {self._last_action_name}", constants.OVERLAY_ACCENT_COLOR),
            ],
        )

    def _play_pause(self, now: float) -> None:
        """Toggle play/pause."""
        pyautogui.press("playpause")
        self._last_action_at = now
        self._last_action_name = "Play/Pause"
        self.status.message = "Media: Play/Pause"
        logging.info("Media: Play/Pause")

    def _next_track(self, now: float) -> None:
        """Skip to next track."""
        pyautogui.press("nexttrack")
        self._last_action_at = now
        self._last_action_name = "Next Track"
        self.status.message = "Media: Next Track"
        logging.info("Media: Next Track")

    def _previous_track(self, now: float) -> None:
        """Go to previous track."""
        pyautogui.press("prevtrack")
        self._last_action_at = now
        self._last_action_name = "Previous Track"
        self.status.message = "Media: Previous Track"
        logging.info("Media: Previous Track")
