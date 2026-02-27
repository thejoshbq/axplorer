"""Export tab layout --- figure preview + format controls + data export.

Provides the ``build_export_tab`` factory that renders figure and data
export controls used by the Export callbacks.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html


# ---------------------------------------------------------------------------
# Source options available for figure export
# ---------------------------------------------------------------------------

_FIGURE_SOURCE_OPTIONS = [
    {"label": "PETH Line", "value": "graph-peth-line"},
    {"label": "Sorted Heatmap", "value": "graph-sorted-heatmap"},
    {"label": "Trial Raster", "value": "graph-trial-raster"},
    {"label": "Cumulative", "value": "graph-cumulative"},
    {"label": "Event Breakdown", "value": "graph-event-breakdown"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _labeled_input(
    label: str,
    input_id: str,
    default: int | float,
    **kwargs,
) -> dbc.InputGroup:
    """Return a compact labeled numeric input group.

    Args:
        label: Text shown in the prepend badge.
        input_id: Dash component ID.
        default: Default numeric value.
        **kwargs: Forwarded to ``dbc.Input``.

    Returns:
        A ``dbc.InputGroup`` for the setting.
    """
    return dbc.InputGroup(
        [
            dbc.InputGroupText(
                label,
                className="bg-dark border-secondary text-light small",
            ),
            dbc.Input(
                id=input_id,
                type="number",
                value=default,
                className="bg-dark border-secondary text-light",
                **kwargs,
            ),
        ],
        size="sm",
        className="mb-2",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_export_tab() -> html.Div:
    """Assemble the Export tab.

    Returns:
        A ``html.Div`` containing figure export controls (preview,
        source selector, format, dimensions, download) and data export
        controls (CSV / HDF5 checkboxes + download).
    """
    # -- Figure export section ----------------------------------------------
    figure_section = dbc.Card(
        [
            dbc.CardHeader("Figure Export", className="text-muted small py-1 px-2"),
            dbc.CardBody(
                [
                    # Preview
                    dcc.Graph(
                        id="graph-export-preview",
                        config={"displayModeBar": True},
                        style={"height": "400px"},
                    ),

                    html.Hr(className="border-secondary my-3"),

                    # Source selector
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Source Figure",
                                        className="small text-muted mb-1",
                                    ),
                                    dcc.Dropdown(
                                        id="dropdown-export-source",
                                        options=_FIGURE_SOURCE_OPTIONS,
                                        value="graph-peth-line",
                                        clearable=False,
                                        style={
                                            "backgroundColor": "#303030",
                                            "color": "#eee",
                                        },
                                    ),
                                ],
                                md=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Format",
                                        className="small text-muted mb-1",
                                    ),
                                    dbc.RadioItems(
                                        id="radio-export-format",
                                        options=[
                                            {"label": "PNG", "value": "png"},
                                            {"label": "SVG", "value": "svg"},
                                            {"label": "PDF", "value": "pdf"},
                                        ],
                                        value="png",
                                        inline=True,
                                        className="mt-1",
                                    ),
                                ],
                                md=6,
                            ),
                        ],
                        className="mb-3",
                    ),

                    # Dimension controls
                    dbc.Row(
                        [
                            dbc.Col(
                                _labeled_input("Width", "input-export-width", 1200, min=100, step=50),
                                md=4,
                            ),
                            dbc.Col(
                                _labeled_input("Height", "input-export-height", 800, min=100, step=50),
                                md=4,
                            ),
                            dbc.Col(
                                _labeled_input("Scale", "input-export-scale", 2, min=1, max=6, step=1),
                                md=4,
                            ),
                        ],
                        className="g-2",
                    ),

                    # Download button
                    dbc.Button(
                        "Download Figure",
                        id="btn-download-figure",
                        color="primary",
                        size="sm",
                        className="w-100 mt-2",
                    ),
                    dcc.Download(id="download-figure"),
                ],
                className="p-3",
            ),
        ],
        className="bg-dark border-secondary mb-3",
    )

    # -- Data export section ------------------------------------------------
    data_section = dbc.Card(
        [
            dbc.CardHeader("Data Export", className="text-muted small py-1 px-2"),
            dbc.CardBody(
                [
                    dbc.Checklist(
                        id="check-export-csv",
                        options=[{"label": " PETH CSV", "value": "csv"}],
                        value=["csv"],
                        switch=True,
                        className="mb-2",
                    ),
                    dbc.Checklist(
                        id="check-export-hdf5",
                        options=[{"label": " Session HDF5", "value": "hdf5"}],
                        value=[],
                        switch=True,
                        className="mb-2",
                    ),
                    dbc.Button(
                        "Download Data",
                        id="btn-download-data",
                        color="primary",
                        size="sm",
                        className="w-100 mt-2",
                    ),
                    dcc.Download(id="download-data"),
                ],
                className="p-3",
            ),
        ],
        className="bg-dark border-secondary mb-3",
    )

    return html.Div(
        [
            figure_section,
            data_section,
        ],
        className="pt-2",
    )


__all__ = ["build_export_tab"]
