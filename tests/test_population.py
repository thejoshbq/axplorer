"""Tests for axplorer.analysis.population."""

from __future__ import annotations

from math import sqrt
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from axplorer.analysis.population import compute_population_peth
from axplorer.types import PETHResult


# ---------------------------------------------------------------------------
# Helpers — mock SessionWrapper that returns controlled PETHResults
# ---------------------------------------------------------------------------

def _make_mock_session(
    name: str,
    n_neurons: int,
    n_trials: int,
    n_time: int,
    effective_fps: float,
    mean_value: float = 1.0,
) -> MagicMock:
    """Build a mock SessionWrapper with controlled properties.

    Args:
        name: Session name.
        n_neurons: Number of neurons in the mock PETH.
        n_trials: Number of trials for the PETH.
        n_time: Number of time bins.
        effective_fps: Effective FPS of the session.
        mean_value: Fill value for the mean matrix (useful for testing averages).

    Returns:
        A MagicMock configured as a SessionWrapper.
    """
    mock = MagicMock()
    mock.name = name
    mock.effective_fps = effective_fps
    return mock


def _make_peth(
    n_neurons: int,
    n_trials: int,
    n_time: int,
    mean_value: float = 1.0,
    pre_event_s: float = 5.0,
    post_event_s: float = 10.0,
) -> PETHResult:
    """Build a synthetic PETHResult with controlled values."""
    mean = np.full((n_neurons, n_time), mean_value, dtype=np.float32)
    sem = np.full((n_neurons, n_time), 0.1, dtype=np.float32)
    time_axis = np.linspace(-pre_event_s, post_event_s, n_time, endpoint=False)
    windows = np.zeros((n_trials, n_neurons, n_time), dtype=np.float32)

    return PETHResult(
        event_windows=windows,
        time_axis=time_axis,
        mean=mean,
        sem=sem,
        event_label="test_event",
        n_trials=n_trials,
        pre_event_s=pre_event_s,
        post_event_s=post_event_s,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestComputePopulationPeth:
    """Tests for compute_population_peth."""

    N_TIME = 100
    PRE = 5.0
    POST = 10.0
    FPS = 7.5

    def _run(self, session_specs, **kwargs):
        """Helper: build mocks + patch compute_peth, then call compute_population_peth.

        Args:
            session_specs: List of (name, n_neurons, n_trials, mean_value) tuples.
            **kwargs: Extra keyword arguments passed to compute_population_peth.

        Returns:
            The PopulationPETHResult.
        """
        sessions = []
        peths = []
        for name, n_neurons, n_trials, mean_val in session_specs:
            mock = _make_mock_session(
                name=name,
                n_neurons=n_neurons,
                n_trials=n_trials,
                n_time=self.N_TIME,
                effective_fps=self.FPS,
                mean_value=mean_val,
            )
            sessions.append(mock)
            peths.append(
                _make_peth(
                    n_neurons=n_neurons,
                    n_trials=n_trials,
                    n_time=self.N_TIME,
                    mean_value=mean_val,
                    pre_event_s=self.PRE,
                    post_event_s=self.POST,
                )
            )

        peth_iter = iter(peths)

        with patch(
            "axplorer.analysis.population.compute_peth",
            side_effect=lambda **kw: next(peth_iter),
        ):
            return compute_population_peth(
                sessions=sessions,
                event_id=1,
                pre_event_s=self.PRE,
                post_event_s=self.POST,
                **kwargs,
            )

    # -- Core pooling tests ------------------------------------------------

    def test_pools_neurons_across_sessions(self):
        """2 sessions x 5 neurons = 10 rows in pooled_mean."""
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 5, 8, 2.0),
        ])
        assert result.pooled_mean.shape == (10, self.N_TIME)
        assert result.total_neurons == 10

    def test_session_means_shape(self):
        """session_means should be (n_sessions, time)."""
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 3, 8, 2.0),
            ("sess_c", 7, 12, 3.0),
        ])
        assert result.session_means.shape == (3, self.N_TIME)

    def test_grand_mean_from_session_averaging(self):
        """Grand mean should be the mean across sessions, not across neurons."""
        # Session A: 5 neurons all with mean_value=1.0 → session mean trace = 1.0
        # Session B: 5 neurons all with mean_value=3.0 → session mean trace = 3.0
        # Grand mean should be (1.0 + 3.0) / 2 = 2.0 (session-level average)
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 5, 8, 3.0),
        ])
        np.testing.assert_allclose(result.grand_mean, 2.0, atol=1e-5)

    def test_grand_sem_uses_n_sessions(self):
        """SEM denominator should be sqrt(n_sessions), not sqrt(total_neurons)."""
        # Session A mean = 1.0, Session B mean = 3.0
        # std(ddof=1) across [1.0, 3.0] = sqrt(2), sem = sqrt(2)/sqrt(2) = 1.0
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 5, 8, 3.0),
        ])
        expected_sem = np.std([1.0, 3.0], ddof=1) / sqrt(2)
        np.testing.assert_allclose(result.grand_sem, expected_sem, atol=1e-5)

    # -- Metadata tests ----------------------------------------------------

    def test_session_labels_preserved(self):
        """Session labels should match input session names."""
        result = self._run([
            ("alpha", 5, 10, 1.0),
            ("beta", 3, 8, 2.0),
        ])
        assert result.session_labels == ["alpha", "beta"]

    def test_session_neuron_counts(self):
        """Neuron counts should reflect each session's contribution."""
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 3, 8, 2.0),
        ])
        assert result.session_neuron_counts == [5, 3]

    def test_total_trials_summed(self):
        """Total trials should be the sum across sessions."""
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 5, 8, 2.0),
        ])
        assert result.total_trials == 18

    def test_n_sessions(self):
        """n_sessions should match the number of input sessions."""
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 5, 8, 2.0),
            ("sess_c", 5, 6, 3.0),
        ])
        assert result.n_sessions == 3

    # -- Edge cases --------------------------------------------------------

    def test_mismatched_fps_raises(self):
        """ValueError should be raised if FPS differs across sessions."""
        mock_a = _make_mock_session("a", 5, 10, 100, effective_fps=7.5)
        mock_b = _make_mock_session("b", 5, 10, 100, effective_fps=15.0)

        with pytest.raises(ValueError, match="effective_fps"):
            compute_population_peth(
                sessions=[mock_a, mock_b],
                event_id=1,
            )

    def test_single_session_degenerates(self):
        """Should work with a single session — grand_sem is zeros."""
        result = self._run([
            ("solo", 5, 10, 2.5),
        ])
        assert result.n_sessions == 1
        assert result.total_neurons == 5
        np.testing.assert_allclose(result.grand_mean, 2.5, atol=1e-5)
        np.testing.assert_allclose(result.grand_sem, 0.0, atol=1e-5)

    def test_empty_sessions_raises(self):
        """ValueError for empty session list."""
        with pytest.raises(ValueError, match="At least one session"):
            compute_population_peth(sessions=[], event_id=1)

    def test_time_axis_propagated(self):
        """Time axis from the first session should be used."""
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 5, 8, 2.0),
        ])
        expected = np.linspace(-self.PRE, self.POST, self.N_TIME, endpoint=False)
        np.testing.assert_allclose(result.time_axis, expected, atol=1e-5)

    def test_event_label_from_first_session(self):
        """Event label should come from the first session's PETH."""
        result = self._run([
            ("sess_a", 5, 10, 1.0),
            ("sess_b", 5, 8, 2.0),
        ])
        assert result.event_label == "test_event"
