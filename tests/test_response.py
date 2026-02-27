"""Tests for axplorer.analysis.response."""

import numpy as np
import pytest

from axplorer.analysis.peth import compute_peth
from axplorer.analysis.response import classify_response, compute_response_metrics
from axplorer.types import ResponseMetrics


class TestComputeResponseMetrics:
    """Tests for compute_response_metrics."""

    def test_returns_per_neuron(self, loaded_session):
        _, meta, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=1.0, post_event_s=2.0, min_trials=1,
        )
        if peth.n_trials == 0:
            pytest.skip("No trials available for test.")

        metrics = compute_response_metrics(peth)
        assert len(metrics) == meta.n_neurons
        assert all(isinstance(m, ResponseMetrics) for m in metrics)

    def test_cell_ids_sequential(self, loaded_session):
        _, _, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=1.0, post_event_s=2.0, min_trials=1,
        )
        if peth.n_trials == 0:
            pytest.skip("No trials available.")

        metrics = compute_response_metrics(peth)
        ids = [m.cell_id for m in metrics]
        assert ids == list(range(len(metrics)))

    def test_peak_latency_in_window(self, loaded_session):
        _, _, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=1.0, post_event_s=2.0, min_trials=1,
        )
        if peth.n_trials == 0:
            pytest.skip("No trials available.")

        metrics = compute_response_metrics(
            peth, response_window_s=(0.0, 2.0),
        )
        for m in metrics:
            assert 0.0 <= m.peak_latency_s <= 2.0


class TestClassifyResponse:
    """Tests for classify_response."""

    def test_excitatory(self):
        m = ResponseMetrics(
            cell_id=0, peak_zscore=3.5, peak_latency_s=1.0,
            auc=10.0, onset_latency_s=0.5, mean_baseline=0.0,
            mean_response=2.0,
        )
        assert classify_response(m) == "excitatory"

    def test_inhibitory(self):
        m = ResponseMetrics(
            cell_id=0, peak_zscore=-3.0, peak_latency_s=1.0,
            auc=-5.0, onset_latency_s=0.8, mean_baseline=0.0,
            mean_response=-1.0,
        )
        assert classify_response(m) == "inhibitory"

    def test_non_responsive(self):
        m = ResponseMetrics(
            cell_id=0, peak_zscore=0.5, peak_latency_s=1.0,
            auc=0.1, onset_latency_s=None, mean_baseline=0.0,
            mean_response=0.1,
        )
        assert classify_response(m) == "non-responsive"

    def test_custom_thresholds(self):
        m = ResponseMetrics(
            cell_id=0, peak_zscore=1.5, peak_latency_s=1.0,
            auc=2.0, onset_latency_s=0.5, mean_baseline=0.0,
            mean_response=1.0,
        )
        # Default threshold (2.0) → non-responsive.
        assert classify_response(m) == "non-responsive"
        # Lower threshold → excitatory.
        assert classify_response(m, exc_threshold=1.0) == "excitatory"
