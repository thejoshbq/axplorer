"""Peri-Event Explorer tab layout --- PETH line, heatmap, raster, metrics.

Provides the ``build_explorer_tab`` factory used by the main dashboard
layout to render the Peri-Event Explorer analysis tab.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html


# ---------------------------------------------------------------------------
# Table column definitions
# ---------------------------------------------------------------------------

_METRIC_COLUMNS = [
    {"name": "Cell ID", "id": "cell_id"},
    {"name": "Peak Z-Score", "id": "peak_zscore"},
    {"name": "Peak Latency (s)", "id": "peak_latency_s"},
    {"name": "AUC", "id": "auc"},
    {"name": "Onset Latency (s)", "id": "onset_latency_s"},
    {"name": "Classification", "id": "classification"},
]

_TABLE_STYLE_HEADER = {
    "backgroundColor": "#303030",
    "color": "#eee",
    "fontWeight": "600",
    "borderBottom": "1px solid #555",
    "textAlign": "center",
}

_TABLE_STYLE_CELL = {
    "backgroundColor": "#222",
    "color": "#ddd",
    "borderBottom": "1px solid #444",
    "textAlign": "center",
    "padding": "6px 10px",
    "fontSize": "13px",
}

_TABLE_STYLE_DATA_CONDITIONAL = [
    {
        "if": {"row_index": "odd"},
        "backgroundColor": "#2a2a2a",
    },
    {
        "if": {"state": "active"},
        "backgroundColor": "#3a3a5c",
        "border": "1px solid #636EFA",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _graph_card(graph_id: str, title: str, height: str = "350px") -> dbc.Card:
    """Return a graph wrapped in a titled card.

    Args:
        graph_id: Dash component ID for the ``dcc.Graph``.
        title: Card header text.
        height: CSS height for the graph container.

    Returns:
        A ``dbc.Card`` containing the graph.
    """
    return dbc.Card(
        [
            dbc.CardHeader(title, className="text-muted small py-1 px-2"),
            dbc.CardBody(
                dcc.Graph(
                    id=graph_id,
                    config={"displayModeBar": True, "scrollZoom": True},
                    style={"height": height},
                ),
                className="p-1",
            ),
        ],
        className="bg-dark border-secondary mb-3",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_explorer_tab() -> html.Div:
    """Assemble the Peri-Event Explorer tab.

    Returns:
        A ``html.Div`` containing the PETH line plot, sorted heatmap
        with sort controls, response classification pie chart, trial
        raster, and a response-metrics DataTable.
    """
    # -- PETH line plot (mean +/- SEM) --------------------------------------
    peth_line = dbc.Row(
        [
            dbc.Col(
                _graph_card("graph-peth-line", "PETH — Mean \u00b1 SEM", height="370px"),
            ),
        ],
        className="g-2",
    )

    # -- Heatmap + sort controls | Pie chart --------------------------------
    sort_controls = html.Div(
        [
            html.Label("Sort Method", className="small text-muted mb-1"),
            dcc.Dropdown(
                id="dropdown-sort-method",
                options=[
                    {"label": "Excitatory", "value": "excitatory"},
                    {"label": "Inhibitory", "value": "inhibitory"},
                    {"label": "Magnitude", "value": "magnitude"},
                ],
                value="excitatory",
                clearable=False,
                className="mb-2",
                style={"backgroundColor": "#303030", "color": "#eee"},
            ),
        ],
    )

    heatmap_col = dbc.Col(
        [
            _graph_card("graph-sorted-heatmap", "Sorted Heatmap", height="350px"),
            sort_controls,
        ],
        md=7,
    )

    pie_col = dbc.Col(
        _graph_card("graph-response-pie", "Response Classification", height="350px"),
        md=5,
    )

    heatmap_row = dbc.Row([heatmap_col, pie_col], className="g-2")

    # -- Trial raster -------------------------------------------------------
    raster_row = dbc.Row(
        [
            dbc.Col(
                _graph_card("graph-trial-raster", "Trial Raster — Single Cell", height="300px"),
            ),
        ],
        className="g-2",
    )

    # -- Response metrics table ---------------------------------------------
    metrics_table = dbc.Card(
        [
            dbc.CardHeader(
                "Response Metrics",
                className="text-muted small py-1 px-2",
            ),
            dbc.CardBody(
                dash_table.DataTable(
                    id="table-response-metrics",
                    columns=_METRIC_COLUMNS,
                    data=[],
                    page_size=15,
                    sort_action="native",
                    filter_action="native",
                    style_header=_TABLE_STYLE_HEADER,
                    style_cell=_TABLE_STYLE_CELL,
                    style_data_conditional=_TABLE_STYLE_DATA_CONDITIONAL,
                    style_table={"overflowX": "auto"},
                    style_as_list_view=True,
                ),
                className="p-2",
            ),
        ],
        className="bg-dark border-secondary mb-3",
    )

    return html.Div(
        [
            dcc.Store(id="store-peth-data"),
            peth_line,
            heatmap_row,
            raster_row,
            metrics_table,
        ],
        className="pt-2",
    )


__all__ = ["build_explorer_tab"]
