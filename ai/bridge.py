"""Bridge between the main loop and the AI subsystem.

The AiGestureBridge runs alongside the rule-based gesture detector.
In Phase 1A it only performs feature extraction --- no model loading,
no inference, no classification. The extracted feature vector is
stored in a thread-safe buffer for future use.
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import Optional

import numpy as np

from ai.features.extractor import FeatureExtractor
from trackers.hand_tracker import LandmarkMap


class AiGestureBridge:
    """Non-blocking bridge that accepts landmarks and caches feature vectors.

    The bridge is designed so that model inference can be added later
    in a background thread without changing the main-loop integration.
    """

    def __init__(self) -> None:
        """Initialise the bridge with a feature extractor and empty buffer."""
        self._extractor = FeatureExtractor()
        self._latest_features: Optional[np.ndarray] = None
        self._lock = Lock()
        self._running = False
        logging.info(
            "AiGestureBridge initialised (feature count: %d)",
            self._extractor.feature_count,
        )

    @property
    def is_running(self) -> bool:
        """Return True after start() has been called."""
        return self._running

    @property
    def latest_features(self) -> Optional[np.ndarray]:
        """Return the most recently extracted feature vector (thread-safe)."""
        with self._lock:
            if self._latest_features is None:
                return None
            return self._latest_features.copy()

    def start(self) -> None:
        """Start the bridge.

        In Phase 1A this only marks the bridge as active.  Future
        phases will launch a background inference thread here.
        """
        self._running = True
        logging.info("AiGestureBridge started")

    def process_landmarks(self, landmarks: LandmarkMap) -> None:
        """Extract features from the current frame's landmarks.

        This method is called from the main loop on every frame.
        Feature extraction is lightweight (<0.5 ms) and does not
        block the main thread.

        Args:
            landmarks: Map of landmark index -> Point from HandTracker.
        """
        if not self._running:
            return

        features = self._extractor.extract(landmarks)
        with self._lock:
            self._latest_features = features

    def stop(self) -> None:
        """Stop the bridge and release resources.

        Safe to call multiple times.  Future phases will also join
        the background thread here.
        """
        self._running = False
        with self._lock:
            self._latest_features = None
        logging.info("AiGestureBridge stopped")
