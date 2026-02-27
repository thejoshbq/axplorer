"""Population Explorer tab layout --- population heatmap, grand average, response pie.

Provides the ``build_population_tab`` factory used by the main dashboard
layout to render the Population Explorer analysis tab.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html


# ---------------------------------------------------------------------------
# Table styles (matching explorer.py)
# ---------------------------------------------------------------------------

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

def build_population_tab() -> html.Div:
    """Assemble the Population Explorer tab.

    Returns:
        A ``html.Div`` containing the grand average trace, sorted population
        heatmap with sort controls, response classification pie chart, and
        a per-session summary table.
    """
    # -- Grand average trace (mean +/- SEM across sessions) -----------------
    grand_avg_row = dbc.Row(
        [
            dbc.Col(
                _graph_card(
                    "graph-pop-peth-line",
                    "Grand Average \u2014 Mean \u00b1 SEM (across sessions)",
                    height="370px",
                ),
            ),
        ],
        className="g-2",
    )

    # -- Population heatmap + sort controls | Pie chart ---------------------
    sort_controls = html.Div(
        [
            html.Label("Sort Method", className="small text-muted mb-1"),
            dcc.Dropdown(
                id="dropdown-pop-sort-method",
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
            _graph_card(
                "graph-pop-heatmap",
                "Population Heatmap (all neurons)",
                height="400px",
            ),
            sort_controls,
        ],
        md=7,
    )

    pie_col = dbc.Col(
        _graph_card(
            "graph-pop-response-pie",
            "Response Classification (pooled)",
            height="350px",
        ),
        md=5,
    )

    heatmap_row = dbc.Row([heatmap_col, pie_col], className="g-2")

    # -- Per-session summary table ------------------------------------------
    session_summary = dbc.Card(
        [
            dbc.CardHeader(
                "Session Summary",
                className="text-muted small py-1 px-2",
            ),
            dbc.CardBody(
                dash_table.DataTable(
                    id="table-pop-session-summary",
                    columns=[
                        {"name": "Session", "id": "session"},
                        {"name": "Neurons", "id": "neurons"},
                        {"name": "Trials", "id": "trials"},
                    ],
                    data=[],
                    page_size=20,
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

    # -- Recompute button for population tab --------------------------------
    recompute_btn = dbc.Button(
        "Recompute Population",
        id="btn-pop-recompute",
        color="primary",
        size="sm",
        className="w-100 mb-3",
    )

    return html.Div(
        [
            dcc.Store(id="store-pop-peth-data"),
            recompute_btn,
            grand_avg_row,
            heatmap_row,
            session_summary,
        ],
        className="pt-2",
    )


__all__ = ["build_population_tab"]
