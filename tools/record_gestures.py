#!/usr/bin/env python3
"""Standalone tool for recording gesture samples.

Opens the webcam and shows an interactive OpenCV window. Press number
keys to select a gesture label, then press SPACE to save the current
hand-landmark feature vector.

Usage::

    python -m tools.record_gestures
"""

from __future__ import annotations

import logging

from ai.data.gesture_recorder import GestureRecorder


def main() -> None:
    """Launch the gesture recorder tool."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    recorder = GestureRecorder()
    recorder.run()


if __name__ == "__main__":
    main()
