"""Save, load, and manage labeled gesture datasets.

Storage layout::

    datasets/
    ├── dataset_config.json               # version, feature_count, schema_version
    ├── LABEL_1/
    │   ├── sample_00000001.npy           # feature vector (61,) float32
    │   ├── sample_00000001_lm.npy        # raw landmarks (21, 3) float32  (optional)
    │   ├── sample_00000002.npy
    │   ├── sample_00000002_lm.npy
    │   └── metadata.json                # {sample_id: {timestamp, source,
    │                                    #    session_id, profile_id, landmark_count}}
    ├── LABEL_2/
    │   └── ...
    └── ...

Each sample stores its 61-element feature vector as a separate .npy file
and, when available, a (21, 3) raw-landmark array as a companion *_lm.npy file.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from configs import ai_config
from trackers.hand_tracker import LandmarkMap

logger = logging.getLogger(__name__)

CONFIG_FILE = "dataset_config.json"
METADATA_FILE = "metadata.json"
SAMPLE_PREFIX = "sample_"
LANDMARK_SUFFIX = "_lm"
SAMPLE_DIGITS = 8


class DatasetStorage:
    """Manages labeled feature-vector datasets on disk.

    Each sample can optionally store raw landmarks alongside features
    for forward-compatible re-extraction when the feature schema changes.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self._base_path = (base_path or ai_config.DATASET_DIR).resolve()
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._ensure_config()
        self._check_schema_version()
        logger.info("DatasetStorage initialised at %s", self._base_path)

    # ── Public API ─────────────────────────────────────────────────

    def save_sample(
        self,
        label: str,
        features: np.ndarray,
        landmarks: Optional[LandmarkMap] = None,
        session_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        source: str = "record",
    ) -> int:
        """Save a single feature vector and return its sample ID.

        Args:
            label: Gesture-pose label (e.g. ``"FIST"``, ``"POINTING"``).
            features: 61-element feature vector.
            landmarks: Optional raw landmarks (LandmarkMap) — saved as
                a companion (21, 3) array for future re-extraction.
            session_id: Recording session identifier.
            profile_id: User profile identifier (from ProfileManager).
            source: ``"record"`` or ``"augmented"``.

        Returns:
            Unique sample ID (auto-incremented per label).
        """
        label_dir = self._label_dir(label)
        label_dir.mkdir(parents=True, exist_ok=True)

        sample_id = self._next_sample_id(label_dir)
        self._save_feature_file(label_dir, sample_id, features)

        landmark_count = 0
        if landmarks:
            self._save_landmark_file(label_dir, sample_id, landmarks)
            landmark_count = 21

        meta = self._load_metadata(label)
        timestamp = datetime.now(timezone.utc).isoformat()
        entry: Dict[str, Any] = {
            "timestamp": timestamp,
            "source": source,
        }
        if session_id:
            entry["session_id"] = session_id
        if profile_id:
            entry["profile_id"] = profile_id
        if landmark_count:
            entry["landmark_count"] = landmark_count

        meta[str(sample_id)] = entry
        self._save_metadata(label, meta)
        self._update_config()

        return sample_id

    def load_samples(self, label: str) -> Tuple[np.ndarray, List[int]]:
        """Return (features_array, sample_ids) for a given label.

        Validates that every loaded feature vector has the expected
        number of dimensions (``FEATURE_COUNT``).  Samples with a
        dimension mismatch are skipped with a warning.

        Raises:
            ValueError: If *every* sample has a dimension mismatch.
        """
        label_dir = self._label_dir(label)
        if not label_dir.is_dir():
            return np.empty((0, ai_config.FEATURE_COUNT), dtype=np.float32), []

        sample_files = sorted(label_dir.glob(f"{SAMPLE_PREFIX}[0-9]*.npy"))
        expected = ai_config.FEATURE_COUNT
        features_list: List[np.ndarray] = []
        ids: List[int] = []
        found_any = False

        for f in sample_files:
            if f.stem.endswith(LANDMARK_SUFFIX):
                continue
            found_any = True
            sid = int(f.stem.replace(SAMPLE_PREFIX, ""))
            arr = np.load(f)
            if arr.shape[-1] != expected:
                logger.warning(
                    "Skipping %s: expected %d features, got %d. "
                    "Migrate or re-record this sample.",
                    f.name,
                    expected,
                    arr.shape[-1],
                )
                continue
            features_list.append(arr)
            ids.append(sid)

        if not features_list:
            if found_any:
                raise ValueError(
                    f"All samples for label '{label}' have a feature count mismatch "
                    f"(expected {expected}). Run dataset migration or re-record."
                )
            return np.empty((0, expected), dtype=np.float32), []

        return np.stack(features_list, axis=0).astype(np.float32), ids

    def load_landmarks(self, label: str) -> Dict[int, np.ndarray]:
        """Load raw-landmark arrays for every sample of a label.

        Returns:
            Dict mapping sample_id -> (21, 3) float32 array of
            normalised (x, y, z) coordinates.  Empty dict if no
            landmarks exist.
        """
        label_dir = self._label_dir(label)
        if not label_dir.is_dir():
            return {}

        result: Dict[int, np.ndarray] = {}
        for f in sorted(label_dir.glob(f"{SAMPLE_PREFIX}[0-9]*{LANDMARK_SUFFIX}.npy")):
            sid = self._sample_id_from_path(f)
            result[sid] = np.load(f).astype(np.float32)
        return result

    def load_all(self) -> Dict[str, np.ndarray]:
        """Return dict mapping label -> features_array for every label."""
        result: Dict[str, np.ndarray] = {}
        for label in self.available_labels:
            feats, _ = self.load_samples(label)
            if feats.shape[0] > 0:
                result[label] = feats
        return result

    def delete_sample(self, label: str, sample_id: int) -> bool:
        """Delete a single sample (feature file + companion files) by ID.

        Returns True if the feature file was deleted.
        """
        label_dir = self._label_dir(label)
        sample_path = label_dir / f"{SAMPLE_PREFIX}{sample_id:0{SAMPLE_DIGITS}d}.npy"
        if not sample_path.exists():
            return False

        sample_path.unlink()
        # Remove companion landmark file if present
        lm_path = label_dir / f"{SAMPLE_PREFIX}{sample_id:0{SAMPLE_DIGITS}d}{LANDMARK_SUFFIX}.npy"
        if lm_path.exists():
            lm_path.unlink()

        meta = self._load_metadata(label)
        meta.pop(str(sample_id), None)
        self._save_metadata(label, meta)
        return True

    def delete_label(self, label: str) -> bool:
        """Delete all samples for a label. Returns True if deleted."""
        label_dir = self._label_dir(label)
        if not label_dir.is_dir():
            return False

        for f in label_dir.glob(f"{SAMPLE_PREFIX}[0-9]*.npy"):
            f.unlink()
        for f in label_dir.glob(f"{SAMPLE_PREFIX}[0-9]*{LANDMARK_SUFFIX}.npy"):
            f.unlink()
        meta_file = label_dir / METADATA_FILE
        if meta_file.exists():
            meta_file.unlink()
        label_dir.rmdir()
        return True

    @property
    def available_labels(self) -> List[str]:
        """Return sorted list of labels that have at least one sample."""
        labels: List[str] = []
        for child in sorted(self._base_path.iterdir()):
            if child.is_dir() and any(
                child.glob(f"{SAMPLE_PREFIX}[0-9]*.npy")
            ):
                # Exclude landmark-only entries by checking for non-_lm files
                has_features = any(
                    not p.stem.endswith(LANDMARK_SUFFIX)
                    for p in child.glob(f"{SAMPLE_PREFIX}[0-9]*.npy")
                )
                if has_features:
                    labels.append(child.name)
        return labels

    def label_counts(self) -> Dict[str, int]:
        """Return dict mapping label -> sample count."""
        counts: Dict[str, int] = {}
        for label in self.available_labels:
            meta = self._load_metadata(label)
            counts[label] = len(meta)
        return counts

    def total_samples(self) -> int:
        """Return total number of samples across all labels."""
        return sum(self.label_counts().values())

    def summary(self) -> str:
        """Return a human-readable dataset summary."""
        counts = self.label_counts()
        total = sum(counts.values())
        lines = [
            f"Dataset at: {self._base_path}",
            f"Total samples: {total}",
            f"Labels: {len(counts)}",
        ]
        for label in sorted(counts):
            lines.append(f"  {label}: {counts[label]} samples")
        return "\n".join(lines)

    def export_csv(self, path: Path) -> None:
        """Export all labeled samples to a single CSV file.

        Columns: label, feat_0, feat_1, ..., feat_N
        """
        all_features: List[np.ndarray] = []
        all_labels: List[str] = []

        for label in self.available_labels:
            feats, _ = self.load_samples(label)
            if feats.shape[0] > 0:
                all_features.append(feats)
                all_labels.extend([label] * feats.shape[0])

        if not all_features:
            logger.warning("No data to export — dataset is empty")
            return

        features_stack = np.concatenate(all_features, axis=0)
        header = ["label"] + [f"feat_{i}" for i in range(features_stack.shape[1])]

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for i in range(len(all_labels)):
                writer.writerow([all_labels[i]] + features_stack[i].tolist())

        logger.info("Exported %d samples to %s", len(all_labels), path)

    def export_json(self, path: Path) -> None:
        """Export all labeled samples to JSON.

        Structure: {label: [{features: [...], metadata: {...}}, ...]}
        """
        export: Dict[str, List[Dict[str, Any]]] = {}
        for label in self.available_labels:
            feats, ids = self.load_samples(label)
            meta = self._load_metadata(label)
            entries: List[Dict[str, Any]] = []
            for i, sid in enumerate(ids):
                entry: Dict[str, Any] = {
                    "features": feats[i].tolist(),
                }
                if str(sid) in meta:
                    entry["metadata"] = meta[str(sid)]
                entries.append(entry)
            export[label] = entries

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(export, f, indent=2)

        total = sum(len(v) for v in export.values())
        logger.info("Exported %d samples to %s", total, path)

    def train_test_split(
        self,
        test_ratio: float = 0.2,
        seed: int = 42,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """Split the dataset into train/test dicts by label."""
        rng = np.random.default_rng(seed)
        train: Dict[str, np.ndarray] = {}
        test: Dict[str, np.ndarray] = {}

        for label in self.available_labels:
            feats, _ = self.load_samples(label)
            n = feats.shape[0]
            if n == 0:
                continue
            indices = rng.permutation(n)
            split = max(1, int(n * (1 - test_ratio)))
            train[label] = feats[indices[:split]]
            test[label] = feats[indices[split:]]

        return train, test

    # ── Internal helpers ──────────────────────────────────────────

    def _label_dir(self, label: str) -> Path:
        sanitised = label.strip().replace(" ", "_").replace("/", "_")
        return self._base_path / sanitised

    @staticmethod
    def _feature_path(label_dir: Path, sample_id: int) -> Path:
        return label_dir / f"{SAMPLE_PREFIX}{sample_id:0{SAMPLE_DIGITS}d}.npy"

    @staticmethod
    def _landmark_path(label_dir: Path, sample_id: int) -> Path:
        return (
            label_dir
            / f"{SAMPLE_PREFIX}{sample_id:0{SAMPLE_DIGITS}d}{LANDMARK_SUFFIX}.npy"
        )

    @staticmethod
    def _sample_id_from_path(path: Path) -> int:
        stem = path.stem
        numeric = stem.replace(SAMPLE_PREFIX, "").replace(LANDMARK_SUFFIX, "")
        return int(numeric)

    def _save_feature_file(
        self, label_dir: Path, sample_id: int, features: np.ndarray
    ) -> None:
        np.save(self._feature_path(label_dir, sample_id), features)

    def _save_landmark_file(
        self, label_dir: Path, sample_id: int, landmarks: LandmarkMap
    ) -> None:
        arr = np.array(
            [[landmarks[i].x, landmarks[i].y, landmarks[i].z] for i in range(21)],
            dtype=np.float32,
        )
        np.save(self._landmark_path(label_dir, sample_id), arr)

    def _next_sample_id(self, label_dir: Path) -> int:
        existing = list(label_dir.glob(f"{SAMPLE_PREFIX}[0-9]*.npy"))
        if not existing:
            return 1
        max_id = 0
        for f in existing:
            if f.stem.endswith(LANDMARK_SUFFIX):
                continue
            sid = self._sample_id_from_path(f)
            max_id = max(max_id, sid)
        return max_id + 1

    def _ensure_config(self) -> None:
        config_path = self._base_path / CONFIG_FILE
        if not config_path.exists():
            self._write_config()

    def _write_config(self) -> None:
        config_path = self._base_path / CONFIG_FILE
        config = {
            "dataset_schema_version": "2.0",
            "feature_count": ai_config.FEATURE_COUNT,
            "feature_extractor_schema_version": (
                ai_config.FEATURE_EXTRACTOR_SCHEMA_VERSION
            ),
            "created": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _update_config(self) -> None:
        config_path = self._base_path / CONFIG_FILE
        if not config_path.exists():
            self._write_config()
            return
        try:
            with open(config_path) as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            config = {}
        config["dataset_schema_version"] = "2.0"
        config["feature_count"] = ai_config.FEATURE_COUNT
        config["feature_extractor_schema_version"] = (
            ai_config.FEATURE_EXTRACTOR_SCHEMA_VERSION
        )
        config["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _check_schema_version(self) -> None:
        """Log a warning if the stored schema version differs from current."""
        config_path = self._base_path / CONFIG_FILE
        if not config_path.exists():
            return
        try:
            with open(config_path) as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        stored_feature_count = config.get("feature_count")
        stored_schema_ver = config.get("feature_extractor_schema_version")

        if stored_feature_count is not None and stored_feature_count != ai_config.FEATURE_COUNT:
            logger.warning(
                "Dataset stored feature_count=%d, current FEATURE_COUNT=%d. "
                "Migrate or re-record samples.",
                stored_feature_count,
                ai_config.FEATURE_COUNT,
            )
        if stored_schema_ver is not None and stored_schema_ver != ai_config.FEATURE_EXTRACTOR_SCHEMA_VERSION:
            logger.warning(
                "Dataset stored feature_extractor_schema_version=%s, "
                "current version=%d. Samples may need migration.",
                stored_schema_ver,
                ai_config.FEATURE_EXTRACTOR_SCHEMA_VERSION,
            )

    def _load_metadata(self, label: str) -> Dict[str, Any]:
        meta_path = self._label_dir(label) / METADATA_FILE
        if not meta_path.exists():
            return {}
        with open(meta_path) as f:
            return dict(json.load(f))

    def _save_metadata(self, label: str, data: Dict[str, Any]) -> None:
        meta_path = self._label_dir(label) / METADATA_FILE
        with open(meta_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
