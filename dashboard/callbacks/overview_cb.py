"""Overview callbacks — behavioral summary + signal quality.

Triggered once when a session is loaded (session-token changes). Populates
metric cards, cumulative response plot, event breakdown, event raster, and
signal quality heatmap.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, no_update

from dashboard import state as session_store
from dashboard.theme import FIGURE_TEMPLATE
from axplorer.alignment.session import SessionWrapper
from axplorer.analysis.behavior import compute_behavior_summary


_METADATA_LABELS = {"frame_trigger", "session_start", "session_end"}


def register_overview_callbacks(app):
    """Register all overview-tab callbacks on *app*."""

    @app.callback(
        Output("card-active", "children"),
        Output("card-inactive", "children"),
        Output("card-discrimination", "children"),
        Output("card-reinforcers", "children"),
        Output("graph-cumulative", "figure"),
        Output("graph-event-breakdown", "figure"),
        Output("graph-event-raster", "figure"),
        Output("graph-signal-heatmap", "figure"),
        Input("session-token", "data"),
        prevent_initial_call=True,
    )
    def _update_overview(token):
        if not token:
            return (no_update,) * 8

        session: SessionWrapper | None = session_store.get_session(token)
        if session is None:
            return (no_update,) * 8

        summary = compute_behavior_summary(session)

        # -- Metric cards ---------------------------------------------------
        active_txt = str(summary.active_presses)
        inactive_txt = str(summary.inactive_presses)
        disc_txt = f"{summary.discrimination_index:.2f}"
        reinf_txt = str(summary.reinforcers)

        # -- Cumulative response plot ---------------------------------------
        fig_cum = go.Figure()
        for label, data in summary.cumulative_presses.items():
            if data["time"].size == 0:
                continue
            color = session.get_event_color(label)
            fig_cum.add_trace(
                go.Scatter(
                    x=data["time"] / 60.0,  # convert to minutes
                    y=data["count"],
                    mode="lines",
                    name=label.replace("_", " ").title(),
                    line=dict(color=color, width=2),
                )
            )
        fig_cum.update_layout(
            template=FIGURE_TEMPLATE,
            xaxis_title="Time (min)",
            yaxis_title="Cumulative Count",
            margin=dict(l=50, r=10, t=30, b=40),
        )

        # -- Event breakdown bar chart --------------------------------------
        event_counts = {
            k: v
            for k, v in summary.event_timeline.groupby("label").size().items()
            if k not in _METADATA_LABELS
        }
        labels = list(event_counts.keys())
        counts = list(event_counts.values())
        colors = [session.get_event_color(l) for l in labels]

        fig_breakdown = go.Figure(
            data=[
                go.Bar(
                    x=[l.replace("_", " ").title() for l in labels],
                    y=counts,
                    marker_color=colors,
                )
            ]
        )
        fig_breakdown.update_layout(
            template=FIGURE_TEMPLATE,
            yaxis_title="Count",
            margin=dict(l=50, r=10, t=30, b=40),
            showlegend=False,
        )

        # -- Behavioral event raster ----------------------------------------
        df = summary.event_timeline
        df_plot = df[~df["label"].isin(_METADATA_LABELS)].copy()

        fig_raster = go.Figure()
        for i, label in enumerate(sorted(df_plot["label"].unique())):
            subset = df_plot[df_plot["label"] == label]
            t0 = df["t1"].min()
            times_min = (subset["t1"].values.astype(float) - t0) / 1e6 / 60.0
            fig_raster.add_trace(
                go.Scatter(
                    x=times_min,
                    y=[label.replace("_", " ").title()] * len(times_min),
                    mode="markers",
                    marker=dict(
                        symbol="line-ns",
                        size=12,
                        line=dict(width=1.5, color=session.get_event_color(label)),
                    ),
                    name=label.replace("_", " ").title(),
                    showlegend=False,
                )
            )
        fig_raster.update_layout(
            template=FIGURE_TEMPLATE,
            xaxis_title="Time (min)",
            margin=dict(l=140, r=10, t=20, b=40),
            yaxis=dict(type="category"),
        )

        # -- Signal quality heatmap -----------------------------------------
        signals = session.get_signals()
        # Downsample for display: take every Nth frame to keep ~1000 columns.
        n_frames = signals.shape[1]
        step = max(1, n_frames // 1000)
        display_signals = signals[:, ::step]

        fig_heatmap = go.Figure(
            data=go.Heatmap(
                z=display_signals,
                colorscale="Viridis",
                colorbar=dict(title="F"),
            )
        )
        fig_heatmap.update_layout(
            template=FIGURE_TEMPLATE,
            xaxis_title="Frame (downsampled)",
            yaxis_title="Neuron",
            margin=dict(l=50, r=10, t=20, b=40),
        )

        return (
            active_txt,
            inactive_txt,
            disc_txt,
            reinf_txt,
            fig_cum,
            fig_breakdown,
            fig_raster,
            fig_heatmap,
        )
