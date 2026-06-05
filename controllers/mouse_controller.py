"""Mouse movement, clicking, scrolling, and cooldown handling."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Tuple

import pyautogui

from configs import constants
from gestures.gesture_detector import GestureResult
from utils.helpers import Point, clamp


@dataclass
class ControllerStatus:
    """Human-readable action state for the OpenCV overlay."""

    message: str = "Ready"
    mouse_mode: str = "Idle"


class MouseController:
    """Maps hand landmarks to mouse actions using PyAutoGUI."""

    def __init__(self) -> None:
        """Initialize screen geometry, smoothing state, and click cooldowns."""
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0
        self._screen_width, self._screen_height = pyautogui.size()
        self._smoothed_x = self._screen_width / 2
        self._smoothed_y = self._screen_height / 2
        self._last_left_click_at = 0.0
        self._last_right_click_at = 0.0
        self._last_scroll_at = 0.0
        self._left_pinch_active = False
        self._right_pinch_active = False
        self.status = ControllerStatus()

    def handle_gesture(
        self,
        gesture: GestureResult,
        index_tip: Point | None,
    ) -> None:
        """Run the OS action associated with a detected gesture."""
        if gesture.is_left_pinch:
            self._click("left")
            self.status.mouse_mode = "Click"
            return

        self._left_pinch_active = False

        if gesture.is_right_pinch:
            self._click("right")
            self.status.mouse_mode = "Context"
            return

        self._right_pinch_active = False

        if gesture.is_scrolling:
            self._scroll(gesture.scroll_direction)
            self.status.mouse_mode = "Scroll"
            return

        if index_tip is not None:
            self.move_cursor(index_tip)
            self.status.mouse_mode = "Move"
            return

        self.status.mouse_mode = "Idle"
        self.status.message = "Show one hand to begin"

    def move_cursor(self, index_tip: Point) -> None:
        """Move the cursor using smoothed index-finger coordinates."""
        target_x, target_y = self._map_to_screen(index_tip)
        delta_x = target_x - self._smoothed_x
        delta_y = target_y - self._smoothed_y

        if abs(delta_x) < constants.CURSOR_DEAD_ZONE_PX:
            target_x = self._smoothed_x
        if abs(delta_y) < constants.CURSOR_DEAD_ZONE_PX:
            target_y = self._smoothed_y

        alpha = constants.CURSOR_SMOOTHING_FACTOR
        self._smoothed_x = self._smoothed_x + alpha * (target_x - self._smoothed_x)
        self._smoothed_y = self._smoothed_y + alpha * (target_y - self._smoothed_y)

        pyautogui.moveTo(self._smoothed_x, self._smoothed_y, duration=0)
        self.status.message = "Cursor tracking index finger"

    def _click(self, button: str) -> None:
        """Perform a debounced mouse click."""
        now = time.perf_counter()
        if button == "left":
            if self._left_pinch_active:
                self.status.message = "Left pinch held"
                return
            if now - self._last_left_click_at < constants.LEFT_CLICK_COOLDOWN_SECONDS:
                self.status.message = "Left click cooling down"
                return
            pyautogui.click(button="left")
            self._left_pinch_active = True
            self._last_left_click_at = now
            self.status.message = "Left click"
            logging.info("Left click triggered")
            return

        if self._right_pinch_active:
            self.status.message = "Right pinch held"
            return
        if now - self._last_right_click_at < constants.RIGHT_CLICK_COOLDOWN_SECONDS:
            self.status.message = "Right click cooling down"
            return
        pyautogui.click(button="right")
        self._right_pinch_active = True
        self._last_right_click_at = now
        self.status.message = "Right click"
        logging.info("Right click triggered")

    def _scroll(self, direction: int) -> None:
        """Perform rate-limited vertical scrolling."""
        now = time.perf_counter()
        if now - self._last_scroll_at < constants.SCROLL_COOLDOWN_SECONDS:
            self.status.message = "Scrolling"
            return

        scroll_amount = constants.SCROLL_AMOUNT * direction
        pyautogui.scroll(scroll_amount)
        self._last_scroll_at = now
        self.status.message = "Scroll up" if direction > 0 else "Scroll down"

    def _map_to_screen(self, point: Point) -> Tuple[float, float]:
        """Map normalized camera coordinates to screen coordinates with margins."""
        margin = constants.CURSOR_BOUNDARY_MARGIN_RATIO
        usable_x = clamp((point.x - margin) / (1 - 2 * margin), 0.0, 1.0)
        usable_y = clamp((point.y - margin) / (1 - 2 * margin), 0.0, 1.0)
        return usable_x * self._screen_width, usable_y * self._screen_height
