"""Data contracts for the Axplorer pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

import numpy as np
import pandas as pd
from numpy.typing import NDArray

if TYPE_CHECKING:
    from axplorer.alignment.session import SessionWrapper


@dataclass(frozen=True)
class SessionMeta:
    """Filesystem-level metadata extracted from the directory hierarchy."""

    phase: str
    animal_id: str
    sex: str
    fov: str
    is_tracked: bool
    npy_paths: tuple[Path, ...]  # signal file paths -- .npy (legacy) or .h5 (roigbiv)
    event_paths: tuple[Path, ...]
    frame_timestamps_path: Path | None = None


@dataclass
class Session:
    """A fully loaded experimental session."""

    meta: SessionMeta
    metadata: SessionMetadata
    wrapper: SessionWrapper


@dataclass(frozen=True)
class SessionMetadata:
    """Immutable summary of a loaded session."""

    name: str
    n_neurons: int
    n_frames: int
    n_events: int
    event_counts: Dict[str, int]
    effective_fps: float
    duration_s: float
    task_type: str
    signal_kind: Optional[str] = None  # h5 trace kind ("f"/"dff"/"raw"/"neuropil"), None for legacy .npy


@dataclass
class PETHResult:
    """Peri-event time histogram for one event type across neurons."""

    event_windows: NDArray[np.float32]  # (trials, neurons, time)
    time_axis: NDArray[np.float64]
    mean: NDArray[np.float32]  # (neurons, time)
    sem: NDArray[np.float32]  # (neurons, time)
    event_label: str
    n_trials: int
    pre_event_s: float
    post_event_s: float


@dataclass
class ResponseMetrics:
    """Per-neuron response quantification relative to an event."""

    cell_id: int
    peak_zscore: float
    peak_latency_s: float
    auc: float
    onset_latency_s: Optional[float]
    mean_baseline: float
    mean_response: float


@dataclass
class PopulationPETHResult:
    """Population-level PETH with both neuron pooling and session averaging.

    Attributes:
        pooled_mean: All neurons stacked across sessions (total_neurons, time).
        session_means: One mean trace per session (n_sessions, time).
        grand_mean: Mean across sessions (time,).
        grand_median: Median across sessions (time,). Mode is intentionally
            omitted -- not meaningful for continuous ΔF/F signals.
        grand_sem: SEM across sessions, N = n_sessions (time,).
        time_axis: Shared time axis (time,).
        event_label: Event label used for the PETH.
        session_labels: Name of each contributing session.
        session_neuron_counts: Number of neurons from each session.
        total_neurons: Sum of neurons across all sessions.
        total_trials: Sum of trials across all sessions.
        n_sessions: Number of sessions included.
        pre_event_s: Pre-event window in seconds.
        post_event_s: Post-event window in seconds.
    """

    pooled_mean: NDArray[np.float32]
    session_means: NDArray[np.float32]
    grand_mean: NDArray[np.float32]
    grand_median: NDArray[np.float32]
    grand_sem: NDArray[np.float32]
    time_axis: NDArray[np.float64]
    event_label: str
    session_labels: List[str]
    session_neuron_counts: List[int]
    total_neurons: int
    total_trials: int
    n_sessions: int
    pre_event_s: float
    post_event_s: float


@dataclass
class BehaviorSummary:
    """Aggregate behavioral metrics for a session."""

    active_presses: int
    inactive_presses: int
    timeout_presses: int
    reinforcers: int
    discrimination_index: float
    press_rate_per_min: float
    event_timeline: pd.DataFrame
    cumulative_presses: Dict[str, Dict[str, NDArray]]
