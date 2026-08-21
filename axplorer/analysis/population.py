"""Population-level peri-event time histogram analysis.

Pools neurons across multiple sessions to produce a population-level PETH
result with both neuron-pooled heatmap data and session-averaged grand
mean/median traces.
"""

from __future__ import annotations

from math import sqrt
from typing import List

import numpy as np
from numpy.typing import NDArray

from pynapse.analysis.preprocessing.epoch import Pipeline

from axplorer.alignment.session import SessionWrapper
from axplorer.analysis.peth import compute_peth
from axplorer.types import PopulationPETHResult


def compute_population_peth(
    sessions: List[SessionWrapper],
    event_id: int,
    pre_event_s: float = 5.0,
    post_event_s: float = 10.0,
    pipeline: Pipeline | None = None,
    buffer_ms: int = 0,
    min_trials: int = 3,
) -> PopulationPETHResult:
    """Compute a population-level PETH by pooling neurons across sessions.

    For each session, computes a single-session PETH via ``compute_peth()``,
    then stacks all session mean traces into a pooled ``(total_neurons, time)``
    matrix.  The grand mean, median, and SEM are computed across *sessions*
    (not individual neurons), treating each session as one observation.

    All sessions must share the same ``effective_fps`` (tolerance +/- 0.01 Hz)
    so that time axes align.

    Args:
        sessions: List of loaded ``SessionWrapper`` objects.
        event_id: Integer event code to lock windows to.
        pre_event_s: Seconds before event onset.
        post_event_s: Seconds after event onset.
        pipeline: Preprocessing pipeline applied per-window.
        buffer_ms: Minimum interval between events in ms.
        min_trials: Minimum valid trials required per session.

    Returns:
        A ``PopulationPETHResult`` containing pooled and session-averaged data.

    Raises:
        ValueError: If sessions have mismatched ``effective_fps`` values or
            the sessions list is empty.
    """
    if not sessions:
        raise ValueError("At least one session is required.")

    # Validate FPS consistency.
    fps_values = [s.effective_fps for s in sessions]
    if max(fps_values) - min(fps_values) > 0.01:
        raise ValueError(
            f"All sessions must share the same effective_fps. "
            f"Got: {fps_values}"
        )

    # Compute per-session PETHs.
    peth_results = []
    for session in sessions:
        peth = compute_peth(
            session=session,
            event_id=event_id,
            pre_event_s=pre_event_s,
            post_event_s=post_event_s,
            pipeline=pipeline,
            buffer_ms=buffer_ms,
            min_trials=min_trials,
        )
        peth_results.append(peth)

    # Use time axis from the first session (all share same FPS + window).
    time_axis = peth_results[0].time_axis

    # Neuron pooling: stack all mean matrices vertically.
    pooled_parts: list[NDArray[np.float32]] = []
    session_mean_traces: list[NDArray[np.float32]] = []
    session_labels: list[str] = []
    session_neuron_counts: list[int] = []
    total_trials = 0

    for session, peth in zip(sessions, peth_results):
        # peth.mean is (neurons, time)
        pooled_parts.append(peth.mean)
        session_neuron_counts.append(peth.mean.shape[0])
        total_trials += peth.n_trials
        session_labels.append(session.name)

        # Per-session mean trace: average across neurons within this session.
        session_trace = np.nanmean(peth.mean, axis=0).astype(np.float32)
        session_mean_traces.append(session_trace)

    pooled_mean = np.vstack(pooled_parts).astype(np.float32)
    session_means = np.stack(session_mean_traces).astype(np.float32)

    n_sessions = len(sessions)
    grand_mean = np.nanmean(session_means, axis=0).astype(np.float32)
    grand_median = np.nanmedian(session_means, axis=0).astype(np.float32)

    if n_sessions > 1:
        grand_sem = (
            np.nanstd(session_means, axis=0, ddof=1) / sqrt(n_sessions)
        ).astype(np.float32)
    else:
        grand_sem = np.zeros_like(grand_mean)

    # Resolve event label from the first session's PETH.
    event_label = peth_results[0].event_label

    return PopulationPETHResult(
        pooled_mean=pooled_mean,
        session_means=session_means,
        grand_mean=grand_mean,
        grand_median=grand_median,
        grand_sem=grand_sem,
        time_axis=time_axis,
        event_label=event_label,
        session_labels=session_labels,
        session_neuron_counts=session_neuron_counts,
        total_neurons=pooled_mean.shape[0],
        total_trials=total_trials,
        n_sessions=n_sessions,
        pre_event_s=pre_event_s,
        post_event_s=post_event_s,
    )
