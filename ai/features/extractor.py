"""Feature extraction from hand landmarks.

Transforms raw MediaPipe landmark coordinates into a fixed-length
feature vector suitable for machine learning classification.

Feature groups (Phase 1B):
    A —  40  Wrist-relative x,y coordinates (landmarks 1-20 / hand_size)
    B —  10  Fingertip pairwise distances (C(5,2), normalised by hand_size)
    C —   5  Finger extension deltas (tip.y - mcp.y)
    D —   5  Finger bend angle cosines (2D dot product, no z)
    E —   1  Hand size (wrist-to-middle-MCP distance)
          --
          61  Total

Design goals:
    - No absolute screen position (eliminates overfitting vector).
    - No z-coordinates (eliminates camera-distance noise).
    - No redundant features (all 61 are independent).
    - Explicit gesture-relevant signals (distances, angles, deltas).
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from configs import ai_config
from trackers.hand_tracker import LandmarkMap
from utils.helpers import Point, euclidean_distance


class FeatureExtractor:
    """Extracts a 61-element feature vector from MediaPipe hand landmarks.

    The output vector layout is documented in the module docstring.
    The public ``extract()`` method is the only entry point.
    """

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_TIP = 20

    def __init__(self) -> None:
        """Pre-allocate a zero feature vector for reuse."""
        self._feature_count = ai_config.FEATURE_COUNT
        self._features: np.ndarray = np.zeros(self._feature_count, dtype=np.float32)

    @property
    def feature_count(self) -> int:
        """Return the fixed length of the feature vector."""
        return self._feature_count

    def extract(self, landmarks: LandmarkMap) -> Optional[np.ndarray]:
        """Build a feature vector from the given hand landmarks.

        Args:
            landmarks: Map of landmark index -> Point (from HandTracker).

        Returns:
            A 1-D float32 NumPy array of length ``feature_count``,
            or None when fewer than 21 landmarks are available.
        """
        if len(landmarks) < 21:
            return None

        self._features.fill(0.0)

        wrist = landmarks[self.WRIST]
        middle_mcp = landmarks[self.MIDDLE_MCP]
        hand_size = euclidean_distance(wrist, middle_mcp)
        if hand_size < 1e-6:
            return None

        offset = self._build_wrist_relative(landmarks, wrist, hand_size, 0)
        offset = self._build_pairwise_distances(landmarks, hand_size, offset)
        offset = self._build_extension_deltas(landmarks, offset)
        offset = self._build_bend_angles(landmarks, offset)
        self._features[offset] = hand_size

        return self._features.copy()

    def _build_wrist_relative(
        self,
        landmarks: LandmarkMap,
        wrist: Point,
        hand_size: float,
        start: int,
    ) -> int:
        """Group A: wrist-relative x,y for landmarks 1-20."""
        inv_size = 1.0 / hand_size
        idx = start
        for i in range(1, 21):
            pt = landmarks[i]
            self._features[idx] = (pt.x - wrist.x) * inv_size
            self._features[idx + 1] = (pt.y - wrist.y) * inv_size
            idx += 2
        return idx

    def _build_pairwise_distances(
        self,
        landmarks: LandmarkMap,
        hand_size: float,
        start: int,
    ) -> int:
        """Group B: all C(5,2) fingertip distances normalised by hand_size."""
        tips = [
            landmarks[self.THUMB_TIP],
            landmarks[self.INDEX_TIP],
            landmarks[self.MIDDLE_TIP],
            landmarks[self.RING_TIP],
            landmarks[self.PINKY_TIP],
        ]
        inv_size = 1.0 / hand_size
        idx = start
        for i in range(5):
            for j in range(i + 1, 5):
                distance = euclidean_distance(tips[i], tips[j])
                self._features[idx] = distance * inv_size
                idx += 1
        return idx

    def _build_extension_deltas(
        self,
        landmarks: LandmarkMap,
        start: int,
    ) -> int:
        """Group C: tip.y - mcp.y for each finger (continuous extension signal)."""
        pairs: Tuple[Tuple[int, int], ...] = (
            (self.THUMB_TIP, self.THUMB_MCP),
            (self.INDEX_TIP, self.INDEX_MCP),
            (self.MIDDLE_TIP, self.MIDDLE_MCP),
            (self.RING_TIP, self.RING_MCP),
            (self.PINKY_TIP, self.PINKY_MCP),
        )
        idx = start
        for tip_id, mcp_id in pairs:
            self._features[idx] = landmarks[tip_id].y - landmarks[mcp_id].y
            idx += 1
        return idx

    def _build_bend_angles(
        self,
        landmarks: LandmarkMap,
        start: int,
    ) -> int:
        """Group D: cos(angle) at PIP joint (MCP for thumb) using 2D vectors.

        Each angle uses two consecutive segments:
            v1: proximal bone (mcp -> pip)
            v2: distal bone   (pip -> tip)

        For the thumb the joints are CMC / MCP / IP instead of MCP / PIP / TIP.

        Returns cos(theta) where theta is the interior bend angle.
        A straight finger yields ~1.0, a fully curled finger yields ~-1.0.
        """
        segments: Tuple[Tuple[int, int, int], ...] = (
            (self.THUMB_CMC, self.THUMB_MCP, self.THUMB_IP),
            (self.INDEX_MCP, self.INDEX_PIP, self.INDEX_TIP),
            (self.MIDDLE_MCP, self.MIDDLE_PIP, self.MIDDLE_TIP),
            (self.RING_MCP, self.RING_PIP, self.RING_TIP),
            (self.PINKY_MCP, self.PINKY_PIP, self.PINKY_TIP),
        )
        idx = start
        for p1_id, p2_id, p3_id in segments:
            p1, p2, p3 = landmarks[p1_id], landmarks[p2_id], landmarks[p3_id]
            v1x = p2.x - p1.x
            v1y = p2.y - p1.y
            v2x = p3.x - p2.x
            v2y = p3.y - p2.y
            dot = v1x * v2x + v1y * v2y
            norm = float(np.hypot(v1x, v1y) * np.hypot(v2x, v2y))
            self._features[idx] = dot / norm if norm > 1e-8 else 0.0
            idx += 1
        return idx
