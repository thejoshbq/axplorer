"""Upload zone layout --- drag-drop areas for signal and event files.

Supports two modes toggled by a radio selector:

- **File Pair:** Manual drag-drop of individual ``.npy`` + ``.mat/.xlsx`` files.
- **Directory:** Scan a hierarchical data directory and select sessions from
  a table.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard.layouts.directory import build_directory_zone


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------

_DROP_ZONE_STYLE: dict = {
    "borderWidth": "2px",
    "borderStyle": "dashed",
    "borderColor": "#555",
    "borderRadius": "8px",
    "textAlign": "center",
    "padding": "24px 12px",
    "cursor": "pointer",
    "transition": "border-color 0.2s ease",
    "marginBottom": "10px",
    "backgroundColor": "rgba(255, 255, 255, 0.03)",
}


def _upload_icon() -> html.I:
    """Return a Bootstrap upload icon element."""
    return html.I(className="bi bi-cloud-arrow-up", style={"fontSize": "2rem", "color": "#888"})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_upload_zone() -> html.Div:
    """Build the file-upload section with a mode toggle.

    Returns:
        A ``html.Div`` containing:
        - A radio toggle to switch between "File Pair" and "Directory" modes.
        - The file-pair drag-drop zones (visible by default).
        - The directory scan zone (hidden by default).
    """
    mode_toggle = dbc.RadioItems(
        id="radio-upload-mode",
        options=[
            {"label": "File Pair", "value": "file-pair"},
            {"label": "Directory", "value": "directory"},
        ],
        value="file-pair",
        inline=True,
        className="mb-2 small",
    )

    # -- File pair mode (existing drag-drop zones) --------------------------
    signal_upload = dcc.Upload(
        id="upload-signal",
        accept=".npy",
        children=html.Div(
            [
                _upload_icon(),
                html.P(
                    "Drop .npy signal file",
                    className="mt-2 mb-0 text-muted small",
                ),
            ],
        ),
        style=_DROP_ZONE_STYLE,
        multiple=False,
    )

    event_upload = dcc.Upload(
        id="upload-events",
        accept=".xlsx,.mat",
        children=html.Div(
            [
                _upload_icon(),
                html.P(
                    "Drop .xlsx / .mat event file",
                    className="mt-2 mb-0 text-muted small",
                ),
            ],
        ),
        style=_DROP_ZONE_STYLE,
        multiple=False,
    )

    status = html.Div(id="upload-status", className="small text-info mt-1")

    file_pair_div = html.Div(
        id="div-file-pair-upload",
        children=[signal_upload, event_upload, status],
        style={"display": "block"},
    )

    # -- Directory mode -----------------------------------------------------
    directory_div = html.Div(
        id="div-directory-upload",
        children=[build_directory_zone()],
        style={"display": "none"},
    )

    return html.Div(
        [
            html.H6("Files", className="text-uppercase text-muted mb-2"),
            mode_toggle,
            file_pair_div,
            directory_div,
        ],
    )


__all__ = ["build_upload_zone"]
