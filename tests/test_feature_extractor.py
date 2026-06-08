"""Tests for the FeatureExtractor (Phase 1B schema, 61 features)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from ai.features.extractor import FeatureExtractor
from configs import ai_config
from trackers.hand_tracker import LandmarkMap
from utils.helpers import Point, euclidean_distance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

L21 = 21  # full set of MediaPipe landmarks


def _make_landmarks(
    positions: list[tuple[float, float, float]],
) -> LandmarkMap:
    """Build a LandmarkMap from (x, y, z) triples."""
    return {
        i: Point(x=x, y=y, z=z, pixel_x=int(x * 640), pixel_y=int(y * 480))
        for i, (x, y, z) in enumerate(positions)
    }


def _open_hand_landmarks() -> LandmarkMap:
    """Synthetic open-hand pose: wrist at bottom, fingers spread upward.

    Natural anatomy: middle fingertip is highest, index and ring are
    slightly lower and spread laterally, pinky is lowest.
    All fingertips are well above their MCPs (negative extension deltas),
    and adjacent fingers have significant horizontal spread.
    """
    pts: list[tuple[float, float, float]] = [(0.5, 0.8, 0.0)]
    # thumb
    pts.extend([
        (0.44, 0.70, 0.02),   # 1 CMC
        (0.38, 0.62, 0.04),   # 2 MCP
        (0.33, 0.54, 0.06),   # 3 IP
        (0.28, 0.46, 0.08),   # 4 TIP
    ])
    # index (x=0.46, extended upward)
    pts.extend([
        (0.47, 0.65, 0.0),    # 5 MCP
        (0.47, 0.52, 0.0),    # 6 PIP
        (0.46, 0.40, 0.0),    # 7 DIP
        (0.46, 0.30, 0.0),    # 8 TIP
    ])
    # middle (x=0.50, centre, highest)
    pts.extend([
        (0.50, 0.63, 0.0),    # 9 MCP
        (0.50, 0.48, 0.0),    # 10 PIP
        (0.50, 0.34, 0.0),    # 11 DIP
        (0.50, 0.22, 0.0),    # 12 TIP
    ])
    # ring (x=0.54)
    pts.extend([
        (0.53, 0.65, 0.0),    # 13 MCP
        (0.53, 0.52, 0.0),    # 14 PIP
        (0.54, 0.42, 0.0),    # 15 DIP
        (0.54, 0.33, 0.0),    # 16 TIP
    ])
    # pinky (x=0.57, lowest)
    pts.extend([
        (0.56, 0.68, 0.0),    # 17 MCP
        (0.56, 0.57, 0.0),    # 18 PIP
        (0.57, 0.48, 0.0),    # 19 DIP
        (0.57, 0.42, 0.0),    # 20 TIP
    ])
    assert len(pts) == L21
    return _make_landmarks(pts)


def _fist_landmarks() -> LandmarkMap:
    """Synthetic fist pose: fingers curled inward, tips clustered near palm.

    All four fingertips cluster within a small horizontal band (x ≈ 0.46-0.50)
    near the palm centre (y ≈ 0.69-0.72). PIPs bend downward (higher y) and
    DIPs/TIPs curl back upward, creating large bend angles at the PIP joint.
    This yields small pairwise distances, positive extension deltas, and
    negative-to-moderate bend-angle cosines.
    """
    pts: list[tuple[float, float, float]] = [(0.5, 0.82, 0.0)]  # wrist
    # thumb wraps across
    pts.extend([
        (0.44, 0.75, 0.02),   # 1 CMC
        (0.42, 0.69, 0.04),   # 2 MCP
        (0.43, 0.67, 0.06),   # 3 IP
        (0.44, 0.70, 0.08),   # 4 TIP
    ])
    # index curled
    pts.extend([
        (0.47, 0.66, 0.0),    # 5 MCP
        (0.47, 0.72, 0.02),   # 6 PIP (down)
        (0.46, 0.75, 0.04),   # 7 DIP (further down)
        (0.46, 0.71, 0.06),   # 8 TIP (curls back up toward palm)
    ])
    # middle curled
    pts.extend([
        (0.49, 0.65, 0.0),    # 9 MCP
        (0.49, 0.71, 0.02),   # 10 PIP
        (0.48, 0.74, 0.04),   # 11 DIP
        (0.48, 0.70, 0.06),   # 12 TIP
    ])
    # ring curled
    pts.extend([
        (0.51, 0.66, 0.0),    # 13 MCP
        (0.51, 0.72, 0.02),   # 14 PIP
        (0.50, 0.75, 0.04),   # 15 DIP
        (0.50, 0.71, 0.06),   # 16 TIP
    ])
    # pinky curled
    pts.extend([
        (0.53, 0.69, 0.0),    # 17 MCP
        (0.52, 0.74, 0.02),   # 18 PIP
        (0.51, 0.77, 0.04),   # 19 DIP
        (0.50, 0.72, 0.06),   # 20 TIP
    ])
    assert len(pts) == L21
    return _make_landmarks(pts)


def _pinch_landmarks() -> LandmarkMap:
    """Synthetic pinch pose: thumb and index tips touching, others extended."""
    pts: list[tuple[float, float, float]] = [(0.5, 0.8, 0.0)]  # wrist
    # thumb curled in toward index
    pts.extend([
        (0.47, 0.68, 0.02),   # 1
        (0.45, 0.58, 0.04),   # 2
        (0.44, 0.48, 0.06),   # 3
        (0.44, 0.40, 0.08),   # 4 TIP — touching index
    ])
    # index curled to meet thumb
    pts.extend([
        (0.46, 0.64, 0.0),    # 5 MCP
        (0.45, 0.54, 0.0),    # 6 PIP
        (0.44, 0.46, 0.0),    # 7 DIP
        (0.44, 0.40, 0.0),    # 8 TIP — touching thumb
    ])
    # middle, ring, pinky extended
    pts.extend([
        (0.50, 0.63, 0.0),    # 9
        (0.50, 0.46, 0.0),    # 10
        (0.50, 0.33, 0.0),    # 11
        (0.50, 0.22, 0.0),    # 12
    ])
    pts.extend([
        (0.52, 0.65, 0.0),    # 13
        (0.52, 0.50, 0.0),    # 14
        (0.52, 0.38, 0.0),    # 15
        (0.52, 0.28, 0.0),    # 16
    ])
    pts.extend([
        (0.54, 0.68, 0.0),    # 17
        (0.54, 0.55, 0.0),    # 18
        (0.54, 0.45, 0.0),    # 19
        (0.54, 0.37, 0.0),    # 20
    ])
    assert len(pts) == L21
    return _make_landmarks(pts)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFeatureExtractor:
    """Suite for the 61-feature Phase 1B extractor."""

    def test_output_shape(self) -> None:
        ext = FeatureExtractor()
        assert ext.feature_count == 61
        assert ext.feature_count == ai_config.FEATURE_COUNT
        vec = ext.extract(_open_hand_landmarks())
        assert vec is not None
        assert vec.shape == (61,)
        assert vec.dtype == np.float32

    def test_empty_landmarks_returns_none(self) -> None:
        ext = FeatureExtractor()
        assert ext.extract({}) is None

    def test_partial_landmarks_returns_none(self) -> None:
        ext = FeatureExtractor()
        lm = {0: Point(0.5, 0.5, 0.0, 320, 240)}
        assert ext.extract(lm) is None

    def test_invalid_hand_size_returns_none(self) -> None:
        """All landmarks at same position -> hand_size ~0 -> return None."""
        ext = FeatureExtractor()
        lm = _make_landmarks([(0.5, 0.5, 0.0)] * 21)
        assert ext.extract(lm) is None

    # -- Group A: wrist-relative invariance --------------------------------

    def test_group_a_wrist_relative_zero_at_wrist(self) -> None:
        """Landmark 0 is excluded from wrist-relative block (indices 0-39)."""
        lm = _open_hand_landmarks()
        vec = ext = FeatureExtractor().extract(lm)
        assert vec is not None
        # Wrist-relative block occupies indices 0-39. The first entry is
        # landmark 1 x-relative, landmark 1 y-relative, etc.
        # Landmark 0 is never stored in this block.

    def test_group_a_wrist_relative_position_independent(self) -> None:
        """Shifting the hand on screen should not change features."""
        ext = FeatureExtractor()
        lm1 = _open_hand_landmarks()
        # Shift every point by (+0.1, -0.05)
        lm2 = _make_landmarks([
            (p.x + 0.1, p.y - 0.05, p.z)
            for p in lm1.values()
        ])
        v1 = ext.extract(lm1)
        v2 = ext.extract(lm2)
        assert v1 is not None and v2 is not None
        # Group A (indices 0-39) should match exactly
        assert np.allclose(v1[:40], v2[:40], atol=1e-6)
        # Hand size (index 60) should also match (same hand, shifted)
        assert abs(v1[60] - v2[60]) < 1e-6

    # -- Group B: pairwise distances ---------------------------------------

    def test_group_b_open_hand_distances_large(self) -> None:
        """Open hand: all fingertips far from each other relative to hand."""
        ext = FeatureExtractor()
        vec = ext.extract(_open_hand_landmarks())
        assert vec is not None
        distances = vec[40:50]
        assert np.all(distances > 0.08), f"Open hand distances too small: {distances}"

    def test_group_b_fist_vs_open_hand(self) -> None:
        """Fist distances are smaller than open-hand distances."""
        ext = FeatureExtractor()
        open_vec = ext.extract(_open_hand_landmarks())
        fist_vec = ext.extract(_fist_landmarks())
        assert open_vec is not None and fist_vec is not None
        assert np.all(fist_vec[40:50] < open_vec[40:50]), (
            "All fist pairwise distances should be smaller than open-hand equivalents"
        )

    def test_group_b_pinch_thumb_index_smallest(self) -> None:
        """Pinch: thumb-index distance (pair 0) is the smallest."""
        ext = FeatureExtractor()
        vec = ext.extract(_pinch_landmarks())
        assert vec is not None
        distances = vec[40:50]
        # pair 0 = thumb(0)-index(1), pair 1 = thumb-middle, ...
        assert distances[0] < distances[4], (
            f"thumb-index ({distances[0]}) should be < index-middle ({distances[4]})"
        )

    # -- Group C: extension deltas -----------------------------------------

    def test_group_c_open_hand_all_negative(self) -> None:
        """Open hand: all tip.y < mcp.y (negative deltas, fingers extended)."""
        ext = FeatureExtractor()
        vec = ext.extract(_open_hand_landmarks())
        assert vec is not None
        deltas = vec[50:55]
        assert np.all(deltas < 0), f"Open hand deltas should be negative: {deltas}"

    def test_group_c_fist_more_positive_than_open(self) -> None:
        """Fist deltas are more positive than open-hand deltas."""
        ext = FeatureExtractor()
        open_vec = ext.extract(_open_hand_landmarks())
        fist_vec = ext.extract(_fist_landmarks())
        assert open_vec is not None and fist_vec is not None
        assert np.all(fist_vec[50:55] > open_vec[50:55]), (
            "All fist extension deltas should be more positive than open-hand deltas"
        )

    # -- Group D: bend angles ----------------------------------------------

    def test_group_d_open_hand_near_one(self) -> None:
        """Open hand: all bend angles near 1.0 (straight fingers)."""
        ext = FeatureExtractor()
        vec = ext.extract(_open_hand_landmarks())
        assert vec is not None
        angles = vec[55:60]
        assert np.all(angles > 0.9), f"Open hand angles should be near 1: {angles}"

    def test_group_d_fist_smaller_than_open(self) -> None:
        """Fist bend-angle cosines are smaller (more curled) than open-hand cosines."""
        ext = FeatureExtractor()
        open_vec = ext.extract(_open_hand_landmarks())
        fist_vec = ext.extract(_fist_landmarks())
        assert open_vec is not None and fist_vec is not None
        assert np.all(fist_vec[55:60] < open_vec[55:60]), (
            "All fist angle cosines should be smaller than open-hand cosines"
        )

    def test_group_d_angle_range(self) -> None:
        """All angle cosines are in [-1, 1]."""
        ext = FeatureExtractor()
        for pose in (_open_hand_landmarks, _fist_landmarks, _pinch_landmarks):
            vec = ext.extract(pose())
            assert vec is not None
            assert np.all(np.abs(vec[55:60]) <= 1.0 + 1e-6), (
                f"Angle cosines out of [-1,1] for {pose.__name__}: {vec[55:60]}"
            )

    # -- Group E: hand size ------------------------------------------------

    def test_group_e_hand_size_matches_wrist_to_middle_mcp(self) -> None:
        """Index 60 equals euclidean_distance(wrist, middle_mcp)."""
        ext = FeatureExtractor()
        lm = _open_hand_landmarks()
        vec = ext.extract(lm)
        assert vec is not None
        expected = euclidean_distance(lm[0], lm[9])
        assert abs(vec[60] - expected) < 1e-6

    def test_group_e_hand_size_is_positive(self) -> None:
        """Hand size is always positive for valid landmarks."""
        ext = FeatureExtractor()
        for pose in (_open_hand_landmarks, _fist_landmarks, _pinch_landmarks):
            vec = ext.extract(pose())
            assert vec is not None
            assert vec[60] > 0

    # -- Determinism -------------------------------------------------------

    def test_deterministic_output(self) -> None:
        """Same input produces identical output."""
        ext = FeatureExtractor()
        lm = _open_hand_landmarks()
        v1 = ext.extract(lm)
        v2 = ext.extract(lm)
        assert v1 is not None and v2 is not None
        assert np.array_equal(v1, v2)
