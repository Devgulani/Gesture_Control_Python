"""MediaPipe-based hand tracking for GestureOS."""

from __future__ import annotations

import logging
import time
from typing import Dict, Optional, Tuple

import cv2
from mediapipe import Image, ImageFormat
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
import numpy as np

from configs import constants
from utils.helpers import Point


LandmarkMap = Dict[int, Point]


class HandTracker:
    """Owns webcam capture, MediaPipe processing, and landmark visualization."""

    def __init__(self) -> None:
        """Initialize MediaPipe Tasks hand landmarker and drawing utilities."""
        self._landmarker = self._create_landmarker()
        self._drawing = vision.drawing_utils
        self._drawing_styles = vision.drawing_styles
        self._hand_connections = (
            vision.HandLandmarksConnections.HAND_CONNECTIONS
        )
        self._capture: Optional[cv2.VideoCapture] = None
        self._last_timestamp_ms = 0

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
        media_pipe_image = Image(
            image_format=ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb_frame),
        )
        results = self._landmarker.detect_for_video(
            media_pipe_image,
            self._next_timestamp_ms(),
        )

        if not results.hand_landmarks:
            return {}, results

        hand_landmarks = results.hand_landmarks[0]
        frame_height, frame_width = frame.shape[:2]
        landmarks: LandmarkMap = {}

        for index, landmark in enumerate(hand_landmarks):
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
        hand_landmarks_list = getattr(results, "hand_landmarks", None)
        if not hand_landmarks_list:
            return

        for hand_landmarks in hand_landmarks_list:
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
        self._landmarker.close()
        logging.info("Hand tracking resources released")

    def _create_landmarker(self) -> vision.HandLandmarker:
        """Create a MediaPipe Tasks hand landmarker for video frames."""
        model_path = constants.HAND_LANDMARKER_MODEL_PATH
        if not model_path.exists():
            raise FileNotFoundError(
                "MediaPipe hand landmarker model not found at "
                f"{model_path}. Download hand_landmarker.task into "
                "assets/models before starting GestureOS."
            )

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=constants.MAX_NUM_HANDS,
            min_hand_detection_confidence=(
                constants.MIN_DETECTION_CONFIDENCE
            ),
            min_hand_presence_confidence=(
                constants.MIN_HAND_PRESENCE_CONFIDENCE
            ),
            min_tracking_confidence=constants.MIN_TRACKING_CONFIDENCE,
        )
        return vision.HandLandmarker.create_from_options(options)

    def _next_timestamp_ms(self) -> int:
        """Return a strictly increasing timestamp for video-mode inference."""
        timestamp_ms = int(time.perf_counter() * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms
        return timestamp_ms
