"""Tests for axplorer.ingestion.discovery — directory walking and validation."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pytest

from axplorer.ingestion.discovery import discover_sessions, parse_animal_sex


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def _make_fov(
    fov_dir: Path,
    npy_name: str = "signals_extractedsignals_raw.npy",
    mat_name: str = "events.mat",
    create_npy: bool = True,
    create_mat: bool = True,
    extra_npy: str | None = None,
    extra_mat: str | None = None,
) -> None:
    """Populate a FOV directory with synthetic signal/event files."""
    fov_dir.mkdir(parents=True, exist_ok=True)
    if create_npy:
        np.save(fov_dir / npy_name, np.zeros((5, 100), dtype=np.float32))
    if create_mat:
        # Create a minimal .mat-like file (just needs to exist for discovery).
        (fov_dir / mat_name).write_bytes(b"\x00" * 128)
    if extra_npy:
        np.save(fov_dir / extra_npy, np.zeros((5, 100), dtype=np.float32))
    if extra_mat:
        (fov_dir / extra_mat).write_bytes(b"\x00" * 128)


# ──────────────────────────────────────────────────────────────────────────
# TestDiscoverSessions
# ──────────────────────────────────────────────────────────────────────────

class TestDiscoverSessions:
    """Tests for discover_sessions()."""

    def test_valid_hierarchy(self, tmp_path: Path) -> None:
        """A well-formed 3-level tree yields correct SessionMeta objects."""
        _make_fov(tmp_path / "0 EarlyAcq" / "PrL-NAc-G6-1F" / "FOV1_tracked")
        _make_fov(tmp_path / "0 EarlyAcq" / "PrL-NAc-G6-2M" / "FOV2")

        result = discover_sessions(tmp_path)

        assert len(result) == 2

        # Sorted by (phase, animal_id, fov).
        m0 = result[0]
        assert m0.phase == "0 EarlyAcq"
        assert m0.animal_id == "PrL-NAc-G6-1F"
        assert m0.sex == "F"
        assert m0.fov == "FOV1_tracked"
        assert m0.is_tracked is True
        assert m0.npy_paths[0].name == "signals_extractedsignals_raw.npy"
        assert m0.event_paths[0].name == "events.mat"

        m1 = result[1]
        assert m1.animal_id == "PrL-NAc-G6-2M"
        assert m1.sex == "M"
        assert m1.fov == "FOV2"
        assert m1.is_tracked is False

    def test_missing_npy(self, tmp_path: Path, caplog) -> None:
        """FOV with only a .mat file is skipped with a warning."""
        _make_fov(
            tmp_path / "phase" / "animal-1F" / "FOV1",
            create_npy=False,
        )

        with caplog.at_level(logging.WARNING):
            result = discover_sessions(tmp_path)

        assert len(result) == 0
        assert "no *extractedsignals_raw.npy" in caplog.text

    def test_missing_mat(self, tmp_path: Path, caplog) -> None:
        """FOV with only a .npy file is skipped with a warning."""
        _make_fov(
            tmp_path / "phase" / "animal-1M" / "FOV1",
            create_mat=False,
        )

        with caplog.at_level(logging.WARNING):
            result = discover_sessions(tmp_path)

        assert len(result) == 0
        assert "no behavior event file" in caplog.text

    def test_multiple_npy(self, tmp_path: Path) -> None:
        """FOV with two .npy files collects both into npy_paths."""
        _make_fov(
            tmp_path / "phase" / "animal-1F" / "FOV1",
            extra_npy="other_extractedsignals_raw.npy",
        )

        result = discover_sessions(tmp_path)

        assert len(result) == 1
        assert len(result[0].npy_paths) == 2

    def test_normalized_fov_whitespace(self, tmp_path: Path) -> None:
        """Whitespace in FOV directory name is stripped."""
        _make_fov(tmp_path / "phase" / "animal-1F" / "FOV1 _tracked")

        result = discover_sessions(tmp_path)

        assert len(result) == 1
        assert result[0].fov == "FOV1_tracked"
        assert result[0].is_tracked is True

    def test_hidden_files_ignored(self, tmp_path: Path) -> None:
        """.DS_Store and __MACOSX directories are ignored."""
        # Create valid FOV.
        _make_fov(tmp_path / "phase" / "animal-1F" / "FOV1")
        # Create hidden/skip dirs at various levels.
        (tmp_path / ".DS_Store").mkdir()
        (tmp_path / "phase" / "__MACOSX").mkdir()

        result = discover_sessions(tmp_path)
        assert len(result) == 1

    def test_empty_root(self, tmp_path: Path) -> None:
        """Empty root directory returns an empty list."""
        result = discover_sessions(tmp_path)
        assert result == []

    def test_nonexistent_root(self) -> None:
        """Non-existent root raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            discover_sessions("/no/such/path/abcxyz123")

    def test_mat_with_extractedsignals_excluded(self, tmp_path: Path) -> None:
        """A .mat file containing 'extractedsignals' in its name is excluded."""
        fov = tmp_path / "phase" / "animal-1M" / "FOV1"
        _make_fov(fov)
        # Add a .mat with "extractedsignals" in the name — should be ignored.
        (fov / "data_extractedsignals.mat").write_bytes(b"\x00" * 64)

        result = discover_sessions(tmp_path)
        assert len(result) == 1
        assert result[0].event_paths[0].name == "events.mat"

    def test_csv_event_preferred(self, tmp_path: Path) -> None:
        """A REACHER behavior_events.csv is preferred over a legacy .mat sibling."""
        fov = tmp_path / "phase" / "animal-1F" / "FOV1"
        _make_fov(fov)
        (fov / "behavior_events.csv").write_text(
            "device,event,start_timestamp,end_timestamp\nPUMP,INFUSION,0,1\n"
        )

        result = discover_sessions(tmp_path)
        assert len(result) == 1
        assert result[0].event_paths[0].name == "behavior_events.csv"
        assert result[0].frame_timestamps_path is None

    def test_frame_timestamps_sidecar_discovered(self, tmp_path: Path) -> None:
        """frame_timestamps.csv next to a CSV event file lands on SessionMeta."""
        fov = tmp_path / "phase" / "animal-1F" / "FOV1"
        _make_fov(fov, create_mat=False)
        (fov / "behavior_events.csv").write_text(
            "device,event,start_timestamp,end_timestamp\nPUMP,INFUSION,0,1\n"
        )
        (fov / "frame_timestamps.csv").write_text("frame_index,timestamp_ms\n0,0\n")

        result = discover_sessions(tmp_path)
        assert len(result) == 1
        assert result[0].frame_timestamps_path is not None
        assert result[0].frame_timestamps_path.name == "frame_timestamps.csv"


# ──────────────────────────────────────────────────────────────────────────
# TestParseAnimalSex
# ──────────────────────────────────────────────────────────────────────────

class TestParseAnimalSex:
    """Tests for parse_animal_sex()."""

    def test_female(self) -> None:
        assert parse_animal_sex("PrL-NAc-G6-1F") == "F"

    def test_male(self) -> None:
        assert parse_animal_sex("PrL-NAc-G6-11M") == "M"

    def test_lowercase_accepted(self) -> None:
        assert parse_animal_sex("animal-1f") == "F"

    def test_invalid_suffix(self) -> None:
        with pytest.raises(ValueError, match="not 'M' or 'F'"):
            parse_animal_sex("PrL-NAc-G6-1X")

    def test_empty_string(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_animal_sex("")
