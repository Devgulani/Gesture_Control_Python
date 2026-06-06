"""Screenshot capture via three-finger pinch gesture."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

import pyautogui

from configs import constants
from controllers.base_controller import BaseController, OverlayData
from gestures.gesture_detector import GestureResult, GestureName
from trackers.hand_tracker import LandmarkMap


class ScreenshotController(BaseController):
    """Captures screenshots when three-finger pinch is detected."""

    def __init__(self) -> None:
        """Initialize screenshot controller state."""
        super().__init__()
        self._last_screenshot_at: float = 0.0
        self._last_filename: str = ""
        self._screenshot_taken: bool = False
        self._screenshot_display_timer: float = 0.0
        self._ensure_screenshots_dir()

    def handle_gesture(
        self,
        gesture: GestureResult,
        landmarks: LandmarkMap,
    ) -> None:
        """Capture a screenshot when the gesture is ready."""
        now = time.perf_counter()

        if self._screenshot_taken:
            if now - self._screenshot_display_timer > 2.0:
                self._screenshot_taken = False
            else:
                self.status.message = f"Screenshot saved: {self._last_filename}"
            return

        if gesture.name == GestureName.SCREENSHOT_READY:
            if now - self._last_screenshot_at < constants.SCREENSHOT_COOLDOWN_SECONDS:
                self.status.message = "Screenshot cooling down"
                return
            self._capture(now)
            self._screenshot_taken = True
            self._screenshot_display_timer = now

    def get_overlay_data(self) -> OverlayData:
        """Return screenshot confirmation overlay data."""
        extra_lines = []
        if self._screenshot_taken:
            extra_lines.append(
                (f"Screenshot: {self._last_filename}", constants.OVERLAY_SUCCESS_COLOR),
            )
        return OverlayData(
            message=self.status.message,
            extra_lines=extra_lines,
        )

    def _ensure_screenshots_dir(self) -> None:
        """Create the screenshots directory if it does not exist."""
        constants.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def _capture(self, now: float) -> None:
        """Capture the screen and save to the screenshots directory."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = constants.SCREENSHOTS_DIR / filename

            screenshot = pyautogui.screenshot()
            screenshot.save(str(filepath))

            self._last_screenshot_at = now
            self._last_filename = filename
            self.status.message = f"Screenshot saved: {filename}"
            logging.info("Screenshot saved: %s", filepath)
        except Exception as exc:
            self.status.message = "Screenshot failed"
            logging.error("Screenshot failed: %s", exc)
