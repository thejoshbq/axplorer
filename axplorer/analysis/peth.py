"""Peri-event time histogram (PETH) computation.

Delegates tensor extraction to Pynapse and computes summary statistics
(mean +/- SEM), sorted heatmaps, and single-cell trial rasters.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from pynapse.analysis.preprocessing.epoch import Pipeline

from axplorer.alignment.session import SessionWrapper
from axplorer.types import PETHResult


def compute_peth(
    session: SessionWrapper,
    event_id: int,
    pre_event_s: float = 5.0,
    post_event_s: float = 10.0,
    pipeline: Pipeline | None = None,
    buffer_ms: int = 0,
    min_trials: int = 3,
    cell_ids: List[int] | None = None,
) -> PETHResult:
    """Compute a peri-event time histogram for a given event.

    Args:
        session: Loaded ``SessionWrapper``.
        event_id: Integer event code to lock windows to.
        pre_event_s: Seconds before event onset.
        post_event_s: Seconds after event onset.
        pipeline: Preprocessing pipeline applied per-window.
        buffer_ms: Minimum interval between events in ms.
        min_trials: Minimum valid trials required.
        cell_ids: If provided, subset the result to these neuron indices.

    Returns:
        A ``PETHResult`` containing event windows, mean, SEM, and metadata.
    """
    tensor = session.get_tensor(
        event_id=event_id,
        pre_event_s=pre_event_s,
        post_event_s=post_event_s,
        pipeline=pipeline,
        buffer_ms=buffer_ms,
        min_trials=min_trials,
    )

    windows = tensor.get_event_windows()  # (trials, neurons, time)
    time_axis = session.make_time_axis(pre_event_s, post_event_s)

    # Align time axis length to actual window length.
    n_time = windows.shape[2] if windows.ndim == 3 and windows.shape[0] > 0 else 0
    if n_time > 0 and len(time_axis) != n_time:
        time_axis = np.linspace(-pre_event_s, post_event_s, n_time, endpoint=False)

    # Optionally subset neurons.
    if cell_ids is not None and windows.ndim == 3 and windows.shape[0] > 0:
        windows = windows[:, cell_ids, :]

    # Compute mean and SEM across trials (axis 0).
    if windows.ndim == 3 and windows.shape[0] > 0:
        mean = np.nanmean(windows, axis=0).astype(np.float32)
        n_trials = windows.shape[0]
        sem = (np.nanstd(windows, axis=0, ddof=1) / np.sqrt(n_trials)).astype(np.float32)
    else:
        n_neurons = session.num_neurons
        if cell_ids is not None:
            n_neurons = len(cell_ids)
        n_time_pts = len(time_axis) if len(time_axis) > 0 else 0
        mean = np.zeros((n_neurons, n_time_pts), dtype=np.float32)
        sem = np.zeros_like(mean)
        n_trials = 0
        windows = np.zeros((0, n_neurons, n_time_pts), dtype=np.float32)

    # Resolve event label.
    event_label = session._code_to_label.get(event_id, str(event_id))

    return PETHResult(
        event_windows=windows,
        time_axis=time_axis,
        mean=mean,
        sem=sem,
        event_label=event_label,
        n_trials=n_trials,
        pre_event_s=pre_event_s,
        post_event_s=post_event_s,
    )


def sort_neuron_matrix(
    mean: NDArray,
    time_axis: NDArray,
    post_event_s: float,
    sort_epoch: Tuple[float, float] | None = None,
    sort_method: str = "excitatory",
) -> Tuple[NDArray[np.float32], NDArray[np.intp]]:
    """Sort a (neurons, time) matrix by response characteristics.

    Args:
        mean: Array of shape ``(neurons, time)`` to sort.
        time_axis: Corresponding time axis of length ``time``.
        post_event_s: Post-event window in seconds (used as default epoch end).
        sort_epoch: Optional ``(start_s, end_s)`` time window for sorting.
            Defaults to the post-event epoch ``(0, post_event_s)``.
        sort_method: Sorting strategy:
            - ``'excitatory'``: by peak latency (ascending).
            - ``'inhibitory'``: by trough latency (ascending).
            - ``'magnitude'``: by absolute peak magnitude (descending).

    Returns:
        Tuple of ``(sorted_mean, sort_indices)`` where *sorted_mean* has
        neurons reordered and *sort_indices* maps new → original order.
    """
    if sort_epoch is None:
        sort_epoch = (0.0, post_event_s)

    mask = (time_axis >= sort_epoch[0]) & (time_axis <= sort_epoch[1])
    epoch_data = mean[:, mask]

    if sort_method == "excitatory":
        sort_indices = np.argsort(np.argmax(epoch_data, axis=1))
    elif sort_method == "inhibitory":
        sort_indices = np.argsort(np.argmin(epoch_data, axis=1))
    elif sort_method == "magnitude":
        sort_indices = np.argsort(-np.max(np.abs(epoch_data), axis=1))
    else:
        raise ValueError(
            f"Unknown sort_method '{sort_method}'. "
            "Choose 'excitatory', 'inhibitory', or 'magnitude'."
        )

    sorted_mean = mean[sort_indices]
    return sorted_mean, sort_indices


def compute_sorted_heatmap(
    peth: PETHResult,
    sort_epoch: Tuple[float, float] | None = None,
    sort_method: str = "excitatory",
) -> Tuple[NDArray[np.float32], NDArray[np.intp]]:
    """Sort neurons in a PETH result by response characteristics.

    Thin wrapper around :func:`sort_neuron_matrix` that unpacks fields
    from a ``PETHResult``.

    Args:
        peth: A ``PETHResult`` to sort.
        sort_epoch: Optional (start_s, end_s) time window for sorting.
            Defaults to the post-event epoch (0 to post_event_s).
        sort_method: Sorting strategy (see :func:`sort_neuron_matrix`).

    Returns:
        Tuple of ``(sorted_mean, sort_indices)`` where *sorted_mean* has
        neurons reordered and *sort_indices* maps new → original order.
    """
    return sort_neuron_matrix(
        peth.mean, peth.time_axis, peth.post_event_s, sort_epoch, sort_method
    )


def compute_trial_raster(
    session: SessionWrapper,
    event_id: int,
    cell_id: int,
    pre_event_s: float = 5.0,
    post_event_s: float = 10.0,
    pipeline: Pipeline | None = None,
    buffer_ms: int = 0,
    min_trials: int = 1,
) -> Tuple[NDArray[np.float32], NDArray[np.float64]]:
    """Extract single-cell trial-by-trial data for a given event.

    Args:
        session: Loaded ``SessionWrapper``.
        event_id: Integer event code.
        cell_id: Index of the neuron to extract.
        pre_event_s: Pre-event window in seconds.
        post_event_s: Post-event window in seconds.
        pipeline: Optional preprocessing pipeline.
        buffer_ms: Minimum ms between events.
        min_trials: Minimum valid trials required.

    Returns:
        Tuple of ``(trials_matrix, time_axis)`` where *trials_matrix* has
        shape ``(n_trials, n_time)`` for the single cell.
    """
    tensor = session.get_tensor(
        event_id=event_id,
        pre_event_s=pre_event_s,
        post_event_s=post_event_s,
        pipeline=pipeline,
        buffer_ms=buffer_ms,
        min_trials=min_trials,
    )

    windows = tensor.get_event_windows()  # (trials, neurons, time)
    time_axis = session.make_time_axis(pre_event_s, post_event_s)

    if windows.ndim == 3 and windows.shape[0] > 0:
        trials_matrix = windows[:, cell_id, :].astype(np.float32)
        n_time = trials_matrix.shape[1]
        if len(time_axis) != n_time:
            time_axis = np.linspace(-pre_event_s, post_event_s, n_time, endpoint=False)
    else:
        n_time = len(time_axis)
        trials_matrix = np.zeros((0, n_time), dtype=np.float32)

    return trials_matrix, time_axis
