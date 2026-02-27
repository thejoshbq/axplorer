"""Explorer callbacks — PETH computation + visualisation.

All expensive computation is gated by the "Recompute" button. Outputs:
PETH line plot, sorted heatmap, response pie, trial raster, metrics table.
"""

from __future__ import annotations

from typing import List

import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, no_update

from dashboard import state as session_store
from dashboard.theme import FIGURE_TEMPLATE
from axplorer.alignment.session import SessionWrapper
from axplorer.analysis.peth import (
    compute_peth,
    compute_sorted_heatmap,
    compute_trial_raster,
)
from axplorer.analysis.response import classify_response, compute_response_metrics


def register_explorer_callbacks(app):
    """Register all explorer-tab callbacks on *app*."""

    # ------------------------------------------------------------------
    # Main callback — expensive PETH computation, stores data for heatmap
    # ------------------------------------------------------------------
    @app.callback(
        Output("graph-peth-line", "figure"),
        Output("graph-response-pie", "figure"),
        Output("graph-trial-raster", "figure"),
        Output("table-response-metrics", "data"),
        Output("store-peth-data", "data"),
        Input("btn-recompute", "n_clicks"),
        State("session-token", "data"),
        State("dropdown-event", "value"),
        State("dropdown-cells", "value"),
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
    def _recompute_explorer(
        n_clicks,
        token,
        event_label,
        cell_ids,
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
        if not token or not event_label:
            return (no_update,) * 5

        session: SessionWrapper | None = session_store.get_session(token)
        if session is None:
            return (no_update,) * 5

        # Resolve parameters with safe defaults.
        pre_event = float(pre_event) if pre_event else 5.0
        post_event = float(post_event) if post_event else 10.0
        buffer_ms = int(buffer_ms) if buffer_ms else 0
        min_trials = int(min_trials) if min_trials else 3
        dfof_pct = float(dfof_pct) if dfof_pct else 8.0
        zscore_start = float(zscore_start) if zscore_start else -3000.0
        zscore_end = float(zscore_end) if zscore_end else -500.0
        smooth_sigma = float(smooth_sigma) if smooth_sigma else 2.0

        # Build preprocessing pipeline.
        pipeline = session.build_pipeline(
            dfof_percentile=dfof_pct,
            zscore_window_ms=(zscore_start, zscore_end),
            smoothing_sigma=smooth_sigma,
            enable_dfof=bool(check_dfof),
            enable_zscore=bool(check_zscore),
            enable_smooth=bool(check_smooth),
        )

        # Resolve event code.
        try:
            event_id = session.get_event_code_for_label(event_label)
        except KeyError:
            return (no_update,) * 5

        # Compute PETH for all neurons.
        peth = compute_peth(
            session=session,
            event_id=event_id,
            pre_event_s=pre_event,
            post_event_s=post_event,
            pipeline=pipeline,
            buffer_ms=buffer_ms,
            min_trials=min_trials,
        )

        if peth.n_trials == 0:
            empty = _empty_figure("No trials found for this event.")
            return empty, empty, empty, [], None

        color = session.get_event_color(event_label)

        # ── PETH line plot ────────────────────────────────────────────────
        fig_peth = _build_peth_line(peth, cell_ids, color)

        # ── Response metrics + classification ─────────────────────────────
        metrics_list = compute_response_metrics(peth)
        classifications = [classify_response(m) for m in metrics_list]

        # Pie chart.
        counts = {"excitatory": 0, "inhibitory": 0, "non-responsive": 0}
        for c in classifications:
            counts[c] += 1
        fig_pie = _build_response_pie(counts)

        # Table data.
        table_data = [
            {
                "cell_id": m.cell_id,
                "peak_zscore": round(m.peak_zscore, 3),
                "peak_latency_s": round(m.peak_latency_s, 3),
                "auc": round(m.auc, 3),
                "onset_latency_s": round(m.onset_latency_s, 3) if m.onset_latency_s is not None else "—",
                "classification": c,
            }
            for m, c in zip(metrics_list, classifications)
        ]

        # ── Trial raster for the first selected cell ─────────────────────
        raster_cell = 0
        if cell_ids:
            raster_cell = int(cell_ids[0]) if isinstance(cell_ids, list) else int(cell_ids)

        trials_mat, raster_time = compute_trial_raster(
            session=session,
            event_id=event_id,
            cell_id=raster_cell,
            pre_event_s=pre_event,
            post_event_s=post_event,
            pipeline=pipeline,
            buffer_ms=buffer_ms,
            min_trials=1,
        )
        fig_raster = _build_trial_raster(trials_mat, raster_time, raster_cell)

        # ── Store PETH data for the sort callback ─────────────────────────
        peth_data = {
            "mean": peth.mean.tolist(),
            "time_axis": peth.time_axis.tolist(),
            "post_event_s": peth.post_event_s,
        }

        return fig_peth, fig_pie, fig_raster, table_data, peth_data

    # ------------------------------------------------------------------
    # Sort callback — instant heatmap re-sort without recomputation
    # ------------------------------------------------------------------
    @app.callback(
        Output("graph-sorted-heatmap", "figure"),
        Input("store-peth-data", "data"),
        Input("dropdown-sort-method", "value"),
        prevent_initial_call=True,
    )
    def _update_sorted_heatmap(peth_data, sort_method):
        if not peth_data:
            return no_update

        mean = np.array(peth_data["mean"], dtype=np.float32)
        time_axis = np.array(peth_data["time_axis"], dtype=np.float64)
        post_event_s = float(peth_data["post_event_s"])
        sort_method = sort_method or "excitatory"

        from axplorer.types import PETHResult

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


def _build_peth_line(
    peth,
    cell_ids: list | None,
    color: str,
) -> go.Figure:
    """Build the PETH mean +/- SEM line plot."""
    fig = go.Figure()

    # If specific cells selected, plot each; else plot grand mean.
    if cell_ids and len(cell_ids) > 0:
        indices = [int(c) for c in cell_ids]
    else:
        indices = list(range(peth.mean.shape[0]))

    if len(indices) <= 10:
        # Individual cell traces.
        for idx in indices:
            mean = peth.mean[idx]
            sem = peth.sem[idx]
            upper = mean + sem
            lower = mean - sem
            fig.add_trace(
                go.Scatter(
                    x=peth.time_axis,
                    y=upper,
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=peth.time_axis,
                    y=lower,
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor=f"rgba({_hex_to_rgb(color)}, 0.15)",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=peth.time_axis,
                    y=mean,
                    mode="lines",
                    name=f"Cell {idx}",
                    line=dict(width=1.5),
                )
            )
    else:
        # Grand average across selected neurons.
        grand_mean = np.nanmean(peth.mean[indices], axis=0)
        grand_sem = np.nanmean(peth.sem[indices], axis=0)
        upper = grand_mean + grand_sem
        lower = grand_mean - grand_sem
        fig.add_trace(
            go.Scatter(x=peth.time_axis, y=upper, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
        )
        fig.add_trace(
            go.Scatter(
                x=peth.time_axis, y=lower, mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor=f"rgba({_hex_to_rgb(color)}, 0.2)",
                showlegend=False, hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(x=peth.time_axis, y=grand_mean, mode="lines", name="Grand Mean", line=dict(color=color, width=2))
        )

    # Event onset line.
    fig.add_vline(x=0, line=dict(color="white", dash="dash", width=1))

    fig.update_layout(
        template=FIGURE_TEMPLATE,
        xaxis_title="Time from event (s)",
        yaxis_title="Z-Score" if peth.mean.shape[0] > 0 else "Activity",
        title=f"{peth.event_label} — {peth.n_trials} trials",
        margin=dict(l=50, r=10, t=40, b=40),
    )
    return fig


def _build_sorted_heatmap(
    sorted_mean: np.ndarray,
    time_axis: np.ndarray,
) -> go.Figure:
    """Build the neuron-sorted heatmap."""
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
    colors = {"excitatory": "#EF553B", "inhibitory": "#636EFA", "non-responsive": "#9e9e9e"}

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


def _build_trial_raster(
    trials_mat: np.ndarray,
    time_axis: np.ndarray,
    cell_id: int,
) -> go.Figure:
    """Build a single-cell trial raster heatmap."""
    if trials_mat.size == 0:
        return _empty_figure(f"No trial data for cell {cell_id}.")

    fig = go.Figure(
        data=go.Heatmap(
            z=trials_mat,
            x=time_axis,
            colorscale="Viridis",
            colorbar=dict(title="Z"),
        )
    )
    fig.add_vline(x=0, line=dict(color="white", dash="dash", width=1))
    fig.update_layout(
        template=FIGURE_TEMPLATE,
        xaxis_title="Time from event (s)",
        yaxis_title="Trial",
        title=f"Cell {cell_id}",
        margin=dict(l=50, r=10, t=40, b=40),
    )
    return fig


def _hex_to_rgb(hex_color: str) -> str:
    """Convert '#RRGGBB' to 'R, G, B' string for rgba()."""
    h = hex_color.lstrip("#")
    if len(h) == 8:
        h = h[:6]  # strip alpha
    return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
