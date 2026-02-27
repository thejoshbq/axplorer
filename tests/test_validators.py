"""Tests for axplorer.ingestion.validators."""

from pathlib import Path

import numpy as np
import pytest

from axplorer.ingestion.validators import (
    ValidationResult,
    detect_task_type,
    validate_alignment,
    validate_event_file,
    validate_signal_file,
)


class TestValidateSignalFile:
    """Tests for validate_signal_file."""

    def test_valid_file(self, mock_signal_path):
        result = validate_signal_file(mock_signal_path)
        assert result.valid
        assert result.errors == []

    def test_missing_file(self, tmp_path):
        result = validate_signal_file(tmp_path / "nonexistent.npy")
        assert not result.valid
        assert any("not found" in e for e in result.errors)

    def test_wrong_extension(self, tmp_path):
        path = tmp_path / "data.csv"
        np.save(str(path).replace(".csv", ".npy"), np.zeros((3, 100)))
        path_csv = tmp_path / "data.csv"
        path_csv.write_text("not npy")
        result = validate_signal_file(path_csv)
        assert not result.valid

    def test_1d_array(self, bad_signal_1d):
        result = validate_signal_file(bad_signal_1d)
        assert not result.valid
        assert any("2-D" in e for e in result.errors)

    def test_nan_values(self, signal_with_nan):
        result = validate_signal_file(signal_with_nan)
        assert not result.valid
        assert any("NaN" in e for e in result.errors)

    def test_3d_singleton_squeezed(self, tmp_path):
        """(1, neurons, frames) array is accepted with a warning."""
        data = np.zeros((1, 5, 500), dtype=np.float32)
        path = tmp_path / "singleton.npy"
        np.save(path, data)
        result = validate_signal_file(path)
        assert result.valid
        assert len(result.warnings) == 1
        assert "squeezed" in result.warnings[0].lower()

    def test_3d_non_singleton_rejected(self, tmp_path):
        """(3, 5, 500) array is still rejected — not squeezable to 2D."""
        data = np.zeros((3, 5, 500), dtype=np.float32)
        path = tmp_path / "three_d.npy"
        np.save(path, data)
        result = validate_signal_file(path)
        assert not result.valid

    def test_transposed_array(self, tmp_path):
        """neurons > frames should fail the orientation check."""
        data = np.zeros((500, 10), dtype=np.float32)
        path = tmp_path / "transposed.npy"
        np.save(path, data)
        result = validate_signal_file(path)
        assert not result.valid
        assert any("transposed" in e.lower() for e in result.errors)


class TestValidateEventFile:
    """Tests for validate_event_file."""

    def test_valid_xlsx(self, mock_event_path):
        result = validate_event_file(mock_event_path)
        assert result.valid

    def test_missing_file(self, tmp_path):
        result = validate_event_file(tmp_path / "nonexistent.xlsx")
        assert not result.valid

    def test_missing_sheet(self, bad_event_xlsx):
        result = validate_event_file(bad_event_xlsx)
        assert not result.valid
        assert any("Behavior Data" in e for e in result.errors)

    def test_unsupported_extension(self, tmp_path):
        path = tmp_path / "events.json"
        path.write_text("{}")
        result = validate_event_file(path)
        assert not result.valid


class TestDetectTaskType:
    """Tests for detect_task_type."""

    def test_xlsx_returns_reacher(self, mock_event_path):
        assert detect_task_type(mock_event_path) == "reacher"

    def test_unsupported_extension(self, tmp_path):
        path = tmp_path / "events.csv"
        path.write_text("")
        with pytest.raises(ValueError, match="Cannot detect"):
            detect_task_type(path)


class TestValidateAlignment:
    """Tests for validate_alignment."""

    def test_perfect_alignment(self):
        result = validate_alignment(1250, 5000, 4)
        assert result.valid
        assert result.warnings == []

    def test_minor_mismatch(self):
        result = validate_alignment(1251, 5000, 4)
        assert result.valid
        assert len(result.warnings) == 1
        assert "Minor" in result.warnings[0]

    def test_severe_mismatch(self):
        result = validate_alignment(1200, 5000, 4)
        assert not result.valid
        assert any("Severe" in e for e in result.errors)
