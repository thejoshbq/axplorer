"""Path type auto-detection for Axplorer data uploads."""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class InputType(str, Enum):
    DUCKDB = "duckdb"
    PROJECT_DIR = "project"
    POPULATION_DIR = "population"
    SAMPLE_DIR = "sample"
    FOV_DIR = "fov"
    SIGNAL_FILE = "signal_file"
    EVENT_FILE = "event_file"
    UNKNOWN = "unknown"


def _is_fov_dir(d: Path) -> bool:
    """Check if a directory looks like a FOV directory."""
    has_signal = any(d.glob("*extractedsignals_raw.npy")) or any(d.glob("*.h5"))
    has_events = (
        any(d.glob("behavior_events*.csv"))
        or any(d.glob("*.mat"))
        or any(d.glob("*.xlsx"))
    )
    return has_signal and has_events


def _first_visible_subdir(d: Path) -> Path | None:
    """Return the first non-hidden subdirectory, or None."""
    for child in sorted(d.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            return child
    return None


def detect_input_type(path: str | Path) -> InputType:
    """Classify a single path by examining its contents.

    Args:
        path: Filesystem path to classify.

    Returns:
        The detected ``InputType``.
    """
    p = Path(path).expanduser().resolve()

    if p.is_file():
        ext = p.suffix.lower()
        if ext == ".duckdb":
            return InputType.DUCKDB
        if ext in (".npy", ".h5", ".hdf5"):
            return InputType.SIGNAL_FILE
        if ext in (".mat", ".xlsx", ".csv"):
            return InputType.EVENT_FILE
        return InputType.UNKNOWN

    if not p.is_dir():
        return InputType.UNKNOWN

    # Check if this directory itself is a FOV dir.
    if _is_fov_dir(p):
        return InputType.FOV_DIR

    # Probe first non-hidden subdirectory (up to 3 levels).
    child = _first_visible_subdir(p)
    if child is None:
        return InputType.UNKNOWN

    if _is_fov_dir(child):
        return InputType.SAMPLE_DIR

    grandchild = _first_visible_subdir(child)
    if grandchild is None:
        return InputType.UNKNOWN

    if _is_fov_dir(grandchild):
        return InputType.POPULATION_DIR

    great_grandchild = _first_visible_subdir(grandchild)
    if great_grandchild is not None and _is_fov_dir(great_grandchild):
        return InputType.PROJECT_DIR

    return InputType.UNKNOWN


# Mapping from InputType to (source, data_level) used by the load endpoint.
_TYPE_TO_SOURCE_LEVEL: dict[InputType, tuple[str, str]] = {
    InputType.DUCKDB: ("database", "Project"),
    InputType.PROJECT_DIR: ("filesystem", "Project"),
    InputType.POPULATION_DIR: ("filesystem", "Population"),
    InputType.SAMPLE_DIR: ("filesystem", "Sample"),
    InputType.FOV_DIR: ("filesystem", "FOV"),
    InputType.SIGNAL_FILE: ("filesystem", "Files"),
    InputType.EVENT_FILE: ("filesystem", "Files"),
}


def classify_paths(paths: list[str]) -> tuple[str, str]:
    """Determine (source, data_level) for a list of paths.

    Args:
        paths: List of filesystem path strings.

    Returns:
        Tuple of ``(source, data_level)``.

    Raises:
        ValueError: If the paths cannot be classified.
    """
    if not paths:
        raise ValueError("No paths provided")

    types = [detect_input_type(p) for p in paths]

    # All files → check for signal + event pair.
    file_types = {InputType.SIGNAL_FILE, InputType.EVENT_FILE}
    if all(t in file_types for t in types):
        return ("filesystem", "Files")

    # Single DuckDB file.
    if len(types) == 1 and types[0] == InputType.DUCKDB:
        return ("database", "Project")

    # All same directory type.
    unique = set(types) - {InputType.UNKNOWN}
    if len(unique) == 1:
        t = unique.pop()
        if t in _TYPE_TO_SOURCE_LEVEL:
            return _TYPE_TO_SOURCE_LEVEL[t]

    # If there's any recognized type, use the first one.
    for t in types:
        if t in _TYPE_TO_SOURCE_LEVEL:
            return _TYPE_TO_SOURCE_LEVEL[t]

    raise ValueError(f"Cannot classify paths: unrecognized input types {types}")
