"""Directory-based session discovery for batch ingestion.

Walks a hierarchical data directory of the form ``{phase}/{animal_id}/{fov}/``
and returns validated :class:`~axplorer.types.SessionMeta` objects for each
FOV that contains a valid signal/event file pair.
"""

from __future__ import annotations

import logging
from pathlib import Path

from axplorer.types import SessionMeta

logger = logging.getLogger(__name__)

_SKIP_DIRS = frozenset({"__MACOSX"})


def parse_animal_sex(animal_id: str) -> str:
    """Extract sex ('M' or 'F') from the trailing character of *animal_id*.

    Args:
        animal_id: Animal identifier string (e.g. ``"PrL-NAc-G6-1F"``).

    Returns:
        ``"M"`` or ``"F"``.

    Raises:
        ValueError: If the trailing character is not ``'M'`` or ``'F'``.
    """
    if not animal_id:
        raise ValueError("animal_id is empty")
    suffix = animal_id[-1].upper()
    if suffix not in ("M", "F"):
        raise ValueError(
            f"Cannot parse sex from animal_id '{animal_id}': "
            f"trailing character '{animal_id[-1]}' is not 'M' or 'F'"
        )
    return suffix


def discover_sessions(root: str | Path) -> list[SessionMeta]:
    """Walk a data directory and return SessionMeta for each valid FOV.

    Expects a three-level hierarchy::

        root/
          {phase}/
            {animal_id}/
              {fov}/
                *extractedsignals_raw.npy
                *.mat  (excluding *extractedsignals*)

    Args:
        root: Path to the data root directory.

    Returns:
        List of :class:`SessionMeta` objects sorted by
        ``(phase, animal_id, fov)``. Invalid FOVs are logged as warnings
        and skipped.

    Raises:
        ValueError: If *root* does not exist or is not a directory.
    """
    root = Path(root).expanduser().resolve()
    if not root.exists():
        raise ValueError(f"Root directory does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Root path is not a directory: {root}")

    sessions: list[SessionMeta] = []

    for phase_dir in _sorted_subdirs(root):
        for animal_dir in _sorted_subdirs(phase_dir):
            for fov_dir in _sorted_subdirs(animal_dir):
                try:
                    meta = _process_fov(
                        phase=phase_dir.name,
                        animal_id=animal_dir.name,
                        fov_dir=fov_dir,
                    )
                except _SkipFOV as exc:
                    logger.warning("Skipping %s: %s", fov_dir, exc)
                    continue
                except (PermissionError, OSError) as exc:
                    logger.warning("Skipping %s: %s", fov_dir, exc)
                    continue

                sessions.append(meta)

    sessions.sort(key=lambda m: (m.phase, m.animal_id, m.fov))
    logger.info("Discovered %d sessions in %s", len(sessions), root)
    return sessions


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

class _SkipFOV(Exception):
    """Raised internally to skip a FOV with a reason message."""


def _is_hidden_or_skip(name: str) -> bool:
    """Return True if *name* should be skipped (hidden or in skip list)."""
    return name.startswith(".") or name in _SKIP_DIRS


def _sorted_subdirs(parent: Path) -> list[Path]:
    """Return sorted child directories of *parent*, excluding hidden/skip."""
    try:
        children = sorted(parent.iterdir())
    except (PermissionError, OSError) as exc:
        logger.warning("Cannot read %s: %s", parent, exc)
        return []
    return [
        p for p in children
        if p.is_dir() and not _is_hidden_or_skip(p.name)
    ]


def _process_fov(phase: str, animal_id: str, fov_dir: Path) -> SessionMeta:
    """Validate a single FOV directory and return its SessionMeta.

    Event-file discovery prefers REACHER-exported CSVs, then falls back to the
    legacy MATLAB (.mat) and XLSX formats so archived FOVs still load.

    Raises:
        _SkipFOV: If the directory doesn't contain a valid file pair.
    """
    # Find signal files: legacy *extractedsignals_raw.npy, falling back to a
    # roigbiv *.h5 trace export (no fixed suffix convention there).
    npy_files = sorted(fov_dir.glob("*extractedsignals_raw.npy"))
    if not npy_files:
        npy_files = sorted(fov_dir.glob("*.h5"))
    logger.debug("FOV %s: found %d signal files", fov_dir, len(npy_files))

    if len(npy_files) == 0:
        raise _SkipFOV("no *extractedsignals_raw.npy or *.h5 signal file found")

    # Find event files: prefer REACHER CSV, fall back to MAT then XLSX.
    event_files = sorted(fov_dir.glob("behavior_events*.csv"))
    if not event_files:
        event_files = sorted(
            f for f in fov_dir.glob("*.mat")
            if "extractedsignals" not in f.name.lower()
        )
    if not event_files:
        event_files = sorted(fov_dir.glob("*.xlsx"))
    logger.debug("FOV %s: found %d event files", fov_dir, len(event_files))

    if not event_files:
        raise _SkipFOV("no behavior event file (.csv, .mat, or .xlsx) found")

    # Optional REACHER companion — forwarded to pynapse when present.
    ft_file = fov_dir / "frame_timestamps.csv"
    frame_timestamps_path: Path | None = ft_file.resolve() if ft_file.exists() else None

    # Normalize FOV name: strip internal whitespace.
    raw_fov = fov_dir.name
    normalized_fov = raw_fov.replace(" ", "")

    # Parse sex from animal_id.
    try:
        sex = parse_animal_sex(animal_id)
    except ValueError as exc:
        raise _SkipFOV(str(exc)) from exc

    return SessionMeta(
        phase=phase,
        animal_id=animal_id,
        sex=sex,
        fov=normalized_fov,
        is_tracked="_tracked" in normalized_fov.lower(),
        npy_paths=tuple(f.resolve() for f in npy_files),
        event_paths=tuple(f.resolve() for f in event_files),
        frame_timestamps_path=frame_timestamps_path,
    )


__all__ = ["discover_sessions", "parse_animal_sex"]
