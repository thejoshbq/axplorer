"""Export router -- figure and data downloads."""

from __future__ import annotations

import logging

import numpy as np
import plotly.graph_objects as go
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import Response

from axplorer.export.figures import export_figure
from axplorer.export.data import export_peth_csv, export_session_hdf5
from api.routers.upload import get_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["export"])

COLOR_PALETTE = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


class FigureExportRequest(BaseModel):
    plots: list[dict]
    y_range: list[float]
    z_range: list[float] = [0.0, 1.0]
    event_label: str
    fmt: str = "png"
    dark: bool = True


class DataExportRequest(BaseModel):
    event_label: str
    fmt: str = "csv"
    pre_event_s: float = 5.0
    post_event_s: float = 10.0
    enable_dfof: bool = True
    dfof_percentile: float = 8.0
    enable_zscore: bool = True
    enable_smooth: bool = True
    smoothing_sigma: float = 2.0
    buffer_ms: int = 0
    min_trials: int = 3


@router.post("/figure")
def export_figure_endpoint(req: FigureExportRequest) -> Response:
    """Build Plotly figures server-side and export as image."""
    from math import ceil

    if not req.plots:
        return Response(content=b"", media_type="application/octet-stream")

    ncols = min(len(req.plots), 3)
    has_heatmap = any(p.get("heatmap") for p in req.plots)
    rows_per_plot = 2 if has_heatmap else 1
    nrows = ceil(len(req.plots) / ncols) * rows_per_plot

    # Theme colors
    if req.dark:
        paper_bg = "rgb(14,18,20)"
        font_color = "rgb(210,245,245)"
        grid_color = "rgb(30,40,45)"
        vline_color = "white"
    else:
        paper_bg = "rgb(250,253,253)"
        font_color = "rgb(10,20,20)"
        grid_color = "rgb(220,230,230)"
        vline_color = "black"

    from plotly.subplots import make_subplots

    # Build subplot titles and specs.
    subplot_titles: list[str] = []
    row_heights: list[float] = []
    logical_rows = ceil(len(req.plots) / ncols)
    for lr in range(logical_rows):
        subplot_titles.extend(
            req.plots[lr * ncols + c]["title"] if lr * ncols + c < len(req.plots) else ""
            for c in range(ncols)
        )
        row_heights.append(0.6 if has_heatmap else 1.0)
        if has_heatmap:
            subplot_titles.extend("" for _ in range(ncols))
            row_heights.append(0.4)

    fig = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=subplot_titles,
        shared_xaxes=has_heatmap,
        row_heights=row_heights,
        horizontal_spacing=0.06,
        vertical_spacing=0.08,
    )

    for idx, pdata in enumerate(req.plots):
        logical_row = idx // ncols
        col = idx % ncols + 1
        line_row = logical_row * rows_per_plot + 1
        time = np.array(pdata["time"])
        mean = np.array(pdata["mean"])
        sem = np.array(pdata["sem"])
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]

        # SEM fill
        fig.add_trace(go.Scatter(
            x=np.concatenate([time, time[::-1]]).tolist(),
            y=np.concatenate([mean + sem, (mean - sem)[::-1]]).tolist(),
            fill="toself",
            fillcolor=_hex_to_rgba(color, 0.2),
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        ), row=line_row, col=col)

        # Mean line
        fig.add_trace(go.Scatter(
            x=time.tolist(),
            y=mean.tolist(),
            mode="lines",
            line=dict(color=color, width=1.5),
            showlegend=False,
        ), row=line_row, col=col)

        # Event onset vline
        fig.add_vline(x=0, line_dash="dash", line_color=vline_color, opacity=0.6,
                      line_width=0.8, row=line_row, col=col)

        fig.update_yaxes(range=req.y_range, row=line_row, col=col)

        # Heatmap row
        heatmap_data = pdata.get("heatmap")
        if has_heatmap and heatmap_data:
            heatmap_row = line_row + 1
            fig.add_trace(go.Heatmap(
                z=heatmap_data["z"],
                x=time.tolist(),
                y=heatmap_data.get("neuron_labels", []),
                zmin=req.z_range[0] if len(req.z_range) == 2 else None,
                zmax=req.z_range[1] if len(req.z_range) == 2 else None,
                colorscale="Viridis",
                showscale=idx == 0,
                colorbar=dict(
                    title="Activity", titlefont=dict(color=font_color, size=10),
                    tickfont=dict(color=font_color, size=9),
                ),
            ), row=heatmap_row, col=col)
            fig.add_vline(x=0, line_dash="dash", line_color=vline_color, opacity=0.6,
                          line_width=0.8, row=heatmap_row, col=col)

    fig.update_layout(
        paper_bgcolor=paper_bg,
        plot_bgcolor=paper_bg,
        font=dict(color=font_color, family="JetBrains Mono, monospace", size=11),
        title=dict(text=f"PETH: {req.event_label}", font=dict(size=14)),
        width=400 * ncols,
        height=(350 * rows_per_plot) * logical_rows + 60,
    )
    fig.update_xaxes(gridcolor=grid_color, title_text="Time (s)")
    fig.update_yaxes(gridcolor=grid_color)

    fmt = req.fmt.lower()
    content_types = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}

    img_bytes = export_figure(fig, path=None, fmt=fmt)
    return Response(
        content=img_bytes,
        media_type=content_types.get(fmt, "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="axplorer_peth.{fmt}"'},
    )


@router.post("/data")
def export_data_endpoint(req: DataExportRequest) -> Response:
    """Export raw PETH data as CSV or HDF5."""
    from axplorer.analysis.peth import compute_peth

    store = get_store()
    if not store.all_wrappers or not req.event_label:
        return Response(content=b"", media_type="application/octet-stream")

    ref_wrapper = store.all_wrappers[0]
    pipeline = ref_wrapper.build_pipeline(
        dfof_percentile=req.dfof_percentile,
        enable_dfof=req.enable_dfof,
        enable_zscore=req.enable_zscore,
        enable_smooth=req.enable_smooth,
        smoothing_sigma=req.smoothing_sigma,
    )
    event_code = ref_wrapper.get_event_code_for_label(req.event_label)

    # Compute PETH for the first wrapper as representative export.
    peth = compute_peth(
        session=ref_wrapper,
        event_id=event_code,
        pre_event_s=req.pre_event_s,
        post_event_s=req.post_event_s,
        pipeline=pipeline,
        buffer_ms=req.buffer_ms,
        min_trials=req.min_trials,
    )

    fmt = req.fmt.lower()
    if fmt == "csv":
        csv_str = export_peth_csv(peth, path=None)
        return Response(
            content=csv_str.encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="axplorer_peth.csv"'},
        )
    elif fmt == "hdf5":
        metadata = ref_wrapper.get_metadata()
        hdf5_bytes = export_session_hdf5(
            metadata=metadata,
            peth_results={req.event_label: peth},
            path=None,
        )
        return Response(
            content=hdf5_bytes,
            media_type="application/x-hdf5",
            headers={"Content-Disposition": 'attachment; filename="axplorer_session.h5"'},
        )

    return Response(content=b"Unsupported format", status_code=400)
