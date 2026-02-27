"""Export callbacks — figure and data download.

Handles the Export tab: figure preview selection, figure download (PNG/SVG/PDF),
and data download (CSV / HDF5).
"""

from __future__ import annotations

import json

from dash import Input, Output, State, callback_context, no_update

from dashboard import state as session_store
from axplorer.alignment.session import SessionWrapper
from axplorer.analysis.peth import compute_peth
from axplorer.export.data import export_peth_csv, export_session_hdf5
from axplorer.export.figures import export_figure
from axplorer.types import SessionMetadata


# Mapping of export-source dropdown values → graph component IDs.
_SOURCE_MAP = {
    "graph-peth-line": "graph-peth-line",
    "graph-sorted-heatmap": "graph-sorted-heatmap",
    "graph-trial-raster": "graph-trial-raster",
    "graph-cumulative": "graph-cumulative",
    "graph-event-breakdown": "graph-event-breakdown",
}


def register_export_callbacks(app):
    """Register all export-tab callbacks on *app*."""

    # ------------------------------------------------------------------
    # Figure preview — mirrors the selected source graph
    # ------------------------------------------------------------------
    @app.callback(
        Output("graph-export-preview", "figure"),
        Input("dropdown-export-source", "value"),
        State("graph-peth-line", "figure"),
        State("graph-sorted-heatmap", "figure"),
        State("graph-trial-raster", "figure"),
        State("graph-cumulative", "figure"),
        State("graph-event-breakdown", "figure"),
        prevent_initial_call=True,
    )
    def _update_preview(source, fig_peth, fig_hm, fig_raster, fig_cum, fig_bd):
        figs = {
            "graph-peth-line": fig_peth,
            "graph-sorted-heatmap": fig_hm,
            "graph-trial-raster": fig_raster,
            "graph-cumulative": fig_cum,
            "graph-event-breakdown": fig_bd,
        }
        selected = figs.get(source)
        if selected is None:
            return no_update
        return selected

    # ------------------------------------------------------------------
    # Download figure
    # ------------------------------------------------------------------
    @app.callback(
        Output("download-figure", "data"),
        Input("btn-download-figure", "n_clicks"),
        State("graph-export-preview", "figure"),
        State("radio-export-format", "value"),
        State("input-export-width", "value"),
        State("input-export-height", "value"),
        State("input-export-scale", "value"),
        State("dropdown-export-source", "value"),
        prevent_initial_call=True,
    )
    def _download_figure(
        n_clicks, figure, fmt, width, height, scale, source_name
    ):
        if not figure:
            return no_update

        import plotly.graph_objects as go

        fig = go.Figure(figure)

        fmt = fmt or "png"
        width = int(width) if width else 1200
        height = int(height) if height else 800
        scale = int(scale) if scale else 2

        img_bytes = export_figure(
            fig=fig,
            fmt=fmt,
            width=width,
            height=height,
            scale=scale,
        )

        safe_name = (source_name or "figure").replace("-", "_")
        filename = f"{safe_name}.{fmt}"

        if fmt == "svg":
            # SVG is text, send as string.
            return dict(content=img_bytes.decode("utf-8"), filename=filename)
        else:
            import base64

            return dict(
                content=base64.b64encode(img_bytes).decode("ascii"),
                filename=filename,
                base64=True,
            )

    # ------------------------------------------------------------------
    # Download data (CSV and/or HDF5)
    # ------------------------------------------------------------------
    @app.callback(
        Output("download-data", "data"),
        Input("btn-download-data", "n_clicks"),
        State("session-token", "data"),
        State("session-metadata", "data"),
        State("check-export-csv", "value"),
        State("check-export-hdf5", "value"),
        State("dropdown-event", "value"),
        State("slider-pre-event", "value"),
        State("slider-post-event", "value"),
        State("slider-dfof-pct", "value"),
        State("input-zscore-start", "value"),
        State("input-zscore-end", "value"),
        State("slider-smooth-sigma", "value"),
        State("check-dfof", "value"),
        State("check-zscore", "value"),
        State("check-smooth", "value"),
        State("input-buffer-ms", "value"),
        State("input-min-trials", "value"),
        prevent_initial_call=True,
    )
    def _download_data(
        n_clicks,
        token,
        meta_dict,
        csv_check,
        hdf5_check,
        event_label,
        pre_event,
        post_event,
        dfof_pct,
        zscore_start,
        zscore_end,
        smooth_sigma,
        check_dfof,
        check_zscore,
        check_smooth,
        buffer_ms,
        min_trials,
    ):
        if not token or not meta_dict:
            return no_update

        want_csv = bool(csv_check)
        want_hdf5 = bool(hdf5_check)

        if not want_csv and not want_hdf5:
            return no_update

        session: SessionWrapper | None = session_store.get_session(token)
        if session is None:
            return no_update

        # Rebuild metadata from the stored dict.
        metadata = SessionMetadata(**meta_dict)

        # Build pipeline and compute PETH for the selected event.
        pipeline = session.build_pipeline(
            dfof_percentile=float(dfof_pct or 8),
            zscore_window_ms=(float(zscore_start or -3000), float(zscore_end or -500)),
            smoothing_sigma=float(smooth_sigma or 2),
            enable_dfof=bool(check_dfof),
            enable_zscore=bool(check_zscore),
            enable_smooth=bool(check_smooth),
        )

        pre = float(pre_event or 5)
        post = float(post_event or 10)
        buf = int(buffer_ms or 0)
        mt = int(min_trials or 3)

        if event_label:
            event_id = session.get_event_code_for_label(event_label)
            peth = compute_peth(
                session, event_id, pre, post, pipeline, buf, mt
            )
        else:
            peth = None

        # Prefer CSV; fall back to HDF5.
        if want_csv and peth is not None and peth.n_trials > 0:
            csv_str = export_peth_csv(peth)
            return dict(content=csv_str, filename=f"peth_{event_label}.csv")

        if want_hdf5:
            import base64

            peth_dict = {}
            if peth is not None and peth.n_trials > 0:
                peth_dict[event_label] = peth
            hdf5_bytes = export_session_hdf5(metadata, peth_dict)
            return dict(
                content=base64.b64encode(hdf5_bytes).decode("ascii"),
                filename=f"{metadata.name}_session.h5",
                base64=True,
            )

        return no_update
