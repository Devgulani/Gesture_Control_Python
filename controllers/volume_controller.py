"""Volume control using thumb-index finger distance."""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple

from configs import constants
from controllers.base_controller import BaseController, OverlayData
from gestures.gesture_detector import GestureResult, GestureName
from trackers.hand_tracker import LandmarkMap
from utils.helpers import Point, clamp, euclidean_distance


class VolumeController(BaseController):
    """Controls system volume via thumb-index finger distance."""

    THUMB_TIP = 4
    INDEX_TIP = 8

    def __init__(self) -> None:
        """Initialize volume state and connect to system audio."""
        super().__init__()
        self._audio_interface = self._init_audio_interface()
        self._current_volume: int = self._get_system_volume()
        self._smoothed_distance: float = 0.5
        self._last_adjust_at: float = 0.0
        self._volume_changed: bool = False
        self._transition_locked_until: float = 0.0

    def handle_gesture(
        self,
        gesture: GestureResult,
        landmarks: LandmarkMap,
    ) -> None:
        """Adjust volume based on thumb-index finger distance."""
        if time.perf_counter() < self._transition_locked_until:
            return

        if not landmarks:
            self.status.message = "No hand detected"
            return

        thumb_tip = landmarks.get(self.THUMB_TIP)
        index_tip = landmarks.get(self.INDEX_TIP)

        if thumb_tip is None or index_tip is None:
            self.status.message = "Hand not fully visible"
            return

        raw_distance = euclidean_distance(thumb_tip, index_tip)
        clamped_distance = clamp(
            (raw_distance - constants.VOLUME_MIN_DISTANCE)
            / (constants.VOLUME_MAX_DISTANCE - constants.VOLUME_MIN_DISTANCE),
            0.0,
            1.0,
        )

        alpha = constants.VOLUME_SMOOTHING_FACTOR
        self._smoothed_distance = (
            self._smoothed_distance
            + alpha * (clamped_distance - self._smoothed_distance)
        )

        now = time.perf_counter()
        if now - self._last_adjust_at >= constants.VOLUME_COOLDOWN_SECONDS:
            target_volume = int(self._smoothed_distance * 100)
            target_volume = clamp(target_volume, 0, 100)
            if abs(target_volume - self._current_volume) >= 1:
                self._set_volume(target_volume)
                self._current_volume = target_volume
                self._volume_changed = True
                self._last_adjust_at = now

        self.status.message = f"Volume: {self._current_volume}%"

    def get_overlay_data(self) -> OverlayData:
        """Return volume bar overlay data."""
        return OverlayData(
            message=self.status.message,
            mode_status="Volume Mode",
            extra_lines=[
                (f"Volume: {self._current_volume}%", constants.OVERLAY_SUCCESS_COLOR),
            ],
        )

    def lock_during_transition(self, duration: float) -> None:
        """Prevent volume adjustments during mode transitions."""
        self._transition_locked_until = time.perf_counter() + duration

    @property
    def current_volume(self) -> int:
        """Return the current volume percentage."""
        return self._current_volume

    @property
    def is_transition_locked(self) -> bool:
        """Return True while the volume controller is in transition lock."""
        return time.perf_counter() < self._transition_locked_until

    @property
    def smoothed_normalized_distance(self) -> float:
        """Return the smoothed normalized distance (0-1) for bar rendering."""
        return self._smoothed_distance

    def _init_audio_interface(self) -> Optional[object]:
        """Initialize the system audio interface."""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None,
            )
            return cast(interface, POINTER(IAudioEndpointVolume))
        except Exception as exc:
            logging.warning("Could not initialize pycaw: %s", exc)
            return None

    def _get_system_volume(self) -> int:
        """Read the current system volume as a percentage (0-100)."""
        if self._audio_interface is None:
            return 50
        try:
            scalar_volume = self._audio_interface.GetMasterVolumeLevelScalar()
            return int(round(scalar_volume * 100))
        except Exception:
            return 50

    def _set_volume(self, volume: int) -> None:
        """Set system volume to a percentage (0-100)."""
        if self._audio_interface is None:
            return
        try:
            scalar = clamp(volume / 100.0, 0.0, 1.0)
            self._audio_interface.SetMasterVolumeLevelScalar(scalar, None)
        except Exception as exc:
            logging.warning("Failed to set volume: %s", exc)
