"""Tests for axplorer.ingestion.db_loader."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, call
import pandas as pd
import pytest

from axplorer.ingestion.db_loader import (
    load_db_hierarchy,
    _DEFAULT_POP,
    _DEFAULT_SAMPLE,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _make_fov_df(fov_ids: list[int]) -> pd.DataFrame:
    return _make_df([{"id": i, "name": f"fov_{i}"} for i in fov_ids])


def _make_session_wrapper(name: str = "fov") -> MagicMock:
    w = MagicMock()
    w.name = name
    return w


# ---------------------------------------------------------------------------
# Patch targets
# ---------------------------------------------------------------------------

_CONNECT = "axplorer.ingestion.db_loader.connect"
_QUERY = "axplorer.ingestion.db_loader.query"
_DBSAMPLE = "axplorer.ingestion.db_loader.DBSample"
_SESSION_WRAPPER = "axplorer.ingestion.db_loader.SessionWrapper"


# ---------------------------------------------------------------------------
# Helper: build a complete mock query module
# ---------------------------------------------------------------------------

def _query_mock(
    projects=None,
    populations=None,
    subjects=None,
    fovs=None,
    fov_by_name=None,
):
    q = MagicMock()
    q.list_projects.return_value = _make_df(projects or [])
    q.list_populations.return_value = _make_df(populations or [])
    q.list_subjects.return_value = _make_df(subjects or [])
    q.list_fovs.return_value = _make_df(fovs or [])
    q.get_fov.return_value = fov_by_name
    return q


# ===========================================================================
# FOV level
# ===========================================================================

class TestLoadDbHierarchyFov:
    def test_single_fov_found(self):
        mock_conn = MagicMock()
        mock_wrapper = _make_session_wrapper("fov_1")

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
            patch(_DBSAMPLE) as MockDBSample,
            patch(_SESSION_WRAPPER, return_value=mock_wrapper),
        ):
            q.get_fov.return_value = {"id": 1, "name": "fov_1"}

            hierarchy, conn = load_db_hierarchy("FOV", ["fov_1"])

        assert conn is mock_conn
        assert _DEFAULT_POP in hierarchy
        assert _DEFAULT_SAMPLE in hierarchy[_DEFAULT_POP]
        assert hierarchy[_DEFAULT_POP][_DEFAULT_SAMPLE] == [mock_wrapper]

    def test_fov_not_found_warns(self, caplog):
        mock_conn = MagicMock()

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
        ):
            q.get_fov.return_value = None
            import logging
            with caplog.at_level(logging.WARNING, logger="axplorer.ingestion.db_loader"):
                hierarchy, conn = load_db_hierarchy("FOV", ["missing_fov"])

        assert hierarchy == {}
        assert "missing_fov" in caplog.text

    def test_multiple_fovs(self):
        mock_conn = MagicMock()
        wrappers = [_make_session_wrapper(f"fov_{i}") for i in range(3)]

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
            patch(_DBSAMPLE),
            patch(_SESSION_WRAPPER, side_effect=wrappers),
        ):
            q.get_fov.side_effect = [
                {"id": i, "name": f"fov_{i}"} for i in range(3)
            ]

            hierarchy, conn = load_db_hierarchy("FOV", ["fov_0", "fov_1", "fov_2"])

        assert len(hierarchy[_DEFAULT_POP][_DEFAULT_SAMPLE]) == 3


# ===========================================================================
# Sample level
# ===========================================================================

class TestLoadDbHierarchySample:
    def test_subject_found(self):
        mock_conn = MagicMock()
        mock_wrapper = _make_session_wrapper("fov_10")

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
            patch(_DBSAMPLE),
            patch(_SESSION_WRAPPER, return_value=mock_wrapper),
        ):
            q.list_subjects.return_value = _make_df([{"id": 5, "name": "subj_A"}])
            q.list_fovs.return_value = _make_df([{"id": 10, "name": "fov_10"}])

            hierarchy, conn = load_db_hierarchy("Sample", ["subj_A"])

        assert _DEFAULT_POP in hierarchy
        assert "subj_A" in hierarchy[_DEFAULT_POP]
        assert hierarchy[_DEFAULT_POP]["subj_A"] == [mock_wrapper]

    def test_subject_not_found_warns(self, caplog):
        mock_conn = MagicMock()

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
        ):
            q.list_subjects.return_value = pd.DataFrame(columns=["id", "name"])
            import logging
            with caplog.at_level(logging.WARNING, logger="axplorer.ingestion.db_loader"):
                hierarchy, _ = load_db_hierarchy("Sample", ["ghost"])

        assert hierarchy == {}
        assert "ghost" in caplog.text


# ===========================================================================
# Population level
# ===========================================================================

class TestLoadDbHierarchyPopulation:
    def test_population_found(self):
        mock_conn = MagicMock()
        mock_wrapper = _make_session_wrapper("fov_20")

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
            patch(_DBSAMPLE),
            patch(_SESSION_WRAPPER, return_value=mock_wrapper),
        ):
            q.list_populations.return_value = _make_df([{"id": 3, "name": "pop_X"}])
            q.list_subjects.return_value = _make_df([{"id": 7, "name": "subj_B"}])
            q.list_fovs.return_value = _make_df([{"id": 20, "name": "fov_20"}])

            hierarchy, conn = load_db_hierarchy("Population", ["pop_X"])

        assert "pop_X" in hierarchy
        assert "subj_B" in hierarchy["pop_X"]
        assert hierarchy["pop_X"]["subj_B"] == [mock_wrapper]

    def test_population_not_found_warns(self, caplog):
        mock_conn = MagicMock()

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
        ):
            q.list_populations.return_value = pd.DataFrame(columns=["id", "name"])
            import logging
            with caplog.at_level(logging.WARNING, logger="axplorer.ingestion.db_loader"):
                hierarchy, _ = load_db_hierarchy("Population", ["nowhere"])

        assert hierarchy == {}
        assert "nowhere" in caplog.text


# ===========================================================================
# Project level
# ===========================================================================

class TestLoadDbHierarchyProject:
    def test_project_found(self):
        mock_conn = MagicMock()
        mock_wrapper = _make_session_wrapper("fov_30")

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
            patch(_DBSAMPLE),
            patch(_SESSION_WRAPPER, return_value=mock_wrapper),
        ):
            q.list_projects.return_value = _make_df([{"id": 1, "name": "proj_Z"}])
            q.list_populations.return_value = _make_df([{"id": 2, "name": "pop_Y"}])
            q.list_subjects.return_value = _make_df([{"id": 4, "name": "subj_C"}])
            q.list_fovs.return_value = _make_df([{"id": 30, "name": "fov_30"}])

            hierarchy, conn = load_db_hierarchy("Project", ["proj_Z"])

        assert "pop_Y" in hierarchy
        assert "subj_C" in hierarchy["pop_Y"]
        assert hierarchy["pop_Y"]["subj_C"] == [mock_wrapper]

    def test_project_not_found_warns(self, caplog):
        mock_conn = MagicMock()

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
        ):
            q.list_projects.return_value = pd.DataFrame(columns=["id", "name"])
            import logging
            with caplog.at_level(logging.WARNING, logger="axplorer.ingestion.db_loader"):
                hierarchy, _ = load_db_hierarchy("Project", ["phantom"])

        assert hierarchy == {}
        assert "phantom" in caplog.text


# ===========================================================================
# Error handling
# ===========================================================================

class TestLoadDbHierarchyErrorHandling:
    def test_unknown_level_raises(self):
        mock_conn = MagicMock()

        with patch(_CONNECT, return_value=mock_conn):
            with pytest.raises(ValueError, match="Unknown data_level"):
                load_db_hierarchy("Galaxy", ["x"])

        # Connection must be closed when exception is raised
        mock_conn.close.assert_called_once()

    def test_connection_closed_on_query_exception(self):
        mock_conn = MagicMock()

        with patch(_CONNECT, return_value=mock_conn), patch(_QUERY) as q:
            q.list_projects.side_effect = RuntimeError("db error")

            with pytest.raises(RuntimeError):
                load_db_hierarchy("Project", ["any"])

        mock_conn.close.assert_called_once()

    def test_connection_not_closed_on_success(self):
        """On success the conn is returned open; caller manages lifecycle."""
        mock_conn = MagicMock()

        with (
            patch(_CONNECT, return_value=mock_conn),
            patch(_QUERY) as q,
        ):
            q.get_fov.return_value = None  # nothing found, but no error

            _, conn = load_db_hierarchy("FOV", ["missing"])

        mock_conn.close.assert_not_called()
        assert conn is mock_conn
