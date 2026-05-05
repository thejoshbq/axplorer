"""Tests for axplorer.dataset — Dataset collection class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from axplorer.dataset import Dataset, load_dataset
from axplorer.types import Session, SessionMeta


# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_metas(tmp_path: Path) -> list[SessionMeta]:
    """Build a list of SessionMeta objects with synthetic files."""
    metas = []
    for phase, animal, sex, fov, tracked in [
        ("EarlyAcq", "animal-1F", "F", "FOV1_tracked", True),
        ("EarlyAcq", "animal-2M", "M", "FOV1", False),
        ("LateAcq", "animal-1F", "F", "FOV2", False),
        ("LateAcq", "animal-3M", "M", "FOV1_tracked", True),
    ]:
        fov_dir = tmp_path / phase / animal / fov
        fov_dir.mkdir(parents=True, exist_ok=True)
        npy_path = fov_dir / "signals_extractedsignals_raw.npy"
        mat_path = fov_dir / "events.mat"
        npy_path.write_bytes(b"\x00" * 1024)
        mat_path.write_bytes(b"\x00" * 512)
        metas.append(
            SessionMeta(
                phase=phase,
                animal_id=animal,
                sex=sex,
                fov=fov,
                is_tracked=tracked,
                npy_paths=(npy_path,),
                event_paths=(mat_path,),
            )
        )
    return metas


@pytest.fixture()
def dataset(sample_metas: list[SessionMeta]) -> Dataset:
    """Return a Dataset from the sample metas."""
    return Dataset(sample_metas)


# ──────────────────────────────────────────────────────────────────────────
# TestDataset
# ──────────────────────────────────────────────────────────────────────────

class TestDataset:
    """Tests for the Dataset collection class."""

    def test_len_and_iter(self, dataset: Dataset, sample_metas: list[SessionMeta]) -> None:
        """Length and iteration match the input list."""
        assert len(dataset) == 4
        assert list(dataset) == sample_metas

    def test_getitem(self, dataset: Dataset, sample_metas: list[SessionMeta]) -> None:
        """Indexing returns the correct SessionMeta."""
        assert dataset[0] == sample_metas[0]
        assert dataset[-1] == sample_metas[-1]

    def test_filter_single_field(self, dataset: Dataset) -> None:
        """Filtering by sex returns only matching sessions."""
        males = dataset.filter(sex="M")
        assert len(males) == 2
        assert all(m.sex == "M" for m in males)

    def test_filter_multiple_fields(self, dataset: Dataset) -> None:
        """Filtering by multiple fields uses AND logic."""
        tracked_females = dataset.filter(sex="F", is_tracked=True)
        assert len(tracked_females) == 1
        assert tracked_females[0].fov == "FOV1_tracked"
        assert tracked_females[0].animal_id == "animal-1F"

    def test_filter_returns_new_dataset(self, dataset: Dataset) -> None:
        """Filtering returns a new Dataset without mutating the original."""
        filtered = dataset.filter(sex="M")
        assert len(dataset) == 4
        assert len(filtered) == 2
        assert isinstance(filtered, Dataset)

    def test_filter_no_match(self, dataset: Dataset) -> None:
        """Filtering with no matches returns an empty Dataset."""
        empty = dataset.filter(phase="NonExistent")
        assert len(empty) == 0

    def test_to_dataframe(self, dataset: Dataset) -> None:
        """to_dataframe() returns the correct columns and row count."""
        df = dataset.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        expected_cols = {
            "phase", "animal_id", "sex", "fov", "is_tracked",
            "npy_paths", "event_paths", "npy_size_mb", "event_size_mb",
        }
        assert set(df.columns) == expected_cols

    def test_to_dataframe_file_sizes(self, dataset: Dataset) -> None:
        """File sizes are computed and present as numeric columns."""
        df = dataset.to_dataframe()
        # Files are small (1024 / 512 bytes) so size_mb rounds to 0.0,
        # but the column should exist and be numeric.
        assert df["npy_size_mb"].dtype == float
        assert df["event_size_mb"].dtype == float
        assert len(df) == 4

    def test_repr(self, dataset: Dataset) -> None:
        """repr shows session count."""
        assert "4 sessions" in repr(dataset)

    def test_load_session(self, dataset: Dataset) -> None:
        """load_session() returns a Session with correct composition."""
        meta = dataset[0]

        mock_sample = MagicMock()
        mock_sample.num_neurons = 10
        mock_sample.num_frames = 5000
        mock_sample.num_events = 50
        mock_sample.effective_fps = 7.5
        mock_sample.name = "test"

        mock_metadata = MagicMock()

        mock_wrapper = MagicMock()

        with (
            patch("axplorer.ingestion.loader.load_session_files", return_value=(mock_sample, mock_metadata)),
            patch("axplorer.alignment.session.SessionWrapper", return_value=mock_wrapper),
        ):
            session = dataset.load_session(meta)

        assert isinstance(session, Session)
        assert session.meta is meta
        assert session.metadata is mock_metadata
        assert session.wrapper is mock_wrapper

    def test_process_all_sequential(self, dataset: Dataset) -> None:
        """process_all with n_jobs=1 applies fn to each session."""
        mock_session = MagicMock(spec=Session)

        with patch.object(Dataset, "load_session", return_value=mock_session):
            results = dataset.process_all(lambda s: s.meta.phase, n_jobs=1)

        # load_session returns the same mock each time, but fn is applied.
        assert len(results) == 4


class TestLoadDataset:
    """Tests for the load_dataset() convenience function."""

    def test_calls_discover_and_wraps(self, tmp_path: Path) -> None:
        """load_dataset() returns a Dataset wrapping discover_sessions()."""
        mock_meta = SessionMeta(
            phase="p", animal_id="a-1F", sex="F", fov="FOV1",
            is_tracked=False, npy_paths=(tmp_path / "a.npy",),
            event_paths=(tmp_path / "a.mat",),
        )

        with patch("axplorer.dataset.discover_sessions", return_value=[mock_meta]):
            ds = load_dataset(tmp_path)

        assert isinstance(ds, Dataset)
        assert len(ds) == 1
        assert ds[0] is mock_meta
