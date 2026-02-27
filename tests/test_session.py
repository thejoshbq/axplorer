"""Tests for axplorer.alignment.session.SessionWrapper."""

import numpy as np
import pytest

from axplorer.alignment.session import SessionWrapper


class TestSessionWrapper:
    """Tests for SessionWrapper convenience methods."""

    def test_properties(self, loaded_session):
        _, meta, wrapper = loaded_session
        assert wrapper.num_neurons == meta.n_neurons
        assert wrapper.num_frames == meta.n_frames
        assert wrapper.effective_fps == pytest.approx(meta.effective_fps)
        assert wrapper.duration_s > 0

    def test_get_event_labels(self, loaded_session):
        _, _, wrapper = loaded_session
        labels = wrapper.get_event_labels()
        assert isinstance(labels, list)
        assert "frame_trigger" not in labels
        assert len(labels) > 0

    def test_get_event_code_roundtrip(self, loaded_session):
        _, _, wrapper = loaded_session
        for label in wrapper.get_event_labels():
            code = wrapper.get_event_code_for_label(label)
            assert isinstance(code, int)

    def test_get_event_code_missing(self, loaded_session):
        _, _, wrapper = loaded_session
        with pytest.raises(KeyError):
            wrapper.get_event_code_for_label("nonexistent_event")

    def test_get_event_color(self, loaded_session):
        _, _, wrapper = loaded_session
        color = wrapper.get_event_color("active_lever_press")
        assert color.startswith("#")

    def test_get_event_color_fallback(self, loaded_session):
        _, _, wrapper = loaded_session
        color = wrapper.get_event_color("unknown_event")
        assert color == "#9e9e9e"

    def test_make_time_axis(self, loaded_session):
        _, _, wrapper = loaded_session
        t = wrapper.make_time_axis(pre_event_s=2.0, post_event_s=5.0)
        assert t[0] == pytest.approx(-2.0, abs=0.2)
        assert t[-1] < 5.0
        assert len(t) > 0
        dt = np.diff(t)
        assert np.allclose(dt, dt[0], atol=1e-6)

    def test_build_pipeline_all_enabled(self, loaded_session):
        _, _, wrapper = loaded_session
        pipe = wrapper.build_pipeline(
            dfof_percentile=8, smoothing_sigma=2, enable_dfof=True,
            enable_zscore=True, enable_smooth=True,
        )
        assert pipe is not None

    def test_build_pipeline_all_disabled(self, loaded_session):
        _, _, wrapper = loaded_session
        pipe = wrapper.build_pipeline(
            enable_dfof=False, enable_zscore=False, enable_smooth=False,
        )
        assert pipe is None

    def test_get_signals(self, loaded_session):
        _, meta, wrapper = loaded_session
        signals = wrapper.get_signals()
        assert signals.shape == (meta.n_neurons, meta.n_frames)

    def test_get_dataframe(self, loaded_session):
        _, _, wrapper = loaded_session
        df = wrapper.get_dataframe()
        assert "label" in df.columns or "code" in df.columns
        assert len(df) > 0
