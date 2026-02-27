"""Response quantification — per-neuron metrics and classification.

Computes peak z-score, AUC, latencies, and classifies neurons as excitatory,
inhibitory, or non-responsive based on PETH data.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from axplorer.types import PETHResult, ResponseMetrics


def compute_response_metrics(
    peth: PETHResult,
    baseline_window_s: Tuple[float, float] = (-5.0, -0.5),
    response_window_s: Tuple[float, float] = (0.0, 5.0),
    onset_threshold_sd: float = 2.0,
) -> List[ResponseMetrics]:
    """Compute per-neuron response metrics from a PETH result.

    For each neuron, calculates:
        - Peak z-score within the response window.
        - Peak latency (time of peak from event onset).
        - AUC (trapezoidal integration in the response window).
        - Onset latency (first sustained threshold crossing).
        - Mean baseline and mean response activity.

    Args:
        peth: A ``PETHResult`` containing mean traces.
        baseline_window_s: (start, end) seconds defining the baseline epoch.
        response_window_s: (start, end) seconds defining the response epoch.
        onset_threshold_sd: Number of baseline SDs for onset detection.

    Returns:
        List of ``ResponseMetrics``, one per neuron.
    """
    mean = peth.mean  # (neurons, time)
    time_axis = peth.time_axis
    n_neurons = mean.shape[0]

    # Build boolean masks for baseline and response windows.
    bl_mask = (time_axis >= baseline_window_s[0]) & (time_axis < baseline_window_s[1])
    resp_mask = (time_axis >= response_window_s[0]) & (time_axis < response_window_s[1])

    dt = np.mean(np.diff(time_axis)) if len(time_axis) > 1 else 1.0
    resp_time = time_axis[resp_mask]

    results: List[ResponseMetrics] = []

    for i in range(n_neurons):
        trace = mean[i]
        bl_vals = trace[bl_mask]
        resp_vals = trace[resp_mask]

        mean_bl = float(np.nanmean(bl_vals)) if bl_vals.size > 0 else 0.0
        mean_resp = float(np.nanmean(resp_vals)) if resp_vals.size > 0 else 0.0
        bl_std = float(np.nanstd(bl_vals, ddof=1)) if bl_vals.size > 1 else 1.0

        # Peak z-score and latency within response window.
        if resp_vals.size > 0:
            abs_vals = np.abs(resp_vals)
            peak_idx = int(np.argmax(abs_vals))
            peak_val = resp_vals[peak_idx]
            peak_zscore = float((peak_val - mean_bl) / bl_std) if bl_std > 0 else 0.0
            peak_latency_s = float(resp_time[peak_idx])
        else:
            peak_zscore = 0.0
            peak_latency_s = 0.0

        # AUC via trapezoidal integration.
        if resp_vals.size > 1:
            auc = float(np.trapezoid(resp_vals - mean_bl, dx=dt))
        else:
            auc = 0.0

        # Onset latency: first time threshold is exceeded for >= 2 consecutive frames.
        onset_latency: Optional[float] = None
        if resp_vals.size > 1 and bl_std > 0:
            threshold = mean_bl + onset_threshold_sd * bl_std
            above = np.abs(resp_vals - mean_bl) > (onset_threshold_sd * bl_std)
            # Find first pair of consecutive True values.
            for j in range(len(above) - 1):
                if above[j] and above[j + 1]:
                    onset_latency = float(resp_time[j])
                    break

        results.append(
            ResponseMetrics(
                cell_id=i,
                peak_zscore=peak_zscore,
                peak_latency_s=peak_latency_s,
                auc=auc,
                onset_latency_s=onset_latency,
                mean_baseline=mean_bl,
                mean_response=mean_resp,
            )
        )

    return results


def classify_response(
    metrics: ResponseMetrics,
    exc_threshold: float = 2.0,
    inh_threshold: float = -2.0,
) -> str:
    """Classify a neuron's response based on its peak z-score.

    Args:
        metrics: ``ResponseMetrics`` for a single neuron.
        exc_threshold: Minimum peak z-score for excitatory classification.
        inh_threshold: Maximum peak z-score for inhibitory classification.

    Returns:
        One of ``'excitatory'``, ``'inhibitory'``, or ``'non-responsive'``.
    """
    if metrics.peak_zscore >= exc_threshold:
        return "excitatory"
    elif metrics.peak_zscore <= inh_threshold:
        return "inhibitory"
    else:
        return "non-responsive"
