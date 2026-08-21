"""Tests for axplorer.ingestion.detection — path type auto-detection."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from axplorer.ingestion.detection import (
    InputType,
    classify_paths,
    detect_input_type,
)


class TestDetectInputType:
    """Tests for detect_input_type()."""

    def test_npy_file(self, mock_signal_path: Path) -> None:
        assert detect_input_type(mock_signal_path) == InputType.SIGNAL_FILE

    def test_h5_file(self, mock_h5_signal_path: Path) -> None:
        assert detect_input_type(mock_h5_signal_path) == InputType.SIGNAL_FILE

    def test_event_csv_file(self, mock_h5_event_path: Path) -> None:
        assert detect_input_type(mock_h5_event_path) == InputType.EVENT_FILE

    def test_fov_dir_with_h5_signal(self, tmp_path: Path) -> None:
        """A FOV dir containing only .h5 + event files is recognized."""
        fov_dir = tmp_path / "FOV1"
        fov_dir.mkdir()
        import pandas as pd

        with pd.HDFStore(str(fov_dir / "traces.h5"), mode="w") as store:
            store.put("/f", pd.DataFrame(np.zeros((10, 3))), format="table")
        (fov_dir / "behavior_events.csv").write_text(
            "device,event,start_timestamp,end_timestamp\n"
        )
        assert detect_input_type(fov_dir) == InputType.FOV_DIR

    def test_unknown_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "data.json"
        path.write_text("{}")
        assert detect_input_type(path) == InputType.UNKNOWN


class TestClassifyPaths:
    """Tests for classify_paths()."""

    def test_h5_and_event_pair(self, mock_h5_signal_path: Path, mock_h5_event_path: Path) -> None:
        source, level = classify_paths([str(mock_h5_signal_path), str(mock_h5_event_path)])
        assert source == "filesystem"
        assert level == "Files"

    def test_empty_paths_raises(self) -> None:
        with pytest.raises(ValueError):
            classify_paths([])
