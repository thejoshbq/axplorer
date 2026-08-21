"""Tests for api.routers.browse."""

from __future__ import annotations

import pytest

from api.routers import browse as browse_module


@pytest.fixture()
def home(tmp_path, monkeypatch):
    """Restrict the browse endpoint's home-directory guard to tmp_path."""
    monkeypatch.setattr(browse_module, "_HOME", tmp_path)
    return tmp_path


class TestBrowseTypeMap:
    """Tests for file-type recognition in GET /api/browse."""

    def test_recognizes_h5_and_csv(self, home):
        (home / "trace.h5").write_bytes(b"")
        (home / "events.csv").write_text("device,event\n")
        (home / "legacy.mat").write_bytes(b"")

        res = browse_module.browse(str(home))
        types = {e.name: e.type for e in res.entries}

        assert types["trace.h5"] == "h5"
        assert types["events.csv"] == "csv"
        assert types["legacy.mat"] == "mat"

    def test_h5_and_csv_are_not_generic_file_type(self, home):
        (home / "trace.h5").write_bytes(b"")
        (home / "events.csv").write_text("device,event\n")

        res = browse_module.browse(str(home))
        for entry in res.entries:
            assert entry.type != "file"
