"""GestureOS application entry point."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2

from configs import constants
from controllers.mouse_controller import MouseController
from gestures.gesture_detector import GestureDetector
from trackers.hand_tracker import HandTracker, LandmarkMap
from utils.helpers import FPSCounter, draw_status_panel


@dataclass
class ApplicationState:
    """Runtime status shown in the OpenCV overlay."""

    running: bool = True
    system_status: str = "Initializing"


class GestureOSApplication:
    """Coordinates camera tracking, gesture recognition, control, and rendering."""

    INDEX_TIP = 8

    def __init__(self) -> None:
        """Create application modules and runtime state."""
        self._state = ApplicationState()
        self._tracker = HandTracker()
        self._detector = GestureDetector()
        self._mouse_controller = MouseController()
        self._fps_counter = FPSCounter()

    def run(self) -> None:
        """Start GestureOS and process webcam frames until exit."""
        try:
            self._tracker.start()
            self._state.system_status = "Ready"

            while self._state.running:
                frame = self._tracker.read_frame()
                if frame is None:
                    self._state.system_status = "Camera frame unavailable"
                    continue

                landmarks, results = self._tracker.process_frame(frame)
                gesture = self._detector.detect(landmarks)
                index_tip = landmarks.get(self.INDEX_TIP)

                self._mouse_controller.handle_gesture(gesture, index_tip)
                self._tracker.draw_landmarks(frame, results)
                fps = self._fps_counter.update()

                if gesture.is_exit_ready:
                    self._state.system_status = "Exit gesture confirmed"
                    self._state.running = False
                elif not landmarks:
                    self._state.system_status = "Waiting for hand"
                elif gesture.exit_progress > 0:
                    percent = int(gesture.exit_progress * 100)
                    self._state.system_status = f"Hold fist to exit: {percent}%"
                else:
                    self._state.system_status = self._mouse_controller.status.message

                self._render_overlay(frame, fps, landmarks, gesture.name.value)
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
        frame,
        fps: float,
        landmarks: LandmarkMap,
        gesture_name: str,
    ) -> None:
        """Render application status on the OpenCV frame."""
        hand_status = "Detected" if landmarks else "Not detected"
        rows = [
            (f"{constants.APP_NAME} | FPS: {fps:.1f}", constants.OVERLAY_ACCENT_COLOR),
            (f"Hand: {hand_status}", constants.OVERLAY_TEXT_COLOR),
            (f"Gesture: {gesture_name}", constants.OVERLAY_TEXT_COLOR),
            (
                f"Mouse Mode: {self._mouse_controller.status.mouse_mode}",
                constants.OVERLAY_SUCCESS_COLOR,
            ),
            (f"Status: {self._state.system_status}", constants.OVERLAY_WARNING_COLOR),
            ("Press Q or hold a closed fist for 2s to exit", constants.OVERLAY_TEXT_COLOR),
        ]
        draw_status_panel(frame, rows)

    def _shutdown(self) -> None:
        """Release resources and close OpenCV windows."""
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
