"""Tests for axplorer.analysis.behavior."""

import numpy as np
import pytest

from axplorer.analysis.behavior import (
    compute_behavior_summary,
    compute_cumulative_presses,
)
from axplorer.types import BehaviorSummary


class TestComputeBehaviorSummary:
    """Tests for compute_behavior_summary."""

    def test_returns_summary(self, loaded_session):
        _, _, wrapper = loaded_session
        summary = compute_behavior_summary(wrapper)
        assert isinstance(summary, BehaviorSummary)

    def test_counts_nonnegative(self, loaded_session):
        _, _, wrapper = loaded_session
        summary = compute_behavior_summary(wrapper)
        assert summary.active_presses >= 0
        assert summary.inactive_presses >= 0
        assert summary.timeout_presses >= 0
        assert summary.reinforcers >= 0

    def test_discrimination_index_range(self, loaded_session):
        _, _, wrapper = loaded_session
        summary = compute_behavior_summary(wrapper)
        assert 0.0 <= summary.discrimination_index <= 1.0

    def test_press_rate_positive(self, loaded_session):
        _, _, wrapper = loaded_session
        summary = compute_behavior_summary(wrapper)
        assert summary.press_rate_per_min >= 0.0

    def test_event_timeline_is_dataframe(self, loaded_session):
        _, _, wrapper = loaded_session
        summary = compute_behavior_summary(wrapper)
        assert hasattr(summary.event_timeline, "columns")

    def test_cumulative_presses_structure(self, loaded_session):
        _, _, wrapper = loaded_session
        summary = compute_behavior_summary(wrapper)
        for label, data in summary.cumulative_presses.items():
            assert "time" in data
            assert "count" in data
            assert len(data["time"]) == len(data["count"])


class TestComputeCumulativePresses:
    """Tests for compute_cumulative_presses."""

    def test_with_loaded_session(self, loaded_session):
        _, _, wrapper = loaded_session
        df = wrapper.get_dataframe()
        labels = [l for l in wrapper.get_event_labels() if "press" in l]
        result = compute_cumulative_presses(df, labels)
        for label in labels:
            assert label in result

    def test_empty_label(self, loaded_session):
        _, _, wrapper = loaded_session
        df = wrapper.get_dataframe()
        result = compute_cumulative_presses(df, ["nonexistent_event"])
        assert result["nonexistent_event"]["time"].size == 0

    def test_counts_are_monotonic(self, loaded_session):
        _, _, wrapper = loaded_session
        df = wrapper.get_dataframe()
        labels = [l for l in wrapper.get_event_labels() if "press" in l]
        result = compute_cumulative_presses(df, labels)
        for label, data in result.items():
            if data["count"].size > 1:
                assert np.all(np.diff(data["count"]) >= 0)
