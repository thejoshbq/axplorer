"""Tests for axplorer.analysis.peth."""

import numpy as np
import pytest

from axplorer.analysis.peth import (
    compute_peth,
    compute_sorted_heatmap,
    compute_trial_raster,
)
from axplorer.types import PETHResult


class TestComputePeth:
    """Tests for compute_peth."""

    def test_basic_computation(self, loaded_session):
        _, meta, wrapper = loaded_session
        # Use active_lever_press (code 22).
        peth = compute_peth(
            session=wrapper,
            event_id=22,
            pre_event_s=2.0,
            post_event_s=5.0,
            min_trials=1,
        )
        assert isinstance(peth, PETHResult)
        assert peth.event_label == "active_lever_press"

    def test_mean_sem_shapes(self, loaded_session):
        _, meta, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper,
            event_id=22,
            pre_event_s=2.0,
            post_event_s=5.0,
            min_trials=1,
        )
        if peth.n_trials > 0:
            assert peth.mean.shape[0] == meta.n_neurons
            assert peth.sem.shape == peth.mean.shape
            assert len(peth.time_axis) == peth.mean.shape[1]

    def test_time_axis_spans_window(self, loaded_session):
        _, _, wrapper = loaded_session
        pre, post = 2.0, 5.0
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=pre, post_event_s=post, min_trials=1,
        )
        if peth.n_trials > 0:
            assert peth.time_axis[0] < 0
            assert peth.time_axis[-1] > 0

    def test_cell_id_subset(self, loaded_session):
        _, _, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=2.0, post_event_s=5.0,
            min_trials=1, cell_ids=[0, 1, 2],
        )
        if peth.n_trials > 0:
            assert peth.mean.shape[0] == 3

    def test_no_trials_returns_empty(self, loaded_session):
        _, _, wrapper = loaded_session
        # Use a very high min_trials to force empty result.
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=2.0, post_event_s=5.0,
            min_trials=10000,
        )
        assert peth.n_trials == 0


class TestComputeSortedHeatmap:
    """Tests for compute_sorted_heatmap."""

    def test_excitatory_sort(self, loaded_session):
        _, _, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=2.0, post_event_s=5.0, min_trials=1,
        )
        if peth.n_trials > 0:
            sorted_mean, indices = compute_sorted_heatmap(peth, sort_method="excitatory")
            assert sorted_mean.shape == peth.mean.shape
            assert len(indices) == peth.mean.shape[0]

    def test_magnitude_sort(self, loaded_session):
        _, _, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=2.0, post_event_s=5.0, min_trials=1,
        )
        if peth.n_trials > 0:
            sorted_mean, indices = compute_sorted_heatmap(peth, sort_method="magnitude")
            # First neuron should have largest absolute response.
            mags = np.max(np.abs(peth.mean), axis=1)
            assert mags[indices[0]] >= mags[indices[-1]]

    def test_invalid_method(self, loaded_session):
        _, _, wrapper = loaded_session
        peth = compute_peth(
            session=wrapper, event_id=22,
            pre_event_s=2.0, post_event_s=5.0, min_trials=1,
        )
        if peth.n_trials > 0:
            with pytest.raises(ValueError, match="Unknown sort_method"):
                compute_sorted_heatmap(peth, sort_method="invalid")


class TestComputeTrialRaster:
    """Tests for compute_trial_raster."""

    def test_basic(self, loaded_session):
        _, _, wrapper = loaded_session
        trials, time = compute_trial_raster(
            session=wrapper, event_id=22, cell_id=0,
            pre_event_s=2.0, post_event_s=5.0, min_trials=1,
        )
        if trials.shape[0] > 0:
            assert trials.ndim == 2
            assert len(time) == trials.shape[1]
