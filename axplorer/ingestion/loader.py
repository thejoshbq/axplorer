"""Session file loading -- constructs a Pynapse Sample + SessionMetadata.

Orchestrates validation, task-type detection, and Sample construction so
that downstream code receives a fully validated, ready-to-analyze pair of
(Sample, SessionMetadata).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from pynapse.core import Sample
from pynapse.core.io.microscopy import SignalRecording
from pynapse.config.events import TASK_TO_DICT

from axplorer.types import SessionMetadata
from axplorer.ingestion.validators import (
    validate_signal_file,
    validate_event_file,
    validate_frame_timestamps_file,
    detect_task_type,
    list_h5_kinds,
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
    frame_timestamps_path: str | Path | None = None,
    h5_kind: str | None = None,
) -> Tuple[Sample, SessionMetadata]:
    """Load and validate signal + event files into a Pynapse Sample.

    Performs input validation on both files, auto-detects the task type when
    not provided, constructs a ``Sample``, and builds a ``SessionMetadata``
    summary from the resulting object.

    Args:
        signal_path: Path(s) to a ``.npy`` signal file (neurons x frames) or
            a roigbiv ``.h5`` trace export. A single path or a list of paths
            for multi-file FOVs. Mixing ``.npy`` and ``.h5`` is not supported.
        event_path: Path(s) to ``.csv``, ``.xlsx``, or ``.mat`` event file(s).
            A single path or a list of paths for multi-file FOVs.
        fps: Raw imaging frame rate in Hz. Ignored for ``.h5`` signal sources
            -- their effective rate comes from the file's ``/meta`` table.
        frame_averaging: Number of raw frames binned into each signal frame.
            Ignored for ``.h5`` signal sources (already baked into ``/meta``'s
            ``fs``).
        task_type: One of ``'reacher'``, ``'legacy_her'``, or
            ``'legacy_eth'``. Auto-detected from the event file if ``None``.
        session_name: Human-readable session label. Defaults to the first
            signal file stem (filename without extension).
        frame_timestamps_path: Optional path to a REACHER ``frame_timestamps.csv``
            file. When ``None`` and the first event file is a ``.csv``, a
            sibling ``frame_timestamps.csv`` (if present) is picked up
            automatically. Passed through to pynapse's
            ``Sample(frame_timestamps=...)`` so event→frame alignment uses
            real acquisition timestamps instead of a synthetic clock grid.
            Ignored for ``.h5`` signal sources, which derive a uniform
            frame-timestamp grid from ``/meta``'s ``fs`` instead.
        h5_kind: Which trace kind to load when ``signal_path`` is a ``.h5``
            file -- one of ``"f"``, ``"dff"``, ``"raw"``, ``"neuropil"``.
            Required (no default) when the signal source is ``.h5``; ignored
            for ``.npy`` sources.

    Returns:
        Tuple of ``(Sample, SessionMetadata)``.

    Raises:
        LoadError: If either file fails validation, the task type is
            unrecognized, or (for ``.h5`` signal sources) ``h5_kind`` is
            missing or not present in the file.
    """
    # Normalize to lists.
    if isinstance(signal_path, (str, Path)):
        signal_paths = [Path(signal_path)]
    else:
        signal_paths = [Path(p) for p in signal_path]

    is_h5_signal = signal_paths[0].suffix.lower() in (".h5", ".hdf5")

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

    if is_h5_signal:
        available_kinds = list_h5_kinds(signal_paths[0])
        if h5_kind is None:
            errors.append(
                f"h5_kind is required for .h5 signal sources (no default trace "
                f"kind). Available kinds in {signal_paths[0].name}: {available_kinds}"
            )
        elif h5_kind not in available_kinds:
            errors.append(
                f"h5_kind '{h5_kind}' not present in {signal_paths[0].name}. "
                f"Available kinds: {available_kinds}"
            )

    for ep in event_paths:
        evt_result = validate_event_file(ep)
        if not evt_result.valid:
            errors.extend(evt_result.errors)

    # Auto-detect a sibling frame_timestamps.csv when a REACHER CSV event file
    # is used and the caller didn't override.
    resolved_ft_path: Path | None
    if frame_timestamps_path is None:
        first_event = event_paths[0] if event_paths else None
        if first_event is not None and first_event.suffix.lower() == ".csv":
            sibling = first_event.parent / "frame_timestamps.csv"
            resolved_ft_path = sibling if sibling.exists() else None
        else:
            resolved_ft_path = None
    else:
        resolved_ft_path = Path(frame_timestamps_path)

    if resolved_ft_path is not None:
        ft_result = validate_frame_timestamps_file(resolved_ft_path)
        if not ft_result.valid:
            errors.extend(ft_result.errors)

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
    event_data: str | list[str] = (
        [str(p) for p in converted_event_paths]
        if len(converted_event_paths) > 1
        else str(converted_event_paths[0])
    )

    try:
        try:
            if is_h5_signal:
                # Build the SignalRecording ourselves so we can read /meta's
                # authoritative fs and derive a uniform frame-timestamp grid --
                # the same extension points Sample already exposes for the
                # REACHER path (pre-built SignalRecording + external
                # frame_timestamps), so Sample itself needs no h5-awareness.
                signal_recording = SignalRecording(
                    source=[str(p) for p in signal_paths] if len(signal_paths) > 1
                    else str(signal_paths[0]),
                    name=session_name,
                    kind=h5_kind,
                )
                h5_fs = signal_recording.fs
                h5_frame_timestamps = np.arange(signal_recording.num_frames) / h5_fs * 1000.0
                sample = Sample(
                    event_data=event_data,
                    signal_data=signal_recording,
                    name=session_name,
                    event_dict=event_dict,
                    fps=h5_fs,
                    frame_averaging=1,
                    frame_timestamps=h5_frame_timestamps,
                )
            else:
                signal_data: str | list[str] = (
                    [str(p) for p in signal_paths] if len(signal_paths) > 1
                    else str(signal_paths[0])
                )
                sample = Sample(
                    event_data=event_data,
                    signal_data=signal_data,
                    name=session_name,
                    event_dict=event_dict,
                    fps=fps,
                    frame_averaging=frame_averaging,
                    frame_timestamps=str(resolved_ft_path) if resolved_ft_path is not None else None,
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
            signal_kind=h5_kind if is_h5_signal else None,
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
