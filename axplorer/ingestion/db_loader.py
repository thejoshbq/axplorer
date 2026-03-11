"""DB-backed session loading for axplorer.

Provides :func:`load_db_hierarchy` which mirrors the filesystem loaders in
``api/state.py`` but reads ``DBSample`` objects from a pynapse DuckDB
database.

The returned hierarchy has the same shape as the filesystem loaders:
``{population_name: {subject_name: [SessionWrapper, ...]}, ...}``.
"""

from __future__ import annotations

import logging

from pynapse.db.engine import connect
from pynapse.db import query
from pynapse.db.hydrate import DBSample

from axplorer.alignment.session import SessionWrapper

logger = logging.getLogger(__name__)

_DEFAULT_POP = "default"
_DEFAULT_SAMPLE = "default"


def load_db_hierarchy(
    level: str,
    names: list[str],
    db_path: str | None = None,
) -> tuple[dict[str, dict[str, list[SessionWrapper]]], object]:
    """Load a DB-backed hierarchy at the given level, filtered by entity names.

    Creates a single DuckDB connection that is shared by all ``DBSample``
    instances so that lazy data access works after this function returns.
    On success the connection is returned alongside the hierarchy; the caller
    (typically :class:`api.state.DataStore`) is responsible for closing it
    when the data is no longer needed.  On exception the connection is closed
    before re-raising so no handles leak.

    Args:
        level: Data level -- one of ``"Project"``, ``"Population"``,
            ``"Sample"``, or ``"FOV"``.
        names: Entity names to load at the given level.
        db_path: Path to the pynapse DuckDB file.
            ``None`` → default ``~/.pynapse/pynapse.duckdb``.

    Returns:
        A ``(hierarchy, conn)`` tuple where *hierarchy* is
        ``{pop_name: {subject_name: [SessionWrapper, ...]}}`` and *conn* is
        the open DuckDB connection shared by all ``DBSample`` instances.

    Raises:
        ValueError: If *level* is not one of the four recognised values.
    """
    conn = connect(db_path)
    try:
        if level == "Project":
            hierarchy = _load_project(names, conn)
        elif level == "Population":
            hierarchy = _load_population(names, conn)
        elif level == "Sample":
            hierarchy = _load_sample(names, conn)
        elif level == "FOV":
            hierarchy = _load_fov(names, conn)
        else:
            raise ValueError(f"Unknown data_level: {level!r}")
        return hierarchy, conn
    except Exception:
        conn.close()
        raise


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fov_row_to_wrapper(fov_id: int, conn) -> SessionWrapper | None:
    """Wrap a single FOV (by id) in a SessionWrapper.  Logs and returns None on failure."""
    try:
        return SessionWrapper(DBSample(fov_id=fov_id, conn=conn))
    except Exception as exc:
        logger.warning("Failed to load FOV id=%d: %s", fov_id, exc)
        return None


def _load_project(
    names: list[str],
    conn,
) -> dict[str, dict[str, list[SessionWrapper]]]:
    projects_df = query.list_projects(conn)
    hierarchy: dict[str, dict[str, list[SessionWrapper]]] = {}
    for name in names:
        matched = projects_df[projects_df["name"] == name]
        if matched.empty:
            logger.warning("Project %r not found in database", name)
            continue
        project_id = int(matched.iloc[0]["id"])
        pops_df = query.list_populations(project_id=project_id, conn=conn)
        for _, pop_row in pops_df.iterrows():
            pop_name = str(pop_row["name"])
            pop_id = int(pop_row["id"])
            subjs_df = query.list_subjects(population_id=pop_id, conn=conn)
            for _, subj_row in subjs_df.iterrows():
                subj_name = str(subj_row["name"])
                subj_id = int(subj_row["id"])
                fovs_df = query.list_fovs(subject_id=subj_id, conn=conn)
                for _, fov_row in fovs_df.iterrows():
                    w = _fov_row_to_wrapper(int(fov_row["id"]), conn)
                    if w is not None:
                        (
                            hierarchy
                            .setdefault(pop_name, {})
                            .setdefault(subj_name, [])
                            .append(w)
                        )
    return hierarchy


def _load_population(
    names: list[str],
    conn,
) -> dict[str, dict[str, list[SessionWrapper]]]:
    pops_df = query.list_populations(conn=conn)
    hierarchy: dict[str, dict[str, list[SessionWrapper]]] = {}
    for name in names:
        matched = pops_df[pops_df["name"] == name]
        if matched.empty:
            logger.warning("Population %r not found in database", name)
            continue
        pop_id = int(matched.iloc[0]["id"])
        subjs_df = query.list_subjects(population_id=pop_id, conn=conn)
        for _, subj_row in subjs_df.iterrows():
            subj_name = str(subj_row["name"])
            subj_id = int(subj_row["id"])
            fovs_df = query.list_fovs(subject_id=subj_id, conn=conn)
            for _, fov_row in fovs_df.iterrows():
                w = _fov_row_to_wrapper(int(fov_row["id"]), conn)
                if w is not None:
                    (
                        hierarchy
                        .setdefault(name, {})
                        .setdefault(subj_name, [])
                        .append(w)
                    )
    return hierarchy


def _load_sample(
    names: list[str],
    conn,
) -> dict[str, dict[str, list[SessionWrapper]]]:
    subjs_df = query.list_subjects(conn=conn)
    hierarchy: dict[str, dict[str, list[SessionWrapper]]] = {}
    for name in names:
        matched = subjs_df[subjs_df["name"] == name]
        if matched.empty:
            logger.warning("Subject %r not found in database", name)
            continue
        subj_id = int(matched.iloc[0]["id"])
        fovs_df = query.list_fovs(subject_id=subj_id, conn=conn)
        for _, fov_row in fovs_df.iterrows():
            w = _fov_row_to_wrapper(int(fov_row["id"]), conn)
            if w is not None:
                (
                    hierarchy
                    .setdefault(_DEFAULT_POP, {})
                    .setdefault(name, [])
                    .append(w)
                )
    return hierarchy


def _load_fov(
    names: list[str],
    conn,
) -> dict[str, dict[str, list[SessionWrapper]]]:
    wrappers: list[SessionWrapper] = []
    for name in names:
        fov = query.get_fov(name=name, conn=conn)
        if fov is None:
            logger.warning("FOV %r not found in database", name)
            continue
        w = _fov_row_to_wrapper(int(fov["id"]), conn)
        if w is not None:
            wrappers.append(w)
    if wrappers:
        return {_DEFAULT_POP: {_DEFAULT_SAMPLE: wrappers}}
    return {}
