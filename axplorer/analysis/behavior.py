"""Behavioral summary computation for a session.

Extracts aggregate behavioral metrics (press counts, discrimination index,
cumulative curves) from a ``SessionWrapper``'s event DataFrame.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from axplorer.alignment.session import SessionWrapper
from axplorer.types import BehaviorSummary


# Labels recognised as presses / reinforcers across task types.
_ACTIVE_LABELS = {"active_lever_press", "active_lever", "active_lick"}
_INACTIVE_LABELS = {"inactive_lever_press", "inactive_lever", "inactive_lick"}
_TIMEOUT_LABELS = {"timeout_lever_press", "active_lever_timeout", "active_lick_timeout"}
_REINFORCER_LABELS = {"infusion", "ethanol_delivery", "water_delivery"}


def compute_behavior_summary(session: SessionWrapper) -> BehaviorSummary:
    """Compute aggregate behavioral metrics for a session.

    Args:
        session: A loaded ``SessionWrapper`` instance.

    Returns:
        A ``BehaviorSummary`` dataclass with press counts, discrimination
        index, press rate, event timeline, and cumulative curves.
    """
    event_counts = {
        label: session.sample.count_events(
            session.get_event_code_for_label(label)
        )
        for label in session.get_event_labels()
    }

    active = sum(v for k, v in event_counts.items() if k in _ACTIVE_LABELS)
    inactive = sum(v for k, v in event_counts.items() if k in _INACTIVE_LABELS)
    timeout = sum(v for k, v in event_counts.items() if k in _TIMEOUT_LABELS)
    reinforcers = sum(v for k, v in event_counts.items() if k in _REINFORCER_LABELS)

    total = active + inactive
    disc_idx = active / total if total > 0 else 0.0

    duration_min = session.duration_s / 60.0
    press_rate = (active + inactive + timeout) / duration_min if duration_min > 0 else 0.0

    df = session.get_dataframe()

    # Cumulative press curves for active, inactive, and timeout labels.
    press_labels = sorted(
        label for label in session.get_event_labels()
        if label in (_ACTIVE_LABELS | _INACTIVE_LABELS | _TIMEOUT_LABELS)
    )
    cumulative = compute_cumulative_presses(df, press_labels)

    return BehaviorSummary(
        active_presses=active,
        inactive_presses=inactive,
        timeout_presses=timeout,
        reinforcers=reinforcers,
        discrimination_index=disc_idx,
        press_rate_per_min=press_rate,
        event_timeline=df,
        cumulative_presses=cumulative,
    )


def compute_cumulative_presses(
    df: pd.DataFrame,
    labels: List[str],
) -> Dict[str, Dict[str, NDArray]]:
    """Build cumulative press curves for a set of event labels.

    Args:
        df: Event DataFrame with ``label`` and ``t1`` columns. ``t1`` is
            in microseconds.
        labels: Event labels to compute cumulative curves for.

    Returns:
        Dict mapping each label to ``{"time": NDArray, "count": NDArray}``
        where *time* is in seconds from session start and *count* is the
        running total.
    """
    result: Dict[str, Dict[str, NDArray]] = {}

    for label in labels:
        subset = df[df["label"] == label].sort_values("t1")
        if subset.empty:
            result[label] = {
                "time": np.array([], dtype=np.float64),
                "count": np.array([], dtype=np.int64),
            }
            continue

        times_us = subset["t1"].values.astype(np.float64)
        # Convert microseconds to seconds, offset from session start.
        t0 = df["t1"].min()
        times_s = (times_us - t0) / 1e6
        counts = np.arange(1, len(times_s) + 1)

        result[label] = {"time": times_s, "count": counts}

    return result
