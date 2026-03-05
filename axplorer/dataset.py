"""Dataset — a collection of discovered sessions for batch analysis.

Provides filtering, lazy loading, and parallel batch processing over
:class:`~axplorer.types.SessionMeta` objects discovered by
:func:`~axplorer.ingestion.discovery.discover_sessions`.
"""

from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Callable, Iterator, TypeVar

import pandas as pd

from axplorer.ingestion.discovery import discover_sessions
from axplorer.types import Session, SessionMeta

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Dataset:
    """A collection of discovered sessions supporting filtering and batch processing."""

    def __init__(self, sessions: list[SessionMeta]) -> None:
        self._sessions = list(sessions)

    def __len__(self) -> int:
        return len(self._sessions)

    def __iter__(self) -> Iterator[SessionMeta]:
        return iter(self._sessions)

    def __getitem__(self, index: int) -> SessionMeta:
        return self._sessions[index]

    def __repr__(self) -> str:
        return f"Dataset({len(self._sessions)} sessions)"

    def filter(self, **kwargs: object) -> Dataset:
        """Return a new Dataset with only sessions matching all given criteria.

        Supports keyword arguments matching :class:`SessionMeta` fields:
        ``phase``, ``animal_id``, ``sex``, ``fov``, ``is_tracked``.
        String fields use case-sensitive equality. ``is_tracked`` uses
        boolean equality.

        Args:
            **kwargs: Field name/value pairs to match against.

        Returns:
            A new :class:`Dataset` containing only matching sessions.

        Raises:
            AttributeError: If a keyword doesn't match a SessionMeta field.

        Example::

            males = dataset.filter(sex="M")
            tracked_males = dataset.filter(sex="M", is_tracked=True)
        """
        filtered = self._sessions
        for key, value in kwargs.items():
            filtered = [s for s in filtered if getattr(s, key) == value]
        return Dataset(filtered)

    def load_session(
        self,
        session_meta: SessionMeta,
        fps: float = 30.0,
        frame_averaging: int = 4,
        task_type: str | None = None,
    ) -> Session:
        """Load a single SessionMeta into a full Session.

        Calls :func:`~axplorer.ingestion.loader.load_session_files` with
        the paths from *session_meta*, wraps the Sample in a
        :class:`~axplorer.alignment.session.SessionWrapper`, and returns
        a composed :class:`Session`.

        Args:
            session_meta: The session to load.
            fps: Raw imaging frame rate in Hz.
            frame_averaging: Number of raw frames binned per signal frame.
            task_type: Task type override (``None`` = auto-detect).

        Returns:
            A fully loaded :class:`Session` object.
        """
        from axplorer.alignment.session import SessionWrapper
        from axplorer.ingestion.loader import load_session_files

        sample, metadata = load_session_files(
            signal_path=list(session_meta.npy_paths),
            event_path=list(session_meta.mat_paths),
            fps=fps,
            frame_averaging=frame_averaging,
            task_type=task_type,
            session_name=session_meta.npy_paths[0].stem,
        )
        wrapper = SessionWrapper(sample)
        return Session(meta=session_meta, metadata=metadata, wrapper=wrapper)

    def process_all(
        self,
        fn: Callable[[Session], T],
        fps: float = 30.0,
        frame_averaging: int = 4,
        task_type: str | None = None,
        n_jobs: int = 1,
    ) -> list[T | None]:
        """Load each session and apply *fn*, optionally in parallel.

        Args:
            fn: Function receiving a loaded :class:`Session`, returning any
                value.
            fps: Frame rate passed to ``load_session_files()``.
            frame_averaging: Frame averaging passed to ``load_session_files()``.
            task_type: Task type override (``None`` = auto-detect per session).
            n_jobs: Number of parallel workers. ``1`` = sequential (default).
                Uses :class:`concurrent.futures.ProcessPoolExecutor` for
                ``n_jobs > 1``.

        Returns:
            List of *fn* results, one per session (order preserved).
            Failed sessions yield ``None`` with a warning logged.
        """
        if n_jobs <= 1:
            return self._process_sequential(fn, fps, frame_averaging, task_type)
        return self._process_parallel(fn, fps, frame_averaging, task_type, n_jobs)

    def to_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame summary of all sessions.

        Columns: ``phase``, ``animal_id``, ``sex``, ``fov``,
        ``is_tracked``, ``npy_paths``, ``mat_paths``, ``npy_size_mb``,
        ``mat_size_mb``.

        Returns:
            A :class:`pandas.DataFrame` with one row per session.
        """
        rows = []
        for s in self._sessions:
            npy_size = sum(
                p.stat().st_size / (1024 * 1024) for p in s.npy_paths if p.exists()
            )
            mat_size = sum(
                p.stat().st_size / (1024 * 1024) for p in s.mat_paths if p.exists()
            )
            rows.append({
                "phase": s.phase,
                "animal_id": s.animal_id,
                "sex": s.sex,
                "fov": s.fov,
                "is_tracked": s.is_tracked,
                "npy_paths": [str(p) for p in s.npy_paths],
                "mat_paths": [str(p) for p in s.mat_paths],
                "npy_size_mb": round(npy_size, 2),
                "mat_size_mb": round(mat_size, 2),
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_sequential(
        self,
        fn: Callable[[Session], T],
        fps: float,
        frame_averaging: int,
        task_type: str | None,
    ) -> list[T | None]:
        """Process all sessions sequentially."""
        results: list[T | None] = []
        for meta in self._sessions:
            try:
                session = self.load_session(meta, fps, frame_averaging, task_type)
                results.append(fn(session))
            except Exception as exc:
                logger.warning(
                    "Failed to process %s/%s/%s: %s",
                    meta.phase, meta.animal_id, meta.fov, exc,
                )
                results.append(None)
        return results

    def _process_parallel(
        self,
        fn: Callable[[Session], T],
        fps: float,
        frame_averaging: int,
        task_type: str | None,
        n_jobs: int,
    ) -> list[T | None]:
        """Process sessions in parallel using ProcessPoolExecutor."""
        results: list[T | None] = [None] * len(self._sessions)

        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            futures = {}
            for idx, meta in enumerate(self._sessions):
                future = executor.submit(
                    _worker_load_and_apply,
                    fn, meta, fps, frame_averaging, task_type,
                )
                futures[future] = idx

            for future in futures:
                idx = futures[future]
                meta = self._sessions[idx]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    logger.warning(
                        "Failed to process %s/%s/%s: %s",
                        meta.phase, meta.animal_id, meta.fov, exc,
                    )
        return results


def _worker_load_and_apply(
    fn: Callable[[Session], T],
    meta: SessionMeta,
    fps: float,
    frame_averaging: int,
    task_type: str | None,
) -> T:
    """Worker function for parallel processing — loads one session and applies *fn*."""
    from axplorer.alignment.session import SessionWrapper
    from axplorer.ingestion.loader import load_session_files

    sample, metadata = load_session_files(
        signal_path=list(meta.npy_paths),
        event_path=list(meta.mat_paths),
        fps=fps,
        frame_averaging=frame_averaging,
        task_type=task_type,
        session_name=meta.npy_paths[0].stem,
    )
    wrapper = SessionWrapper(sample)
    session = Session(meta=meta, metadata=metadata, wrapper=wrapper)
    return fn(session)


def load_dataset(root: str | Path) -> Dataset:
    """Discover all sessions under *root* and return a Dataset.

    Equivalent to ``Dataset(discover_sessions(root))``.

    Args:
        root: Path to the data root directory.

    Returns:
        A :class:`Dataset` containing all discovered sessions.
    """
    return Dataset(discover_sessions(root))


__all__ = ["Dataset", "load_dataset"]
