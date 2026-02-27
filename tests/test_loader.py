"""Tests for axplorer.ingestion.loader."""

from pathlib import Path

import pytest

from axplorer.ingestion.loader import LoadError, load_session_files
from axplorer.types import SessionMetadata


class TestLoadSessionFiles:
    """Tests for load_session_files."""

    def test_successful_load(self, mock_signal_path, mock_event_path):
        sample, meta = load_session_files(
            signal_path=mock_signal_path,
            event_path=mock_event_path,
            fps=30.0,
            frame_averaging=4,
            task_type="reacher",
        )
        assert meta.n_neurons == 10
        assert meta.task_type == "reacher"
        assert isinstance(meta, SessionMetadata)
        assert meta.effective_fps == pytest.approx(30.0 / 4)
        assert meta.n_events > 0

    def test_auto_detect_task_type(self, mock_signal_path, mock_event_path):
        _, meta = load_session_files(
            signal_path=mock_signal_path,
            event_path=mock_event_path,
            fps=30.0,
            frame_averaging=4,
        )
        assert meta.task_type == "reacher"

    def test_missing_signal_raises(self, tmp_path, mock_event_path):
        with pytest.raises(LoadError) as exc_info:
            load_session_files(
                signal_path=tmp_path / "missing.npy",
                event_path=mock_event_path,
            )
        assert len(exc_info.value.errors) > 0

    def test_missing_event_raises(self, mock_signal_path, tmp_path):
        with pytest.raises(LoadError) as exc_info:
            load_session_files(
                signal_path=mock_signal_path,
                event_path=tmp_path / "missing.xlsx",
            )
        assert len(exc_info.value.errors) > 0

    def test_unknown_task_type_raises(self, mock_signal_path, mock_event_path):
        with pytest.raises(LoadError, match="Unknown task_type"):
            load_session_files(
                signal_path=mock_signal_path,
                event_path=mock_event_path,
                task_type="nonexistent",
            )

    def test_event_counts_exclude_frame_trigger(self, mock_signal_path, mock_event_path):
        _, meta = load_session_files(
            signal_path=mock_signal_path,
            event_path=mock_event_path,
            task_type="reacher",
        )
        assert "frame_trigger" not in meta.event_counts

    def test_session_name_default(self, mock_signal_path, mock_event_path):
        _, meta = load_session_files(
            signal_path=mock_signal_path,
            event_path=mock_event_path,
            task_type="reacher",
        )
        assert meta.name == mock_signal_path.stem

    def test_session_name_override(self, mock_signal_path, mock_event_path):
        _, meta = load_session_files(
            signal_path=mock_signal_path,
            event_path=mock_event_path,
            task_type="reacher",
            session_name="custom_name",
        )
        assert meta.name == "custom_name"
