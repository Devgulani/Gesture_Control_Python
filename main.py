"""GestureOS application entry point."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from ai.bridge import AiGestureBridge
from configs import constants
from gestures.gesture_detector import GestureDetector
from modes.mode_manager import ModeManager
from profiles.profile_manager import ProfileManager
from trackers.hand_tracker import HandTracker, LandmarkMap
from utils.helpers import FPSCounter, draw_status_panel


@dataclass
class ApplicationState:
    """Runtime status shown in the OpenCV overlay."""

    running: bool = True
    system_status: str = "Initializing"
    frame_processing_ms: float = 0.0
    detection_confidence: Optional[float] = None


class GestureOSApplication:
    """Coordinates camera tracking, gesture recognition, control, and rendering."""

    def __init__(self) -> None:
        """Create application modules and runtime state."""
        self._state = ApplicationState()
        self._tracker = HandTracker()
        self._detector = GestureDetector()
        self._mode_manager = ModeManager()
        self._fps_counter = FPSCounter()
        self._profile_manager = ProfileManager()
        self._ai_bridge = AiGestureBridge()

    def run(self) -> None:
        """Start GestureOS and process webcam frames until exit."""
        try:
            self._tracker.start()
            self._profile_manager.active
            self._ai_bridge.start()
            self._state.system_status = "Ready"

            while self._state.running:
                frame_started_at = time.perf_counter()
                frame = self._tracker.read_frame()
                if frame is None:
                    self._state.system_status = "Camera frame unavailable"
                    continue

                landmarks, results = self._tracker.process_frame(frame)
                gesture = self._detector.detect(landmarks)

                self._ai_bridge.process_landmarks(landmarks)
                self._mode_manager.handle_gesture(gesture, landmarks)
                self._tracker.draw_landmarks(frame, results)
                fps = self._fps_counter.update()
                self._state.detection_confidence = self._extract_confidence(results)

                now = time.perf_counter()
                if self._mode_manager.exit_requested:
                    self._state.system_status = "Exit gesture confirmed"
                    self._state.running = False
                elif not landmarks:
                    self._state.system_status = "Waiting for hand"
                elif gesture.exit_progress > 0:
                    progress_val = gesture.exit_progress
                    hold_target = constants.EXIT_HOLD_SECONDS
                    elapsed = progress_val * hold_target
                    self._state.system_status = (
                        f"Exit Gesture Detected — Holding {elapsed:.1f} / {hold_target:.0f}s"
                    )
                else:
                    self._state.system_status = (
                        self._mode_manager.active_controller.status.message
                    )

                self._state.frame_processing_ms = (
                    time.perf_counter() - frame_started_at
                ) * 1000
                self._render_overlay(frame, fps, landmarks, gesture.name.value)
                self._render_volume_bar(frame)
                cv2.imshow(constants.WINDOW_NAME, frame)

                if cv2.waitKey(1) & 0xFF == constants.EXIT_KEY:
                    self._state.system_status = "Keyboard exit requested"
                    self._state.running = False

        except KeyboardInterrupt:
            logging.info("Application interrupted by user")
        except Exception:
            logging.exception("GestureOS stopped due to an unexpected error")
            raise
        finally:
            self._shutdown()

    def _render_overlay(
        self,
        frame: np.ndarray,
        fps: float,
        landmarks: LandmarkMap,
        gesture_name: str,
    ) -> None:
        """Render application status on the OpenCV frame."""
        hand_status = "Detected" if landmarks else "Not detected"
        width, height = self._tracker.camera_resolution
        confidence = (
            f"{self._state.detection_confidence:.2f}"
            if self._state.detection_confidence is not None
            else "n/a"
        )

        mode_data = self._mode_manager.get_overlay_data()
        rows = [
            (f"{constants.APP_NAME} | FPS: {fps:.1f}", constants.OVERLAY_ACCENT_COLOR),
            (
                f"Frame: {self._state.frame_processing_ms:.1f} ms | "
                f"Camera: {width}x{height}",
                constants.OVERLAY_TEXT_COLOR,
            ),
            (f"Hand: {hand_status}", constants.OVERLAY_TEXT_COLOR),
            (f"Detection Confidence: {confidence}", constants.OVERLAY_TEXT_COLOR),
        ]
        rows.extend(mode_data.extra_lines)

        lock_parts = []
        mm = self._mode_manager
        if mm.state_lock_label:
            lock_parts.append(f"Lock: {mm.state_lock_label}")
        cooldown = mm.mode_switch_cooldown_remaining
        if cooldown > 0:
            lock_parts.append(f"Cooldown: {cooldown:.1f}s")
        if lock_parts:
            rows.append(
                (" | ".join(lock_parts), constants.OVERLAY_WARNING_COLOR),
            )

        rows.append(
            (f"Status: {self._state.system_status}", constants.OVERLAY_WARNING_COLOR),
        )
        rows.append(
            ("Press Q or hold a closed fist for 2s to exit",
             constants.OVERLAY_TEXT_COLOR),
        )
        draw_status_panel(frame, rows)

    def _render_volume_bar(self, frame: np.ndarray) -> None:
        """Render a volume bar overlay when Volume Mode is active."""
        if self._mode_manager.active_mode != ModeManager.MODE_VOLUME:
            return

        from controllers.volume_controller import VolumeController
        volume_ctrl: VolumeController = self._mode_manager.active_controller  # type: ignore[assignment]
        volume = volume_ctrl.current_volume
        normalized = volume_ctrl.smoothed_normalized_distance

        x = constants.VOLUME_BAR_X
        y = constants.VOLUME_BAR_Y
        bar_w = constants.VOLUME_BAR_WIDTH
        bar_h = constants.VOLUME_BAR_HEIGHT

        cv2.rectangle(frame, (x, y), (x + bar_w, y + bar_h),
                      constants.VOLUME_BAR_BG_COLOR, thickness=-1)
        fill_w = int(bar_w * normalized)
        cv2.rectangle(frame, (x, y), (x + fill_w, y + bar_h),
                      constants.VOLUME_BAR_COLOR, thickness=-1)
        cv2.putText(
            frame,
            f"Volume: {volume}%",
            (x, y - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            constants.OVERLAY_FONT_SCALE,
            constants.OVERLAY_TEXT_COLOR,
            constants.OVERLAY_FONT_THICKNESS,
            cv2.LINE_AA,
        )

    @staticmethod
    def _extract_confidence(results: object) -> Optional[float]:
        """Return the top hand detection confidence when MediaPipe provides it."""
        handedness = getattr(results, "handedness", None)
        if not handedness or not handedness[0]:
            return None
        score = getattr(handedness[0][0], "score", None)
        return float(score) if score is not None else None

    def _shutdown(self) -> None:
        """Release resources and close OpenCV windows."""
        self._ai_bridge.stop()
        self._tracker.release()
        cv2.destroyAllWindows()
        logging.info("GestureOS shutdown complete")


def configure_logging() -> None:
    """Configure lightweight console logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    """Run the GestureOS application."""
    configure_logging()
    GestureOSApplication().run()


if __name__ == "__main__":
    main()
