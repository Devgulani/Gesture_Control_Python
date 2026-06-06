"""Abstract base controller for GestureOS."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple

from gestures.gesture_detector import GestureResult
from trackers.hand_tracker import LandmarkMap


@dataclass
class ControllerStatus:
    """Human-readable action state for the OpenCV overlay."""

    message: str = "Ready"
    mouse_mode: str = "Idle"


@dataclass
class OverlayData:
    """Structured diagnostics data for overlay rendering."""

    message: str = ""
    mode_status: str = ""
    extra_lines: List[Tuple[str, Tuple[int, int, int]]] = field(default_factory=list)


class BaseController(ABC):
    """Common interface shared by all mode controllers."""

    def __init__(self) -> None:
        self.status = ControllerStatus()

    @abstractmethod
    def handle_gesture(
        self,
        gesture: GestureResult,
        landmarks: LandmarkMap,
    ) -> None:
        """Process a classified gesture and execute the corresponding action."""
        ...

    def get_overlay_data(self) -> OverlayData:
        """Return structured overlay data for the current frame."""
        return OverlayData(
            message=self.status.message,
            extra_lines=[],
        )
