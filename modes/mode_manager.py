"""Mode management for GestureOS.

Routes gestures to the appropriate controller and handles mode transitions.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Optional

from configs import constants
from controllers.base_controller import BaseController, OverlayData
from controllers.mouse_controller import MouseController
from controllers.volume_controller import VolumeController
from controllers.media_controller import MediaController
from controllers.screenshot_controller import ScreenshotController
from gestures.gesture_detector import GestureResult, GestureName
from trackers.hand_tracker import LandmarkMap


class ModeManager:
    """Orchestrates mode state, gesture routing, and controller lifecycle."""

    MODE_MOUSE = "mouse"
    MODE_VOLUME = "volume"
    MODE_MEDIA = "media"

    def __init__(self) -> None:
        """Initialize mode registry and set default mode."""
        self._modes: Dict[str, BaseController] = {
            self.MODE_MOUSE: MouseController(),
            self.MODE_VOLUME: VolumeController(),
            self.MODE_MEDIA: MediaController(),
        }
        self._screenshot: ScreenshotController = ScreenshotController()
        self._active_mode: str = self.MODE_MOUSE
        self.exit_requested: bool = False
        self._last_gesture_name: str = ""
        self._state_lock: Optional[str] = None
        self._lock_until: float = 0.0
        self._last_mode_switch_at: float = 0.0
        self._transition_message: str = ""
        logging.info("ModeManager initialized: default mode = %s", self._active_mode)

    @property
    def active_mode(self) -> str:
        """Return the name of the currently active mode."""
        return self._active_mode

    @property
    def active_controller(self) -> BaseController:
        """Return the currently active mode controller."""
        return self._modes[self._active_mode]

    @property
    def is_state_locked(self) -> bool:
        """Return True when the mode manager is in a temporary lock state."""
        if self._state_lock is None:
            return False
        if time.perf_counter() >= self._lock_until:
            self._state_lock = None
            return False
        return True

    @property
    def state_lock_label(self) -> str:
        """Return the current lock reason or empty string."""
        return self._state_lock if self.is_state_locked else ""

    @property
    def mode_switch_cooldown_remaining(self) -> float:
        """Return seconds remaining before another mode switch is allowed."""
        remaining = self._last_mode_switch_at + constants.MODE_SWITCH_COOLDOWN_SECONDS - time.perf_counter()
        return max(remaining, 0.0)

    def handle_gesture(
        self,
        gesture: GestureResult,
        landmarks: LandmarkMap,
    ) -> None:
        """Route a gesture to the appropriate handler.

        Priority order:
        1. Global exit gesture
        2. Global screenshot gesture
        3. Mode-switch gestures (handled here, not routed to controllers)
        4. Active mode controller
        """
        self._last_gesture_name = gesture.name.value

        if gesture.is_exit_ready:
            self.exit_requested = True
            return

        self._screenshot.handle_gesture(gesture, landmarks)

        now = time.perf_counter()

        if gesture.name in (GestureName.OPEN_HAND_HELD, GestureName.PEACE_HELD):
            if self.mode_switch_cooldown_remaining > 0:
                self._transition_message = (
                    f"Cooldown: {self.mode_switch_cooldown_remaining:.1f}s"
                )
                return
            self._transition_message = ""

        if gesture.name == GestureName.OPEN_HAND_HELD:
            if self._active_mode in (self.MODE_MOUSE, self.MODE_VOLUME):
                self._toggle_volume_mode()
                return

        if gesture.name == GestureName.PEACE_HELD:
            if self._active_mode in (self.MODE_MOUSE, self.MODE_MEDIA):
                self._toggle_media_mode()
                return

        if self.is_state_locked:
            return

        self._modes[self._active_mode].handle_gesture(gesture, landmarks)

    def get_overlay_data(self) -> OverlayData:
        """Aggregate overlay data from all relevant sources."""
        active = self._modes[self._active_mode]
        mode_data = active.get_overlay_data()

        lines = []
        lines.append(
            (f"Mode: {self._active_mode.title()}", constants.OVERLAY_ACCENT_COLOR),
        )
        lines.append(
            (f"Gesture: {self._last_gesture_name}",
             constants.OVERLAY_TEXT_COLOR),
        )
        if mode_data.mode_status:
            lines.append(
                (mode_data.mode_status, constants.OVERLAY_SUCCESS_COLOR),
            )

        if self._transition_message:
            lines.append(
                (self._transition_message, constants.OVERLAY_WARNING_COLOR),
            )

        screenshot_data = self._screenshot.get_overlay_data()
        if screenshot_data.extra_lines:
            lines.extend(screenshot_data.extra_lines)

        if mode_data.extra_lines:
            lines.extend(mode_data.extra_lines)

        return OverlayData(
            message=mode_data.message,
            extra_lines=lines,
        )

    def _lock_state(self, reason: str, duration: float) -> None:
        """Prevent lower-priority gesture processing for a duration."""
        self._state_lock = reason
        self._lock_until = time.perf_counter() + duration

    def _toggle_volume_mode(self) -> None:
        """Toggle between Mouse and Volume mode.

        Open hand held 2s toggles: Mouse → Volume → Mouse.
        In Media mode, open hand is routed to the media controller instead.
        """
        self._last_mode_switch_at = time.perf_counter()
        if self._active_mode == self.MODE_MOUSE:
            self._active_mode = self.MODE_VOLUME
            self._transition_message = "Volume Mode activated"
            self._lock_state("transition", constants.VOLUME_TRANSITION_DELAY)
            volume_ctrl = self._modes[self.MODE_VOLUME]
            if isinstance(volume_ctrl, VolumeController):
                volume_ctrl.lock_during_transition(constants.VOLUME_TRANSITION_DELAY)
            logging.info("Switched to Volume mode")
        elif self._active_mode == self.MODE_VOLUME:
            self._active_mode = self.MODE_MOUSE
            self._transition_message = "Mouse Mode activated"
            self._lock_state("transition", constants.VOLUME_TRANSITION_DELAY)
            volume_ctrl = self._modes[self.MODE_VOLUME]
            if isinstance(volume_ctrl, VolumeController):
                volume_ctrl.lock_during_transition(constants.VOLUME_TRANSITION_DELAY)
            logging.info("Switched to Mouse mode")

    def _toggle_media_mode(self) -> None:
        """Toggle between Mouse and Media mode.

        Peace sign held 2s toggles: Mouse → Media → Mouse.
        In Volume mode, peace sign is routed to the volume controller instead.
        """
        self._last_mode_switch_at = time.perf_counter()
        if self._active_mode == self.MODE_MOUSE:
            self._active_mode = self.MODE_MEDIA
            self._transition_message = "Media Mode activated"
            self._lock_state("transition", constants.VOLUME_TRANSITION_DELAY)
            logging.info("Switched to Media mode")
        elif self._active_mode == self.MODE_MEDIA:
            self._active_mode = self.MODE_MOUSE
            self._transition_message = "Mouse Mode activated"
            self._lock_state("transition", constants.VOLUME_TRANSITION_DELAY)
            logging.info("Switched to Mouse mode")
