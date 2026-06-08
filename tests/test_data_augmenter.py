"""Tests for DataAugmenter — augmentation pipelines for feature vectors."""

from __future__ import annotations

import numpy as np
import pytest

from ai.data.data_augmenter import DataAugmenter


@pytest.fixture
def vec() -> np.ndarray:
    """A stable 61-element feature vector for testing."""
    return np.arange(61, dtype=np.float32)


@pytest.fixture
def rng() -> np.random.Generator:
    """Deterministic RNG for reproducible tests."""
    return np.random.default_rng(42)


class TestDataAugmenter:
    """Unit tests for DataAugmenter."""

    def test_add_jitter_output_shape(self, vec: np.ndarray, rng: np.random.Generator) -> None:
        aug = DataAugmenter.add_jitter(vec, std=0.01, rng=rng)
        assert aug.shape == vec.shape
        assert aug.dtype == vec.dtype

    def test_add_jitter_adds_noise(self, vec: np.ndarray, rng: np.random.Generator) -> None:
        aug = DataAugmenter.add_jitter(vec, std=0.1, rng=rng)
        # With std=0.1, at least some values should differ notably
        diff = np.abs(aug - vec)
        assert diff.mean() > 0.01

    def test_add_jitter_no_noise_when_std_zero(self, vec: np.ndarray) -> None:
        aug = DataAugmenter.add_jitter(vec, std=0.0, rng=np.random.default_rng(0))
        np.testing.assert_array_almost_equal(aug, vec)

    def test_scale_variation_output_shape(self, vec: np.ndarray, rng: np.random.Generator) -> None:
        aug = DataAugmenter.scale_variation(vec, factor_range=(0.9, 1.1), rng=rng)
        assert aug.shape == vec.shape

    def test_scale_variation_factor_applied(self, vec: np.ndarray) -> None:
        # Force factor = 2.0 by setting range to [2.0, 2.0]
        aug = DataAugmenter.scale_variation(
            vec, factor_range=(2.0, 2.0), rng=np.random.default_rng(0)
        )
        np.testing.assert_array_almost_equal(aug, vec * 2.0)

    def test_feature_dropout_output_shape(self, vec: np.ndarray, rng: np.random.Generator) -> None:
        aug = DataAugmenter.feature_dropout(vec, drop_prob=0.5, rng=rng)
        assert aug.shape == vec.shape

    def test_feature_dropout_zeros_some_elements(self, vec: np.ndarray) -> None:
        aug = DataAugmenter.feature_dropout(
            vec, drop_prob=1.0, rng=np.random.default_rng(0)
        )
        # With prob=1.0, all elements should be zero
        assert np.all(aug == 0.0)

    def test_feature_dropout_no_drop_when_prob_zero(self, vec: np.ndarray) -> None:
        aug = DataAugmenter.feature_dropout(
            vec, drop_prob=0.0, rng=np.random.default_rng(0)
        )
        np.testing.assert_array_almost_equal(aug, vec)

    def test_augment_single_count(self, vec: np.ndarray, rng: np.random.Generator) -> None:
        variants = DataAugmenter.augment_single(vec, n_variations=5, rng=rng)
        assert len(variants) == 5
        for v in variants:
            assert v.shape == (61,)
            assert v.dtype == np.float32

    def test_augment_single_not_identity(self, vec: np.ndarray, rng: np.random.Generator) -> None:
        variants = DataAugmenter.augment_single(vec, n_variations=3, rng=rng)
        for v in variants:
            # Extremely unlikely all three transforms produce the identity
            assert not np.array_equal(v, vec)

    def test_augment_single_default_n(self, vec: np.ndarray) -> None:
        variants = DataAugmenter.augment_single(vec, rng=np.random.default_rng(0))
        assert len(variants) == DataAugmenter.N_VARIATIONS

    def test_augment_dataset_shapes(self, rng: np.random.Generator) -> None:
        features = np.random.randn(10, 61).astype(np.float32)
        labels = np.array(["A", "B"] * 5)
        aug_features, aug_labels = DataAugmenter.augment_dataset(
            features, labels, n_variations=3, rng=rng
        )
        assert aug_features.shape == (30, 61)
        assert aug_labels.shape == (30,)

    def test_augment_dataset_preserves_labels(self) -> None:
        features = np.zeros((4, 61), dtype=np.float32)
        labels = np.array(["X", "X", "Y", "Y"])
        aug_features, aug_labels = DataAugmenter.augment_dataset(
            features, labels, n_variations=2, rng=np.random.default_rng(0)
        )
        # First 4 augments should be from X (2 per original = 4)
        assert np.all(aug_labels[:4] == "X")
        assert np.all(aug_labels[4:] == "Y")

    def test_deterministic_with_seed(self, vec: np.ndarray) -> None:
        rng1 = np.random.default_rng(123)
        rng2 = np.random.default_rng(123)
        v1 = DataAugmenter.augment_single(vec, n_variations=4, rng=rng1)
        v2 = DataAugmenter.augment_single(vec, n_variations=4, rng=rng2)
        for a, b in zip(v1, v2):
            np.testing.assert_array_almost_equal(a, b)

    def test_different_with_different_seeds(self, vec: np.ndarray) -> None:
        rng1 = np.random.default_rng(1)
        rng2 = np.random.default_rng(2)
        v1 = DataAugmenter.augment_single(vec, n_variations=1, rng=rng1)
        v2 = DataAugmenter.augment_single(vec, n_variations=1, rng=rng2)
        # Extremely unlikely to be same
        assert not np.array_equal(v1[0], v2[0])
