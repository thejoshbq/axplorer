"""Session file loading -- constructs a Pynapse Sample + SessionMetadata.

Orchestrates validation, task-type detection, and Sample construction so
that downstream code receives a fully validated, ready-to-analyze pair of
(Sample, SessionMetadata).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from pynapse.core import Sample
from pynapse.config.events import TASK_TO_DICT

from axplorer.types import SessionMetadata
from axplorer.ingestion.validators import (
    validate_signal_file,
    validate_event_file,
    detect_task_type,
)


class LoadError(Exception):
    """Raised when session loading fails validation.

    Attributes:
        errors: List of human-readable error descriptions.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Session load failed: {'; '.join(errors)}")


def load_session_files(
    signal_path: str | Path | list[str | Path],
    event_path: str | Path | list[str | Path],
    fps: float = 30.0,
    frame_averaging: int = 4,
    task_type: str | None = None,
    session_name: str | None = None,
) -> Tuple[Sample, SessionMetadata]:
    """Load and validate signal + event files into a Pynapse Sample.

    Performs input validation on both files, auto-detects the task type when
    not provided, constructs a ``Sample``, and builds a ``SessionMetadata``
    summary from the resulting object.

    Args:
        signal_path: Path(s) to ``.npy`` signal file(s) (neurons x frames).
            A single path or a list of paths for multi-file FOVs.
        event_path: Path(s) to ``.xlsx`` or ``.mat`` event file(s).
            A single path or a list of paths for multi-file FOVs.
        fps: Raw imaging frame rate in Hz.
        frame_averaging: Number of raw frames binned into each signal frame.
        task_type: One of ``'reacher'``, ``'legacy_her'``, or
            ``'legacy_eth'``. Auto-detected from the event file if ``None``.
        session_name: Human-readable session label. Defaults to the first
            signal file stem (filename without extension).

    Returns:
        Tuple of ``(Sample, SessionMetadata)``.

    Raises:
        LoadError: If either file fails validation or the task type is
            unrecognized.
    """
    # Normalize to lists.
    if isinstance(signal_path, (str, Path)):
        signal_paths = [Path(signal_path)]
    else:
        signal_paths = [Path(p) for p in signal_path]

    if isinstance(event_path, (str, Path)):
        event_paths = [Path(p) for p in ([event_path] if isinstance(event_path, (str, Path)) else event_path)]
    else:
        event_paths = [Path(p) for p in event_path]

    # ------------------------------------------------------------------
    # 1. Validate all files, collecting all errors before bailing out
    # ------------------------------------------------------------------
    errors: list[str] = []

    for sp in signal_paths:
        sig_result = validate_signal_file(sp)
        if not sig_result.valid:
            errors.extend(sig_result.errors)

    for ep in event_paths:
        evt_result = validate_event_file(ep)
        if not evt_result.valid:
            errors.extend(evt_result.errors)

    if errors:
        raise LoadError(errors)

    # ------------------------------------------------------------------
    # 2. Resolve task type (use the first event file for detection)
    # ------------------------------------------------------------------
    if task_type is None:
        try:
            task_type = detect_task_type(event_paths[0])
        except ValueError as exc:
            raise LoadError([str(exc)]) from exc

    if task_type not in TASK_TO_DICT:
        raise LoadError(
            [
                f"Unknown task_type '{task_type}'. "
                f"Valid options: {sorted(TASK_TO_DICT.keys())}"
            ]
        )

    # ------------------------------------------------------------------
    # 3. Look up event dictionary
    # ------------------------------------------------------------------
    event_dict = TASK_TO_DICT[task_type]

    # ------------------------------------------------------------------
    # 3.5 Convert .xlsx event files to temp CSV for Pynapse
    # ------------------------------------------------------------------
    _temp_files: list[Path] = []
    converted_event_paths: list[Path] = []
    for ep in event_paths:
        if ep.suffix.lower() == ".xlsx":
            csv_path = _convert_xlsx_to_csv(ep)
            _temp_files.append(csv_path)
            converted_event_paths.append(csv_path)
        else:
            converted_event_paths.append(ep)

    # ------------------------------------------------------------------
    # 4. Derive session name
    # ------------------------------------------------------------------
    if session_name is None:
        session_name = signal_paths[0].stem

    # ------------------------------------------------------------------
    # 5. Construct Pynapse Sample (supports multi-file natively)
    # ------------------------------------------------------------------
    signal_data: str | list[str] = (
        [str(p) for p in signal_paths] if len(signal_paths) > 1
        else str(signal_paths[0])
    )
    event_data: str | list[str] = (
        [str(p) for p in converted_event_paths]
        if len(converted_event_paths) > 1
        else str(converted_event_paths[0])
    )

    try:
        try:
            sample = Sample(
                event_data=event_data,
                signal_data=signal_data,
                name=session_name,
                event_dict=event_dict,
                fps=fps,
                frame_averaging=frame_averaging,
            )
        except Exception as exc:
            raise LoadError([f"Pynapse Sample construction failed: {exc}"]) from exc

        # ------------------------------------------------------------------
        # 6. Build SessionMetadata from the live sample
        # ------------------------------------------------------------------
        event_counts = _build_event_counts(sample, event_dict)

        metadata = SessionMetadata(
            name=session_name,
            n_neurons=sample.num_neurons,
            n_frames=sample.num_frames,
            n_events=sample.num_events,
            event_counts=event_counts,
            effective_fps=sample.effective_fps,
            duration_s=sample.num_frames / sample.effective_fps,
            task_type=task_type,
        )

        return sample, metadata
    finally:
        for tmp in _temp_files:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _convert_xlsx_to_csv(xlsx_path: Path) -> Path:
    """Convert a REACHER ``.xlsx`` event file to a temporary CSV for Pynapse.

    Reads the ``Behavior Data`` sheet and writes only the columns that
    Pynapse's ``EventLog._load_reacher_csv()`` expects: ``device``,
    ``event``, ``start_timestamp``, ``end_timestamp``.

    Args:
        xlsx_path: Path to the validated ``.xlsx`` event file.

    Returns:
        Path to a temporary ``.csv`` file.  Caller is responsible for
        cleanup (see the ``finally`` block in :func:`load_session_files`).
    """
    import tempfile

    import pandas as pd

    df = pd.read_excel(xlsx_path, sheet_name="Behavior Data", engine="openpyxl")
    cols = ["device", "event", "start_timestamp", "end_timestamp"]
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, prefix="axplorer_",
    )
    df[cols].to_csv(tmp.name, index=False)
    tmp.close()
    return Path(tmp.name)


def _build_event_counts(
    sample: Sample,
    event_dict: dict[int, str],
) -> dict[str, int]:
    """Aggregate per-event counts, excluding the frame trigger.

    Args:
        sample: A constructed ``Sample`` instance.
        event_dict: Mapping of integer event codes to label strings.

    Returns:
        Dictionary mapping event labels to their occurrence counts.
    """
    counts: dict[str, int] = {}
    for code, label in event_dict.items():
        if label == "frame_trigger":
            continue
        counts[label] = sample.count_events(code)
    return counts
