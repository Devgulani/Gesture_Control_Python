"""Tests for DatasetStorage — save, load, export, and delete operations."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from ai.data.dataset_storage import DatasetStorage
from trackers.hand_tracker import LandmarkMap
from utils.helpers import Point


def _make_landmarks(count: int = 21) -> LandmarkMap:
    """Build a synthetic LandmarkMap with count entries."""
    return {
        i: Point(x=float(i) / 20.0, y=float(i % 5) / 5.0, z=float(i) * 0.01,
                 pixel_x=100 + i, pixel_y=200 - i)
        for i in range(count)
    }


@pytest.fixture
def storage() -> DatasetStorage:
    """Temporary empty dataset storage."""
    tmp = Path(tempfile.mkdtemp())
    return DatasetStorage(tmp)


class TestDatasetStorage:
    """Unit tests for DatasetStorage."""

    def test_empty_storage(self, storage: DatasetStorage) -> None:
        assert storage.available_labels == []
        assert storage.total_samples() == 0
        assert storage.label_counts() == {}

    def test_save_and_load(self, storage: DatasetStorage) -> None:
        vec = np.random.randn(61).astype(np.float32)
        sid = storage.save_sample("TEST", vec)
        assert sid == 1

        feats, ids = storage.load_samples("TEST")
        assert feats.shape == (1, 61)
        assert ids == [1]
        np.testing.assert_array_almost_equal(feats[0], vec)

    def test_save_multiple(self, storage: DatasetStorage) -> None:
        for i in range(5):
            vec = np.full(61, float(i), dtype=np.float32)
            sid = storage.save_sample("MULTI", vec)
            assert sid == i + 1

        feats, ids = storage.load_samples("MULTI")
        assert feats.shape == (5, 61)
        assert ids == [1, 2, 3, 4, 5]
        for i in range(5):
            np.testing.assert_array_almost_equal(feats[i], np.full(61, float(i)))

    def test_multiple_labels(self, storage: DatasetStorage) -> None:
        storage.save_sample("A", np.zeros(61, dtype=np.float32))
        storage.save_sample("B", np.ones(61, dtype=np.float32))
        storage.save_sample("A", np.full(61, 2.0, dtype=np.float32))

        assert set(storage.available_labels) == {"A", "B"}
        assert storage.label_counts() == {"A": 2, "B": 1}
        assert storage.total_samples() == 3

    def test_load_nonexistent_label(self, storage: DatasetStorage) -> None:
        feats, ids = storage.load_samples("NONEXISTENT")
        assert feats.shape == (0, 61)
        assert ids == []

    def test_delete_sample(self, storage: DatasetStorage) -> None:
        storage.save_sample("DEL", np.zeros(61, dtype=np.float32))
        storage.save_sample("DEL", np.ones(61, dtype=np.float32))
        assert storage.total_samples() == 2

        ok = storage.delete_sample("DEL", 1)
        assert ok
        assert storage.total_samples() == 1

        feats, ids = storage.load_samples("DEL")
        assert ids == [2]
        np.testing.assert_array_almost_equal(feats[0], np.ones(61))

    def test_delete_nonexistent_sample(self, storage: DatasetStorage) -> None:
        ok = storage.delete_sample("EMPTY", 99)
        assert not ok

    def test_delete_label(self, storage: DatasetStorage) -> None:
        storage.save_sample("KEEP", np.zeros(61, dtype=np.float32))
        storage.save_sample("REMOVE", np.ones(61, dtype=np.float32))
        assert "REMOVE" in storage.available_labels

        ok = storage.delete_label("REMOVE")
        assert ok
        assert "REMOVE" not in storage.available_labels
        assert storage.total_samples() == 1

    def test_delete_nonexistent_label(self, storage: DatasetStorage) -> None:
        ok = storage.delete_label("NONEXISTENT")
        assert not ok

    def test_export_csv(self, storage: DatasetStorage) -> None:
        storage.save_sample("A", np.arange(61, dtype=np.float32))
        storage.save_sample("B", np.arange(61, dtype=np.float32) + 100)

        csv_path = Path(tempfile.mktemp(suffix=".csv"))
        storage.export_csv(csv_path)

        lines = csv_path.read_text().strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows
        header = lines[0].split(",")
        assert header[0] == "label"
        assert header[1] == "feat_0"

        row1 = lines[1].split(",")
        assert row1[0] == "A"
        assert float(row1[1]) == 0.0

    def test_export_json(self, storage: DatasetStorage) -> None:
        storage.save_sample("X", np.arange(61, dtype=np.float32))

        json_path = Path(tempfile.mktemp(suffix=".json"))
        storage.export_json(json_path)

        data = json.loads(json_path.read_text())
        assert "X" in data
        assert len(data["X"]) == 1
        assert data["X"][0]["features"] == list(range(61))

    def test_export_empty(self, storage: DatasetStorage, caplog) -> None:
        csv_path = Path(tempfile.mktemp(suffix=".csv"))
        storage.export_csv(csv_path)
        assert "No data to export" in caplog.text

    def test_train_test_split(self, storage: DatasetStorage) -> None:
        for i in range(20):
            vec = np.full(61, float(i), dtype=np.float32)
            storage.save_sample("CLS", vec)

        train, test = storage.train_test_split(test_ratio=0.25, seed=42)
        assert "CLS" in train
        assert "CLS" in test
        total = train["CLS"].shape[0] + test["CLS"].shape[0]
        assert total == 20

    def test_load_all(self, storage: DatasetStorage) -> None:
        storage.save_sample("A", np.zeros(61, dtype=np.float32))
        storage.save_sample("B", np.ones(61, dtype=np.float32))

        all_data = storage.load_all()
        assert set(all_data.keys()) == {"A", "B"}
        assert all_data["A"].shape == (1, 61)
        assert all_data["B"].shape == (1, 61)

    # ── Landmark storage tests ─────────────────────────────────────

    def test_save_with_landmarks(self, storage: DatasetStorage) -> None:
        vec = np.random.randn(61).astype(np.float32)
        lm = _make_landmarks(21)
        sid = storage.save_sample("GEST", vec, landmarks=lm)

        lm_dict = storage.load_landmarks("GEST")
        assert sid in lm_dict
        assert lm_dict[sid].shape == (21, 3)
        # Spot-check: landmark 0 x-coord should match
        assert abs(lm_dict[sid][0, 0] - lm[0].x) < 1e-6

    def test_save_without_landmarks(self, storage: DatasetStorage) -> None:
        vec = np.zeros(61, dtype=np.float32)
        storage.save_sample("NO_LM", vec)
        lm_dict = storage.load_landmarks("NO_LM")
        assert lm_dict == {}

    def test_delete_sample_removes_landmarks(self, storage: DatasetStorage) -> None:
        lm = _make_landmarks(21)
        sid = storage.save_sample("DEL_LM", np.zeros(61, dtype=np.float32), landmarks=lm)
        assert sid in storage.load_landmarks("DEL_LM")

        storage.delete_sample("DEL_LM", sid)
        assert storage.load_landmarks("DEL_LM") == {}

    # ── Session and profile metadata tests ─────────────────────────

    def test_save_with_session_and_profile(self, storage: DatasetStorage) -> None:
        vec = np.zeros(61, dtype=np.float32)
        sid = storage.save_sample(
            "TAGGED", vec, session_id="abc123", profile_id="user1",
        )
        # Load metadata and verify fields
        label_dir = storage._label_dir("TAGGED")
        meta_path = label_dir / "metadata.json"
        assert meta_path.exists()
        with open(meta_path) as f:
            meta = json.load(f)
        entry = meta.get(str(sid))
        assert entry is not None
        assert entry["session_id"] == "abc123"
        assert entry["profile_id"] == "user1"
        assert "timestamp" in entry

    def test_save_without_session_profile(self, storage: DatasetStorage) -> None:
        vec = np.zeros(61, dtype=np.float32)
        sid = storage.save_sample("PLAIN", vec)
        label_dir = storage._label_dir("PLAIN")
        with open(label_dir / "metadata.json") as f:
            meta = json.load(f)
        entry = meta.get(str(sid))
        assert entry is not None
        assert "session_id" not in entry
        assert "profile_id" not in entry

    # ── Feature count validation tests ─────────────────────────────

    def test_load_samples_wrong_feature_count_warns(self, storage: DatasetStorage) -> None:
        vec = np.zeros(61, dtype=np.float32)
        storage.save_sample("VALID", vec)
        # Manually save a file with wrong shape
        wrong = np.zeros(99, dtype=np.float32)
        label_dir = storage._label_dir("VALID")
        bad_path = label_dir / "sample_BAD.npy"
        np.save(bad_path, wrong)

        feats, ids = storage.load_samples("VALID")
        # Should skip the bad file
        assert ids == [1]

    def test_load_samples_all_wrong_raises(self, storage: DatasetStorage) -> None:
        label_dir = storage._label_dir("BROKEN")
        label_dir.mkdir(parents=True, exist_ok=True)
        wrong = np.zeros(99, dtype=np.float32)
        np.save(label_dir / "sample_00000001.npy", wrong)

        with pytest.raises(ValueError, match="All samples.*mismatch"):
            storage.load_samples("BROKEN")

    # ── Schema version tests ───────────────────────────────────────

    def test_config_contains_schema_version(self, storage: DatasetStorage) -> None:
        vec = np.zeros(61, dtype=np.float32)
        storage.save_sample("VER", vec)

        config_path = storage._base_path / "dataset_config.json"
        assert config_path.exists()
        with open(config_path) as f:
            config = json.load(f)
        assert "feature_extractor_schema_version" in config
        assert config["feature_extractor_schema_version"] >= 1
        assert config["feature_count"] == 61
        assert "dataset_schema_version" in config

    def test_landmark_count_in_metadata(self, storage: DatasetStorage) -> None:
        lm = _make_landmarks(21)
        sid = storage.save_sample(
            "LM_META", np.zeros(61, dtype=np.float32), landmarks=lm,
        )
        label_dir = storage._label_dir("LM_META")
        with open(label_dir / "metadata.json") as f:
            meta = json.load(f)
        assert meta[str(sid)]["landmark_count"] == 21

    # ── Landmark file pattern isolation tests ──────────────────────

    def test_landmark_files_not_counted_as_samples(self, storage: DatasetStorage) -> None:
        """Landmark-only directories should not appear in available_labels."""
        vec = np.zeros(61, dtype=np.float32)
        storage.save_sample("REAL", vec)

        label_dir = storage._label_dir("REAL")
        orphan_dir = storage._label_dir("ORPHAN_LM")
        orphan_dir.mkdir(parents=True, exist_ok=True)
        # Create only a landmark file with no companion feature file
        np.save(orphan_dir / "sample_00000001_lm.npy", np.zeros((21, 3), dtype=np.float32))

        assert "ORPHAN_LM" not in storage.available_labels
