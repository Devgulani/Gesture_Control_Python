"""MediaPipe-based hand tracking for GestureOS."""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

from configs import constants
from utils.helpers import Point


LandmarkMap = Dict[int, Point]


class HandTracker:
    """Owns webcam capture, MediaPipe processing, and landmark visualization."""

    def __init__(self) -> None:
        """Initialize MediaPipe Hands and drawing utilities."""
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=constants.MAX_NUM_HANDS,
            model_complexity=constants.MODEL_COMPLEXITY,
            min_detection_confidence=constants.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=constants.MIN_TRACKING_CONFIDENCE,
        )
        self._drawing = mp.solutions.drawing_utils
        self._drawing_styles = mp.solutions.drawing_styles
        self._hand_connections = mp.solutions.hands.HAND_CONNECTIONS
        self._capture: Optional[cv2.VideoCapture] = None

    def start(self) -> None:
        """Open the configured webcam and apply preferred frame dimensions."""
        self._capture = cv2.VideoCapture(constants.CAMERA_INDEX)
        if not self._capture.isOpened():
            raise RuntimeError("Unable to open webcam. Check camera permissions.")

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, constants.CAMERA_WIDTH)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, constants.CAMERA_HEIGHT)
        logging.info("Webcam initialized")

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the webcam, returning None if capture fails."""
        if self._capture is None:
            raise RuntimeError("HandTracker.start() must be called before reading.")

        success, frame = self._capture.read()
        if not success:
            logging.warning("Failed to read frame from webcam")
            return None

        if constants.FRAME_FLIP_HORIZONTAL:
            frame = cv2.flip(frame, 1)
        return frame

    def process_frame(
        self,
        frame: np.ndarray,
    ) -> Tuple[LandmarkMap, Optional[object]]:
        """Detect one hand and return landmark points plus raw MediaPipe results."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb_frame)

        if not results.multi_hand_landmarks:
            return {}, results

        hand_landmarks = results.multi_hand_landmarks[0]
        frame_height, frame_width = frame.shape[:2]
        landmarks: LandmarkMap = {}

        for index, landmark in enumerate(hand_landmarks.landmark):
            pixel_x = int(landmark.x * frame_width)
            pixel_y = int(landmark.y * frame_height)
            landmarks[index] = Point(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                pixel_x=pixel_x,
                pixel_y=pixel_y,
            )

        return landmarks, results

    def draw_landmarks(self, frame: np.ndarray, results: object) -> None:
        """Draw hand landmarks and connections on the frame if available."""
        multi_hand_landmarks = getattr(results, "multi_hand_landmarks", None)
        if not multi_hand_landmarks:
            return

        for hand_landmarks in multi_hand_landmarks:
            self._drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self._hand_connections,
                self._drawing_styles.get_default_hand_landmarks_style(),
                self._drawing_styles.get_default_hand_connections_style(),
            )

    def release(self) -> None:
        """Release MediaPipe and webcam resources."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._hands.close()
        logging.info("Hand tracking resources released")
