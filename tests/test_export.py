"""Tests for axplorer.export modules."""

from io import BytesIO
from pathlib import Path

import h5py
import numpy as np
import plotly.graph_objects as go
import pytest

from axplorer.export.data import export_peth_csv, export_session_hdf5
from axplorer.export.figures import export_figure
from axplorer.types import PETHResult, SessionMetadata


# ──────────────────────────────────────────────────────────────────────────
# Test fixtures
# ──────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_peth() -> PETHResult:
    """Create a synthetic PETHResult for testing."""
    n_neurons, n_time, n_trials = 5, 100, 10
    rng = np.random.default_rng(42)
    windows = rng.normal(size=(n_trials, n_neurons, n_time)).astype(np.float32)
    mean = np.nanmean(windows, axis=0).astype(np.float32)
    sem = (np.nanstd(windows, axis=0) / np.sqrt(n_trials)).astype(np.float32)
    time_axis = np.linspace(-2, 5, n_time)

    return PETHResult(
        event_windows=windows,
        time_axis=time_axis,
        mean=mean,
        sem=sem,
        event_label="test_event",
        n_trials=n_trials,
        pre_event_s=2.0,
        post_event_s=5.0,
    )


@pytest.fixture()
def sample_metadata() -> SessionMetadata:
    """Create a synthetic SessionMetadata for testing."""
    return SessionMetadata(
        name="test_session",
        n_neurons=5,
        n_frames=1000,
        n_events=50,
        event_counts={"test_event": 10, "other_event": 40},
        effective_fps=7.5,
        duration_s=133.3,
        task_type="reacher",
    )


# ──────────────────────────────────────────────────────────────────────────
# Figure export tests
# ──────────────────────────────────────────────────────────────────────────

class TestExportFigure:
    """Tests for export_figure."""

    def test_returns_bytes(self):
        fig = go.Figure(data=go.Scatter(x=[1, 2], y=[3, 4]))
        result = export_figure(fig, fmt="png")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_write_to_file(self, tmp_path):
        fig = go.Figure(data=go.Scatter(x=[1, 2], y=[3, 4]))
        path = tmp_path / "test.png"
        result = export_figure(fig, path=path, fmt="png")
        assert result is None
        assert path.exists()
        assert path.stat().st_size > 0

    def test_svg_format(self):
        fig = go.Figure(data=go.Scatter(x=[1, 2], y=[3, 4]))
        result = export_figure(fig, fmt="svg")
        assert isinstance(result, bytes)
        assert b"<svg" in result

    def test_invalid_format(self):
        fig = go.Figure()
        with pytest.raises(ValueError, match="Unsupported format"):
            export_figure(fig, fmt="gif")


# ──────────────────────────────────────────────────────────────────────────
# CSV export tests
# ──────────────────────────────────────────────────────────────────────────

class TestExportPethCsv:
    """Tests for export_peth_csv."""

    def test_returns_string(self, sample_peth):
        csv_str = export_peth_csv(sample_peth)
        assert isinstance(csv_str, str)
        assert "time" in csv_str
        assert "cell_0_mean" in csv_str
        assert "cell_0_sem" in csv_str

    def test_correct_columns(self, sample_peth):
        csv_str = export_peth_csv(sample_peth)
        header = csv_str.split("\n")[0]
        cols = header.split(",")
        # time + (mean + sem) per neuron.
        assert len(cols) == 1 + 2 * sample_peth.mean.shape[0]

    def test_write_to_file(self, tmp_path, sample_peth):
        path = tmp_path / "peth.csv"
        result = export_peth_csv(sample_peth, path=path)
        assert result is None
        assert path.exists()


# ──────────────────────────────────────────────────────────────────────────
# HDF5 export tests
# ──────────────────────────────────────────────────────────────────────────

class TestExportSessionHdf5:
    """Tests for export_session_hdf5."""

    def test_returns_bytes(self, sample_metadata, sample_peth):
        result = export_session_hdf5(
            sample_metadata, {"test_event": sample_peth},
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_hdf5_structure(self, tmp_path, sample_metadata, sample_peth):
        path = tmp_path / "session.h5"
        export_session_hdf5(
            sample_metadata, {"test_event": sample_peth}, path=path,
        )

        with h5py.File(path, "r") as f:
            assert "metadata" in f
            assert f["metadata"].attrs["name"] == "test_session"
            assert f["metadata"].attrs["n_neurons"] == 5

            assert "events" in f
            assert "test_event" in f["events"]
            grp = f["events/test_event"]
            assert "mean" in grp
            assert "sem" in grp
            assert "windows" in grp
            assert "time_axis" in grp
            assert grp.attrs["n_trials"] == 10
