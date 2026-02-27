"""Sidebar layout --- upload zone + preprocessing + peri-event controls.

Builds the full left-hand sidebar column used by the main dashboard layout.
All component IDs follow the project naming convention and are referenced by
the callback modules.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard.layouts.upload import build_upload_zone


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _section_header(text: str) -> html.H6:
    """Return a styled section header."""
    return html.H6(
        text,
        className="text-uppercase text-muted mb-2 mt-3",
    )


def _labeled_input(
    label: str,
    input_id: str,
    default: float | int | str,
    input_type: str = "number",
    **kwargs,
) -> dbc.InputGroup:
    """Return a compact labeled input group."""
    return dbc.InputGroup(
        [
            dbc.InputGroupText(label, className="bg-dark border-secondary text-light small"),
            dbc.Input(
                id=input_id,
                type=input_type,
                value=default,
                className="bg-dark border-secondary text-light",
                **kwargs,
            ),
        ],
        size="sm",
        className="mb-2",
    )


def _labeled_slider(
    label: str,
    slider_id: str,
    min_val: float,
    max_val: float,
    default: float,
    step: float,
    marks: dict | None = None,
) -> html.Div:
    """Return a slider with a label and value badge."""
    if marks is None:
        marks = {min_val: str(min_val), max_val: str(max_val)}
    return html.Div(
        [
            html.Label(label, className="small text-muted mb-1"),
            dcc.Slider(
                id=slider_id,
                min=min_val,
                max=max_val,
                step=step,
                value=default,
                marks=marks,
                tooltip={"placement": "bottom", "always_visible": False},
                className="mb-2",
            ),
        ],
        className="mb-2",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_sidebar() -> html.Div:
    """Assemble the full sidebar column.

    Returns:
        A ``html.Div`` containing the app title, upload zone, session
        configuration, preprocessing controls, and peri-event parameters.
    """
    # -- Title / branding ---------------------------------------------------
    title = html.Div(
        [
            html.H4("Axplorer", className="text-light mb-0"),
            html.Small("Exploratory Data Analysis", className="text-muted"),
        ],
        className="mb-3",
    )

    # -- Upload zone --------------------------------------------------------
    upload = build_upload_zone()

    # -- Session configuration ----------------------------------------------
    session_config = html.Div(
        [
            _section_header("Session Config"),
            _labeled_input("FPS", "input-fps", default=30, min=1, max=1000, step=1),
            _labeled_input("Frame Avg", "input-frame-avg", default=4, min=1, max=100, step=1),
            html.Label("Task Type", className="small text-muted mb-1"),
            dcc.Dropdown(
                id="dropdown-task-type",
                options=[
                    {"label": "Auto-Detect", "value": "auto"},
                    {"label": "Reacher", "value": "reacher"},
                    {"label": "Legacy HER", "value": "legacy_her"},
                    {"label": "Legacy ETH", "value": "legacy_eth"},
                ],
                value="auto",
                clearable=False,
                className="mb-2",
                style={"backgroundColor": "#303030", "color": "#eee"},
            ),
            dbc.Button(
                "Load Session",
                id="btn-load-session",
                color="success",
                size="sm",
                className="w-100 mt-1",
            ),
        ],
    )

    # -- Preprocessing controls ---------------------------------------------
    preprocessing = html.Div(
        [
            _section_header("Preprocessing"),
            dbc.Checklist(
                id="check-dfof",
                options=[{"label": " DF/F", "value": "enabled"}],
                value=["enabled"],
                switch=True,
                className="mb-1",
                inline=True,
            ),
            _labeled_slider(
                label="DF/F Percentile",
                slider_id="slider-dfof-pct",
                min_val=1,
                max_val=50,
                default=8,
                step=1,
                marks={1: "1", 25: "25", 50: "50"},
            ),
            dbc.Checklist(
                id="check-zscore",
                options=[{"label": " Z-Score", "value": "enabled"}],
                value=["enabled"],
                switch=True,
                className="mb-1",
                inline=True,
            ),
            html.Div(
                [
                    html.Label("Z-Score Window (ms)", className="small text-muted mb-1"),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Input(
                                    id="input-zscore-start",
                                    type="number",
                                    value=-3000,
                                    className="bg-dark border-secondary text-light",
                                    size="sm",
                                    placeholder="Start",
                                ),
                            ),
                            dbc.Col(
                                dbc.Input(
                                    id="input-zscore-end",
                                    type="number",
                                    value=-500,
                                    className="bg-dark border-secondary text-light",
                                    size="sm",
                                    placeholder="End",
                                ),
                            ),
                        ],
                        className="g-1 mb-2",
                    ),
                ],
            ),
            dbc.Checklist(
                id="check-smooth",
                options=[{"label": " Smoothing", "value": "enabled"}],
                value=["enabled"],
                switch=True,
                className="mb-1",
                inline=True,
            ),
            _labeled_slider(
                label="Smoothing Sigma",
                slider_id="slider-smooth-sigma",
                min_val=0.5,
                max_val=5,
                default=2,
                step=0.5,
                marks={0.5: "0.5", 2.5: "2.5", 5: "5"},
            ),
        ],
    )

    # -- Peri-event controls ------------------------------------------------
    peri_event = html.Div(
        [
            _section_header("Peri-Event"),
            html.Label("Event", className="small text-muted mb-1"),
            dcc.Dropdown(
                id="dropdown-event",
                placeholder="Select event...",
                clearable=False,
                className="mb-2",
                style={"backgroundColor": "#303030", "color": "#eee"},
            ),
            html.Label("Cells", className="small text-muted mb-1"),
            dcc.Dropdown(
                id="dropdown-cells",
                placeholder="Select cells...",
                multi=True,
                className="mb-2",
                style={"backgroundColor": "#303030", "color": "#eee"},
            ),
            _labeled_slider(
                label="Pre-Event (s)",
                slider_id="slider-pre-event",
                min_val=0.5,
                max_val=10,
                default=5,
                step=0.5,
                marks={0.5: "0.5", 5: "5", 10: "10"},
            ),
            _labeled_slider(
                label="Post-Event (s)",
                slider_id="slider-post-event",
                min_val=0.5,
                max_val=20,
                default=10,
                step=0.5,
                marks={0.5: "0.5", 10: "10", 20: "20"},
            ),
            _labeled_input("Buffer (ms)", "input-buffer-ms", default=0, min=0, step=1),
            _labeled_input("Min Trials", "input-min-trials", default=3, min=1, step=1),
            dbc.Button(
                "Recompute",
                id="btn-recompute",
                color="primary",
                size="sm",
                className="w-100 mt-2",
            ),
        ],
    )

    # -- Assemble -----------------------------------------------------------
    return html.Div(
        [
            title,
            upload,
            html.Hr(className="border-secondary"),
            session_config,
            html.Hr(className="border-secondary"),
            preprocessing,
            html.Hr(className="border-secondary"),
            peri_event,
        ],
    )


__all__ = ["build_sidebar"]
