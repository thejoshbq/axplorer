"""Figure export utilities."""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go


def export_figure(
    fig: go.Figure,
    path: str | Path | None = None,
    fmt: str = "png",
    width: int = 1200,
    height: int = 800,
    scale: int = 2,
) -> bytes | None:
    """Export a Plotly figure to PNG, SVG, or PDF.

    Args:
        fig: Plotly figure to export.
        path: Output file path. If None, returns raw bytes.
        fmt: Format --- ``'png'``, ``'svg'``, or ``'pdf'``.
        width: Figure width in pixels.
        height: Figure height in pixels.
        scale: Resolution scale factor (applied to raster formats only).

    Returns:
        Image bytes when *path* is None, otherwise None (writes to file).

    Raises:
        ValueError: If *fmt* is not one of the supported formats.
    """
    supported = {"png", "svg", "pdf"}
    fmt = fmt.lower()
    if fmt not in supported:
        raise ValueError(
            f"Unsupported format '{fmt}'. Choose from {sorted(supported)}."
        )

    img_bytes: bytes = fig.to_image(
        format=fmt,
        width=width,
        height=height,
        scale=scale,
    )

    if path is None:
        return img_bytes

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(img_bytes)
    return None
