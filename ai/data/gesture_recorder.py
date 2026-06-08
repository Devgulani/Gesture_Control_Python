"""Standalone gesture-recording tool with OpenCV preview.

Opens the webcam, performs hand tracking, and allows the user to
save the current feature vector under a gesture label with a key press.

Each recorded sample includes:
    - 61-element feature vector
    - Raw landmarks (21×3 array)
    - Session ID (auto-generated UUID4 per session)
    - Profile ID (from the active ProfileManager profile)
    - Timestamp (ISO-8601 UTC)

Key bindings::

    0-9     — Select gesture label
    SPACE   — Record current frame
    R       — Toggle continuous recording
    U       — Undo last recording
    S       — Show dataset summary
    Q       — Quit
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, Optional

import cv2
import numpy as np

from ai.data.dataset_storage import DatasetStorage
from ai.features.extractor import FeatureExtractor
from configs import ai_config
from profiles.profile_manager import ProfileManager
from trackers.hand_tracker import HandTracker, LandmarkMap

logger = logging.getLogger(__name__)

# Keyboard mapping: scancode -> gesture-pose label
_LABEL_MAP: Dict[int, str] = ai_config.RECORDER_LABEL_MAP

# Gesture colours for overlay (BGR)
_LABEL_COLORS: Dict[str, tuple[int, int, int]] = {
    "NO_HAND": (128, 128, 128),
    "POINTING": (0, 255, 0),
    "PINCH_INDEX": (255, 0, 0),
    "PINCH_MIDDLE": (0, 0, 255),
    "TWO_FINGER_UP": (255, 255, 0),
    "OPEN_HAND": (0, 255, 255),
    "FIST": (0, 0, 255),
    "THREE_FINGER_PINCH": (255, 128, 0),
    "PINCH_PINKY": (255, 0, 128),
    "PEACE": (0, 128, 255),
}


class GestureRecorder:
    """Interactive gesture recording tool.

    Each recording session generates a unique session ID. Samples are
    tagged with the session ID and the active profile name from
    ProfileManager.

    Key bindings::

        0-9     — Select gesture label
        SPACE   — Record current frame
        R       — Toggle continuous recording
        U       — Undo last recording
        S       — Show dataset summary
        Q       — Quit
    """

    def __init__(self, storage: Optional[DatasetStorage] = None) -> None:
        self._storage = storage or DatasetStorage()
        self._tracker = HandTracker()
        self._extractor = FeatureExtractor()
        self._profile_manager = ProfileManager()

        self._session_id: str = uuid.uuid4().hex[:12]
        self._profile_id: str = self._profile_manager.active.profile_name

        self._current_label_key: int = ord("1")
        self._continuous: bool = False
        self._samples_this_session: int = 0
        self._last_saved_label: Optional[str] = None
        self._prev_hand_present: bool = False

        self._label_history: list[tuple[str, int]] = []

        logger.info(
            "Session %s | Profile: %s",
            self._session_id,
            self._profile_id,
        )

    @property
    def current_label(self) -> str:
        """Return the name of the currently selected gesture label."""
        return _LABEL_MAP.get(self._current_label_key, "POINTING")

    def run(self) -> None:
        """Open webcam and run the interactive recording loop."""
        logger.info("GestureRecorder starting...")
        self._tracker.start()

        cv2.namedWindow(ai_config.RECORDER_WINDOW_NAME)
        self._print_help()

        try:
            while True:
                frame = self._tracker.read_frame()
                if frame is None:
                    continue

                landmarks, results = self._tracker.process_frame(frame)
                features: Optional[np.ndarray] = None
                features_valid = False

                if landmarks:
                    features = self._extractor.extract(landmarks)
                    features_valid = features is not None
                else:
                    landmarks = {}

                self._tracker.draw_landmarks(frame, results)

                hand_present = len(landmarks) >= 21
                if self._continuous and hand_present and not self._prev_hand_present:
                    self._record_sample(features, landmarks, features_valid)
                self._prev_hand_present = hand_present

                self._render_overlay(frame, features_valid)
                cv2.imshow(ai_config.RECORDER_WINDOW_NAME, frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ai_config.RECORDER_QUIT_KEY:
                    logger.info(
                        "Recording session ended. %d samples recorded.",
                        self._samples_this_session,
                    )
                    break
                elif key == ai_config.RECORDER_RECORD_KEY:
                    self._record_sample(features, landmarks, features_valid)
                elif key == ai_config.RECORDER_TOGGLE_CONTINUOUS_KEY:
                    self._continuous = not self._continuous
                    mode = "ON" if self._continuous else "OFF"
                    logger.info("Continuous recording: %s", mode)
                elif key == ai_config.RECORDER_SUMMARY_KEY:
                    print(self._storage.summary())
                elif key == ai_config.RECORDER_UNDO_KEY:
                    self._undo_last()
                elif key in _LABEL_MAP:
                    self._current_label_key = key
                    logger.info("Label: %s", self.current_label)

        except KeyboardInterrupt:
            pass
        finally:
            self._tracker.release()
            cv2.destroyAllWindows()

        if self._samples_this_session > 0:
            print(self._storage.summary())

    def _record_sample(
        self,
        features: Optional[np.ndarray],
        landmarks: LandmarkMap,
        valid: bool,
    ) -> None:
        if not valid or features is None:
            return
        label = self.current_label
        sample_id = self._storage.save_sample(
            label=label,
            features=features,
            landmarks=landmarks,
            session_id=self._session_id,
            profile_id=self._profile_id,
        )
        self._samples_this_session += 1
        self._last_saved_label = label
        self._label_history.append((label, sample_id))
        count = self._storage.label_counts().get(label, 0)
        logger.info(
            "Saved  %s  #%d  (total %s: %d)",
            label,
            sample_id,
            label,
            count,
        )

    def _undo_last(self) -> None:
        if not self._label_history:
            return
        label, sample_id = self._label_history.pop()
        self._storage.delete_sample(label, sample_id)
        self._samples_this_session -= 1
        logger.info("Undo  %s  #%d", label, sample_id)

    def _render_overlay(self, frame: np.ndarray, valid: bool) -> None:
        h, w = frame.shape[:2]
        label_name = self.current_label
        color = _LABEL_COLORS.get(label_name, (255, 255, 255))
        counts = self._storage.label_counts()
        label_count = counts.get(label_name, 0)

        # Top bar
        cv2.rectangle(frame, (0, 0), (w, 40), (30, 30, 30), -1)
        cv2.putText(
            frame,
            f"Label: {label_name}",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Count: {label_count}  |  Session: {self._samples_this_session}",
            (280, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )

        # Hand status indicator
        hand_text = "HAND OK" if valid else "NO HAND"
        hand_color = (0, 255, 0) if valid else (0, 0, 255)
        cv2.putText(
            frame,
            hand_text,
            (w - 130, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            hand_color,
            2,
            cv2.LINE_AA,
        )

        # Continuous recording indicator
        if self._continuous:
            cv2.circle(frame, (w - 16, 20), 6, (0, 0, 255), -1)
            cv2.putText(
                frame,
                "REC",
                (w - 50, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )

        # Bottom help bar
        cv2.rectangle(frame, (0, h - 26), (w, h), (30, 30, 30), -1)
        cv2.putText(
            frame,
            "[0-9] Label  [SPACE] Save  [R] Auto  [U] Undo  [S] Stats  [Q] Quit",
            (12, h - 7),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )

    @staticmethod
    def _print_help() -> None:
        print("=" * 56)
        print("  GestureOS Gesture Recorder")
        print("=" * 56)
        print("  Keys:")
        for key, label in sorted(_LABEL_MAP.items(), key=lambda x: x[1]):
            print(f"    {chr(key)}  —  {label}")
        print(f"    SPACE  —  Save current frame")
        print(f"    R      —  Toggle continuous recording")
        print(f"    U      —  Undo last save")
        print(f"    S      —  Show dataset summary")
        print(f"    Q      —  Quit")
        print("=" * 56)
