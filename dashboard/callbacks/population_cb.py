"""Population Explorer callbacks --- population PETH computation + visualisation.

Computation is gated by the "Recompute Population" button. Outputs:
grand average trace, population heatmap, response pie, session summary table.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, no_update

from dashboard import state as session_store
from dashboard.theme import FIGURE_TEMPLATE
from axplorer.alignment.session import SessionWrapper
from axplorer.analysis.peth import compute_sorted_heatmap
from axplorer.analysis.population import compute_population_peth
from axplorer.analysis.response import classify_response, compute_response_metrics
from axplorer.types import PETHResult


def register_population_callbacks(app):
    """Register all population-tab callbacks on *app*."""

    # ------------------------------------------------------------------
    # Main callback — compute population PETH
    # ------------------------------------------------------------------
    @app.callback(
        Output("graph-pop-peth-line", "figure"),
        Output("graph-pop-response-pie", "figure"),
        Output("store-pop-peth-data", "data"),
        Output("table-pop-session-summary", "data"),
        Input("btn-pop-recompute", "n_clicks"),
        State("population-token", "data"),
        State("dropdown-event", "value"),
        State("slider-pre-event", "value"),
        State("slider-post-event", "value"),
        State("input-buffer-ms", "value"),
        State("input-min-trials", "value"),
        State("slider-dfof-pct", "value"),
        State("input-zscore-start", "value"),
        State("input-zscore-end", "value"),
        State("slider-smooth-sigma", "value"),
        State("check-dfof", "value"),
        State("check-zscore", "value"),
        State("check-smooth", "value"),
        prevent_initial_call=True,
    )
    def _recompute_population(
        n_clicks,
        pop_token,
        event_label,
        pre_event,
        post_event,
        buffer_ms,
        min_trials,
        dfof_pct,
        zscore_start,
        zscore_end,
        smooth_sigma,
        check_dfof,
        check_zscore,
        check_smooth,
    ):
        if not pop_token or not event_label:
            return (no_update,) * 4

        entries = session_store.get_population(pop_token)
        if entries is None:
            return (no_update,) * 4

        # Extract wrappers.
        wrappers = [wrapper for wrapper, _meta in entries]

        # Resolve parameters with safe defaults.
        pre_event = float(pre_event) if pre_event else 5.0
        post_event = float(post_event) if post_event else 10.0
        buffer_ms = int(buffer_ms) if buffer_ms else 0
        min_trials = int(min_trials) if min_trials else 3
        dfof_pct = float(dfof_pct) if dfof_pct else 8.0
        zscore_start = float(zscore_start) if zscore_start else -3000.0
        zscore_end = float(zscore_end) if zscore_end else -500.0
        smooth_sigma = float(smooth_sigma) if smooth_sigma else 2.0

        # Build shared preprocessing pipeline from the first session.
        pipeline = wrappers[0].build_pipeline(
            dfof_percentile=dfof_pct,
            zscore_window_ms=(zscore_start, zscore_end),
            smoothing_sigma=smooth_sigma,
            enable_dfof=bool(check_dfof),
            enable_zscore=bool(check_zscore),
            enable_smooth=bool(check_smooth),
        )

        # Resolve event code from the first session.
        try:
            event_id = wrappers[0].get_event_code_for_label(event_label)
        except KeyError:
            return (no_update,) * 4

        # Compute population PETH.
        try:
            pop_peth = compute_population_peth(
                sessions=wrappers,
                event_id=event_id,
                pre_event_s=pre_event,
                post_event_s=post_event,
                pipeline=pipeline,
                buffer_ms=buffer_ms,
                min_trials=min_trials,
            )
        except ValueError as exc:
            empty = _empty_figure(str(exc))
            return empty, empty, None, []

        # ── Grand average trace ───────────────────────────────────────────
        fig_line = _build_grand_avg_line(pop_peth)

        # ── Response metrics + classification on pooled neurons ───────────
        # Build a synthetic PETHResult for the pooled data.
        pooled_peth = PETHResult(
            event_windows=np.empty(0),
            time_axis=pop_peth.time_axis,
            mean=pop_peth.pooled_mean,
            sem=np.empty(0),
            event_label=pop_peth.event_label,
            n_trials=pop_peth.total_trials,
            pre_event_s=pop_peth.pre_event_s,
            post_event_s=pop_peth.post_event_s,
        )
        metrics_list = compute_response_metrics(pooled_peth)
        classifications = [classify_response(m) for m in metrics_list]

        counts = {"excitatory": 0, "inhibitory": 0, "non-responsive": 0}
        for c in classifications:
            counts[c] += 1
        fig_pie = _build_response_pie(counts)

        # ── Store PETH data for the sort callback ─────────────────────────
        peth_data = {
            "mean": pop_peth.pooled_mean.tolist(),
            "time_axis": pop_peth.time_axis.tolist(),
            "post_event_s": pop_peth.post_event_s,
        }

        # ── Session summary table ─────────────────────────────────────────
        summary_rows = []
        for i, label in enumerate(pop_peth.session_labels):
            summary_rows.append({
                "session": label,
                "neurons": pop_peth.session_neuron_counts[i],
                "trials": "—",  # per-session trial count not stored individually
            })
        summary_rows.append({
            "session": "TOTAL",
            "neurons": pop_peth.total_neurons,
            "trials": pop_peth.total_trials,
        })

        return fig_line, fig_pie, peth_data, summary_rows

    # ------------------------------------------------------------------
    # Sort callback — instant heatmap re-sort without recomputation
    # ------------------------------------------------------------------
    @app.callback(
        Output("graph-pop-heatmap", "figure"),
        Input("store-pop-peth-data", "data"),
        Input("dropdown-pop-sort-method", "value"),
        prevent_initial_call=True,
    )
    def _update_pop_heatmap(peth_data, sort_method):
        if not peth_data:
            return no_update

        mean = np.array(peth_data["mean"], dtype=np.float32)
        time_axis = np.array(peth_data["time_axis"], dtype=np.float64)
        post_event_s = float(peth_data["post_event_s"])
        sort_method = sort_method or "excitatory"

        peth = PETHResult(
            event_windows=np.empty(0),
            time_axis=time_axis,
            mean=mean,
            sem=np.empty(0),
            event_label="",
            n_trials=0,
            pre_event_s=0.0,
            post_event_s=post_event_s,
        )

        sorted_mean, _ = compute_sorted_heatmap(peth, sort_method=sort_method)
        return _build_sorted_heatmap(sorted_mean, time_axis)


# ──────────────────────────────────────────────────────────────────────────
# Figure builders
# ──────────────────────────────────────────────────────────────────────────

def _empty_figure(message: str) -> go.Figure:
    """Return a blank figure with a centred message annotation."""
    fig = go.Figure()
    fig.update_layout(
        template=FIGURE_TEMPLATE,
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="#888"),
            )
        ],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _build_grand_avg_line(pop_peth) -> go.Figure:
    """Build the grand average trace (mean +/- SEM across sessions)."""
    fig = go.Figure()
    time_axis = pop_peth.time_axis
    grand_mean = pop_peth.grand_mean
    grand_sem = pop_peth.grand_sem
    upper = grand_mean + grand_sem
    lower = grand_mean - grand_sem

    # SEM ribbon.
    fig.add_trace(
        go.Scatter(
            x=time_axis, y=upper, mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=time_axis, y=lower, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(99, 110, 250, 0.2)",
            showlegend=False, hoverinfo="skip",
        )
    )
    # Grand mean line.
    fig.add_trace(
        go.Scatter(
            x=time_axis, y=grand_mean, mode="lines",
            name="Grand Mean",
            line=dict(color="#636EFA", width=2),
        )
    )

    # Overlay per-session means as thin traces.
    for i, label in enumerate(pop_peth.session_labels):
        fig.add_trace(
            go.Scatter(
                x=time_axis, y=pop_peth.session_means[i],
                mode="lines", name=label,
                line=dict(width=0.8), opacity=0.4,
            )
        )

    fig.add_vline(x=0, line=dict(color="white", dash="dash", width=1))

    fig.update_layout(
        template=FIGURE_TEMPLATE,
        xaxis_title="Time from event (s)",
        yaxis_title="Z-Score",
        title=(
            f"{pop_peth.event_label} \u2014 "
            f"{pop_peth.n_sessions} sessions, "
            f"{pop_peth.total_neurons} neurons, "
            f"{pop_peth.total_trials} trials"
        ),
        margin=dict(l=50, r=10, t=40, b=40),
    )
    return fig


def _build_sorted_heatmap(
    sorted_mean: np.ndarray,
    time_axis: np.ndarray,
) -> go.Figure:
    """Build the neuron-sorted population heatmap."""
    fig = go.Figure(
        data=go.Heatmap(
            z=sorted_mean,
            x=time_axis,
            colorscale="RdBu_r",
            zmid=0,
            colorbar=dict(title="Z"),
        )
    )
    fig.add_vline(x=0, line=dict(color="white", dash="dash", width=1))
    fig.update_layout(
        template=FIGURE_TEMPLATE,
        xaxis_title="Time from event (s)",
        yaxis_title="Neuron (sorted)",
        margin=dict(l=50, r=10, t=20, b=40),
    )
    return fig


def _build_response_pie(counts: dict) -> go.Figure:
    """Build a response classification pie chart."""
    labels = list(counts.keys())
    values = list(counts.values())
    colors = {
        "excitatory": "#EF553B",
        "inhibitory": "#636EFA",
        "non-responsive": "#9e9e9e",
    }

    fig = go.Figure(
        data=go.Pie(
            labels=[l.title() for l in labels],
            values=values,
            marker=dict(colors=[colors.get(l, "#aaa") for l in labels]),
            hole=0.4,
            textinfo="label+value",
        )
    )
    fig.update_layout(
        template=FIGURE_TEMPLATE,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
    )
    return fig


__all__ = ["register_population_callbacks"]
