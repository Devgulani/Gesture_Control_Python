"""Data augmentation for hand-landmark feature vectors.

Provides stochastic transformations that produce realistic
variations of gesture feature vectors for training ML models.

All augmentations operate directly on the 61-element feature vector
output by FeatureExtractor. This avoids re-extracting from landmarks
and is fast enough for online augmentation during training.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from configs import ai_config


class DataAugmenter:
    """Factory for synthetic variations of gesture feature vectors.

    Usage::

        vec = extractor.extract(landmarks)
        variations = DataAugmenter.augment_single(vec, n_variations=4)
        for aug in variations:
            storage.save_sample(label, aug, source="augmented")
    """

    #: Standard deviation of Gaussian noise added to each feature.
    JITTER_STD: float = ai_config.AUGMENT_JITTER_STD
    #: Uniform scale-factor range [min, max].
    SCALE_MIN: float = ai_config.AUGMENT_SCALE_MIN
    SCALE_MAX: float = ai_config.AUGMENT_SCALE_MAX
    #: Probability of zeroing out any single feature.
    FEATURE_DROPOUT_PROB: float = ai_config.AUGMENT_FEATURE_DROPOUT_PROB
    #: Default number of variations to generate per call.
    N_VARIATIONS: int = ai_config.AUGMENT_N_VARIATIONS

    # ── Single-transform helpers ──────────────────────────────────

    @staticmethod
    def add_jitter(
        features: np.ndarray,
        std: Optional[float] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Add Gaussian noise to every element.

        Args:
            features: Input feature vector (shape N,).
            std: Noise standard deviation (default ``JITTER_STD``).
            rng: Optional RNG for reproducibility.

        Returns:
            New array with noise added (no in-place modification).
        """
        rng = rng or np.random.default_rng()
        sigma = std if std is not None else DataAugmenter.JITTER_STD
        return features + rng.normal(0.0, sigma, size=features.shape).astype(
            features.dtype
        )

    @staticmethod
    def scale_variation(
        features: np.ndarray,
        factor_range: Optional[Tuple[float, float]] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Multiply all features by a random scale factor near 1.0.

        This simulates hands of slightly different sizes or camera
        distances beyond the normalisation already performed by the
        FeatureExtractor.

        Args:
            features: Input feature vector (shape N,).
            factor_range: (min, max) for uniform sampling
                (default ``(SCALE_MIN, SCALE_MAX)``).
            rng: Optional RNG for reproducibility.

        Returns:
            Scaled feature vector.
        """
        rng = rng or np.random.default_rng()
        lo, hi = factor_range or (DataAugmenter.SCALE_MIN, DataAugmenter.SCALE_MAX)
        factor = rng.uniform(lo, hi)
        return (features * factor).astype(features.dtype)

    @staticmethod
    def feature_dropout(
        features: np.ndarray,
        drop_prob: Optional[float] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """Randomly set individual features to zero.

        Simulates partial occlusion or tracking noise.

        Args:
            features: Input feature vector (shape N,).
            drop_prob: Per-feature dropout probability
                (default ``FEATURE_DROPOUT_PROB``).
            rng: Optional RNG for reproducibility.

        Returns:
            Feature vector with some elements set to zero.
        """
        rng = rng or np.random.default_rng()
        prob = drop_prob if drop_prob is not None else DataAugmenter.FEATURE_DROPOUT_PROB
        mask = rng.random(size=features.shape) > prob
        return (features * mask).astype(features.dtype)

    # ── Composite pipelines ───────────────────────────────────────

    @classmethod
    def augment_single(
        cls,
        features: np.ndarray,
        n_variations: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> List[np.ndarray]:
        """Generate *n* augmented variations of a single feature vector.

        Each variation is the result of applying a random combination
        of jitter, scale, and dropout.  The original vector is *not*
        included in the returned list.

        Args:
            features: Input feature vector (shape ``(FEATURE_COUNT,)``).
            n_variations: Number of variations to generate
                (default ``N_VARIATIONS``).
            rng: Optional RNG for reproducibility.

        Returns:
            List of ``n_variations`` augmented vectors.
        """
        n = n_variations or cls.N_VARIATIONS
        rng = rng or np.random.default_rng()
        variations: List[np.ndarray] = []

        for _ in range(n):
            aug = features.copy()
            aug = cls.add_jitter(aug, rng=rng)
            aug = cls.scale_variation(aug, rng=rng)
            aug = cls.feature_dropout(aug, rng=rng)
            variations.append(aug)

        return variations

    @classmethod
    def augment_dataset(
        cls,
        features: np.ndarray,
        labels: np.ndarray,
        n_variations: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Augment an entire dataset.

        Each original sample generates ``n_variations`` augmented
        copies.  The original samples are *not* included — callers
        that want originals should concatenate them manually.

        Args:
            features: Feature matrix, shape ``(N, FEATURE_COUNT)``.
            labels: Label array, shape ``(N,)``.
            n_variations: Variations per original sample
                (default ``N_VARIATIONS``).
            rng: Optional RNG for reproducibility.

        Returns:
            Tuple ``(augmented_features, augmented_labels)``.
            Shape is ``(N * n, FEATURE_COUNT)`` and ``(N * n,)``.
        """
        n = n_variations or cls.N_VARIATIONS
        rng = rng or np.random.default_rng()
        out_features: List[np.ndarray] = []
        out_labels: List[np.ndarray] = []

        for i in range(features.shape[0]):
            vec = features[i]
            label = labels[i]
            variants = cls.augment_single(vec, n_variations=n, rng=rng)
            out_features.extend(variants)
            out_labels.extend([label] * len(variants))

        return np.stack(out_features, axis=0), np.array(out_labels)
