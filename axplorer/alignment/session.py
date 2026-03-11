"""SessionWrapper — convenience API over a Pynapse Sample for dashboard use.

Wraps a ``pynapse.core.Sample`` with UI-friendly helpers for building
preprocessing pipelines from slider values, generating time axes, and
looking up event metadata. Does **not** reimplement any Pynapse logic.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from pynapse.analysis.preprocessing.epoch import (
    DFOverF,
    GaussianSmoothing,
    Pipeline,
    ZScore,
)
from pynapse.analysis.peri_event import SampleEventTensor
from pynapse.config.events import COLORS
from pynapse.core import Sample
from pynapse.db.hydrate import DBSample

_COLOR_OVERRIDES: dict[str, str] = {
    "active_lever_timeout": "#FFC107",
    "timeout_lever_press": "#FFC107",
}


class SessionWrapper:
    """Dashboard-friendly wrapper around a Pynapse Sample.

    Attributes:
        sample: The underlying ``pynapse.core.Sample`` instance.
    """

    def __init__(self, sample: Sample | DBSample) -> None:
        self.sample = sample

        # Pre-compute reverse lookup: label → event code.
        # DBSample exposes get_event_dict() instead of get_event_log().get_code_dict().
        if hasattr(sample, "get_event_log"):
            code_dict = sample.get_event_log().get_code_dict()
        else:
            code_dict = sample.get_event_dict()  # DBSample path
        self._label_to_code: Dict[str, int] = {v: k for k, v in code_dict.items()}
        self._code_to_label: Dict[int, str] = dict(code_dict)

    # ------------------------------------------------------------------
    # Properties delegated to Sample
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self.sample.name

    @property
    def num_neurons(self) -> int:
        return self.sample.num_neurons

    @property
    def num_frames(self) -> int:
        return self.sample.num_frames

    @property
    def num_events(self) -> int:
        return self.sample.num_events

    @property
    def effective_fps(self) -> float:
        return self.sample.effective_fps

    @property
    def duration_s(self) -> float:
        return self.sample.num_frames / self.sample.effective_fps

    # ------------------------------------------------------------------
    # Pipeline construction from UI slider values
    # ------------------------------------------------------------------

    def build_pipeline(
        self,
        dfof_percentile: float = 8.0,
        zscore_window_ms: Tuple[float, float] = (-3000.0, -500.0),
        smoothing_sigma: float = 2.0,
        enable_dfof: bool = True,
        enable_zscore: bool = True,
        enable_smooth: bool = True,
    ) -> Pipeline | None:
        """Construct a Pynapse Pipeline from UI parameter values.

        Args:
            dfof_percentile: Baseline percentile for delta-F / F (1--50).
            zscore_window_ms: (start, end) in ms relative to event onset.
            smoothing_sigma: Gaussian kernel sigma in frames.
            enable_dfof: Whether to include the DF/F step.
            enable_zscore: Whether to include the Z-score step.
            enable_smooth: Whether to include Gaussian smoothing.

        Returns:
            A ``Pipeline`` with the enabled steps, or ``None`` if all
            steps are disabled.
        """
        steps = []

        if enable_dfof:
            steps.append(DFOverF(percentile=dfof_percentile))

        if enable_zscore:
            frame_dur_ms = 1000.0 / self.effective_fps
            steps.append(
                ZScore(
                    window_ms=zscore_window_ms,
                    frame_duration_ms=frame_dur_ms,
                )
            )

        if enable_smooth:
            steps.append(GaussianSmoothing(sigma_frames=smoothing_sigma))

        if not steps:
            return None

        return Pipeline(steps=steps)

    # ------------------------------------------------------------------
    # Tensor extraction (delegates to Sample)
    # ------------------------------------------------------------------

    def get_tensor(
        self,
        event_id: int,
        pre_event_s: float = 5.0,
        post_event_s: float = 10.0,
        pipeline: Pipeline | None = None,
        buffer_ms: int = 0,
        min_trials: int = 3,
    ) -> SampleEventTensor:
        """Extract a peri-event tensor from the underlying Sample.

        Args:
            event_id: Integer event code to lock windows to.
            pre_event_s: Seconds before event onset.
            post_event_s: Seconds after event onset.
            pipeline: Optional preprocessing pipeline (applied per-window).
            buffer_ms: Minimum ms between events; closer events excluded.
            min_trials: Minimum valid trials required.

        Returns:
            A ``SampleEventTensor`` with shape (trials, neurons, time).
        """
        return self.sample.get_tensor(
            event_id=event_id,
            pre_event=pre_event_s,
            post_event=post_event_s,
            window_preprocess=pipeline,
            buffer_ms=buffer_ms,
            min_trials=min_trials,
            use_cache=False,
        )

    # ------------------------------------------------------------------
    # Time axis helper
    # ------------------------------------------------------------------

    def make_time_axis(
        self,
        pre_event_s: float,
        post_event_s: float,
    ) -> NDArray[np.float64]:
        """Generate a time axis array from ``-pre`` to ``+post``.

        Args:
            pre_event_s: Pre-event window in seconds.
            post_event_s: Post-event window in seconds.

        Returns:
            1-D array of time values at ``1 / effective_fps`` spacing.
        """
        dt = 1.0 / self.effective_fps
        n_frames = int(round((pre_event_s + post_event_s) * self.effective_fps))
        return np.linspace(-pre_event_s, post_event_s, n_frames, endpoint=False)

    # ------------------------------------------------------------------
    # Event metadata helpers
    # ------------------------------------------------------------------

    def get_event_labels(self) -> List[str]:
        """Return event labels, excluding 'frame_trigger'.

        Returns:
            Sorted list of human-readable event label strings.
        """
        return sorted(
            label
            for label in self._label_to_code
            if label != "frame_trigger"
        )

    def get_event_code_for_label(self, label: str) -> int:
        """Look up the integer event code for a given label.

        Args:
            label: Human-readable event label.

        Returns:
            The corresponding integer event code.

        Raises:
            KeyError: If the label is not found in the event dictionary.
        """
        return self._label_to_code[label]

    def get_event_color(self, label: str) -> str:
        """Return the color associated with an event label.

        Falls back to a neutral gray if the label has no assigned color.
        Converts 8-char hex (``#RRGGBBAA``) to ``rgba()`` for Plotly
        compatibility.

        Args:
            label: Human-readable event label.

        Returns:
            Color string in 6-char hex or ``rgba()`` format.
        """
        color = _COLOR_OVERRIDES.get(label) or COLORS.get(label, "#9e9e9e")
        if len(color) == 9 and color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            a = round(int(color[7:9], 16) / 255, 2)
            return f"rgba({r},{g},{b},{a})"
        return color

    def get_signals(self) -> NDArray:
        """Return the raw signal matrix (neurons x frames).

        Returns:
            2-D numpy array of fluorescence values.
        """
        return self.sample.get_signals()

    def get_dataframe(self):
        """Return the event DataFrame with frame-aligned indices.

        Returns:
            ``pandas.DataFrame`` with columns including ``code``, ``label``,
            ``t1``, ``t2``, and ``frame_index``.
        """
        return self.sample.get_dataframe()
