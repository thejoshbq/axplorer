"""DataStore -- central state for data hierarchy and loaded sessions."""

from __future__ import annotations

import logging
from pathlib import Path

from axplorer.alignment.session import SessionWrapper
from axplorer.ingestion.db_loader import load_db_hierarchy
from axplorer.ingestion.discovery import discover_sessions, parse_animal_sex
from axplorer.ingestion.loader import load_session_files

logger = logging.getLogger(__name__)

_DEFAULT_POP = "default"
_DEFAULT_SAMPLE = "default"


class DataStore:
    """Holds the loaded data hierarchy and exposes it to the API."""

    def __init__(self) -> None:
        self.data_level: str = "Project"
        self.data_paths: list[str] = []
        self.source: str = "filesystem"
        self.db_path: str | None = None
        self.hierarchy: dict[str, dict[str, list[SessionWrapper]]] = {}
        self.all_wrappers: list[SessionWrapper] = []
        self.available_events: list[str] = []
        self.status: str = "No data loaded."
        self.loading: bool = False
        self._db_conn = None  # open DuckDB connection shared by DBSample instances

    def load_data(self) -> None:
        """Load data according to source, data_level, and data_paths."""
        if not self.data_paths:
            self.status = "No paths provided."
            return

        # Close any open DB connection from a previous database load.
        if self._db_conn is not None:
            try:
                self._db_conn.close()
            except Exception:
                pass
            self._db_conn = None

        self.loading = True
        self.status = "Loading..."
        hierarchy: dict[str, dict[str, list[SessionWrapper]]] = {}

        try:
            if self.source == "database":
                hierarchy, self._db_conn = load_db_hierarchy(
                    self.data_level, self.data_paths, self.db_path
                )
            else:
                level = self.data_level
                if level == "Project":
                    hierarchy = self._load_project(self.data_paths[0])
                elif level == "Population":
                    for p in self.data_paths:
                        h = self._load_population(p)
                        for pop, samples in h.items():
                            hierarchy.setdefault(pop, {}).update(samples)
                elif level == "Sample":
                    for p in self.data_paths:
                        h = self._load_sample(p)
                        for pop, samples in h.items():
                            hierarchy.setdefault(pop, {}).update(samples)
                elif level == "FOV":
                    wrappers = []
                    for p in self.data_paths:
                        w = self._load_fov(p)
                        if w is not None:
                            wrappers.append(w)
                    if wrappers:
                        hierarchy[_DEFAULT_POP] = {_DEFAULT_SAMPLE: wrappers}
        except Exception as exc:
            self.status = f"Error: {exc}"
            self.loading = False
            logger.exception("Failed to load data")
            return

        flat: list[SessionWrapper] = []
        for samples in hierarchy.values():
            for ws in samples.values():
                flat.extend(ws)

        if not flat:
            self.status = "No valid sessions found."
            self.loading = False
            return

        # Compute available events as intersection across all wrappers.
        event_sets = [set(w.get_event_labels()) for w in flat]
        common = sorted(set.intersection(*event_sets)) if event_sets else []

        self.hierarchy = hierarchy
        self.all_wrappers = flat
        self.available_events = common
        self.status = f"Loaded {len(flat)} FOV(s) across {len(hierarchy)} population(s)."
        self.loading = False

    # ------------------------------------------------------------------
    # Level-specific loaders
    # ------------------------------------------------------------------

    def _load_project(self, root_path: str) -> dict[str, dict[str, list[SessionWrapper]]]:
        """Load a full project directory using discover_sessions."""
        metas = discover_sessions(root_path)
        hierarchy: dict[str, dict[str, list[SessionWrapper]]] = {}
        for meta in metas:
            wrapper = self._meta_to_wrapper(meta)
            if wrapper is not None:
                hierarchy.setdefault(meta.phase, {}).setdefault(meta.animal_id, []).append(wrapper)
        return hierarchy

    def _load_population(self, pop_path: str) -> dict[str, dict[str, list[SessionWrapper]]]:
        """Each path is a population dir containing sample subdirs."""
        pop_dir = Path(pop_path).expanduser().resolve()
        pop_name = pop_dir.name
        hierarchy: dict[str, dict[str, list[SessionWrapper]]] = {}
        for sample_dir in sorted(pop_dir.iterdir()):
            if not sample_dir.is_dir() or sample_dir.name.startswith("."):
                continue
            wrappers = self._load_sample_dir(sample_dir)
            if wrappers:
                hierarchy.setdefault(pop_name, {})[sample_dir.name] = wrappers
        return hierarchy

    def _load_sample(self, sample_path: str) -> dict[str, dict[str, list[SessionWrapper]]]:
        """Each path is a sample dir containing FOV subdirs."""
        sample_dir = Path(sample_path).expanduser().resolve()
        wrappers = self._load_sample_dir(sample_dir)
        if wrappers:
            return {_DEFAULT_POP: {sample_dir.name: wrappers}}
        return {}

    def _load_sample_dir(self, sample_dir: Path) -> list[SessionWrapper]:
        """Load all FOV subdirectories under a sample directory."""
        wrappers: list[SessionWrapper] = []
        for fov_dir in sorted(sample_dir.iterdir()):
            if not fov_dir.is_dir() or fov_dir.name.startswith("."):
                continue
            w = self._load_fov(str(fov_dir))
            if w is not None:
                wrappers.append(w)
        return wrappers

    def _load_fov(self, fov_path: str) -> SessionWrapper | None:
        """Load a single FOV directory into a SessionWrapper."""
        fov_dir = Path(fov_path).expanduser().resolve()
        npy_files = sorted(fov_dir.glob("*extractedsignals_raw.npy"))
        mat_files = sorted(
            f for f in fov_dir.glob("*.mat")
            if "extractedsignals" not in f.name.lower()
        )
        xlsx_files = sorted(fov_dir.glob("*.xlsx"))
        event_files = mat_files + xlsx_files
        if not npy_files or not event_files:
            logger.warning("Skipping %s: missing .npy or event files", fov_dir)
            return None
        try:
            sample, _ = load_session_files(
                signal_path=[str(p) for p in npy_files] if len(npy_files) > 1 else str(npy_files[0]),
                event_path=[str(p) for p in event_files] if len(event_files) > 1 else str(event_files[0]),
                session_name=fov_dir.name,
            )
            return SessionWrapper(sample)
        except Exception as exc:
            logger.warning("Failed to load FOV %s: %s", fov_dir, exc)
            return None

    def _meta_to_wrapper(self, meta) -> SessionWrapper | None:
        """Convert a SessionMeta to a SessionWrapper."""
        try:
            sample, _ = load_session_files(
                signal_path=list(meta.npy_paths),
                event_path=list(meta.mat_paths),
                session_name=meta.npy_paths[0].stem,
            )
            return SessionWrapper(sample)
        except Exception as exc:
            logger.warning(
                "Failed to load %s/%s/%s: %s",
                meta.phase, meta.animal_id, meta.fov, exc,
            )
            return None
