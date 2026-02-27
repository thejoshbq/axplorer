"""Session Overview tab layout --- metric cards + behavioral plots + heatmap.

Provides the ``build_overview_tab`` factory that assembles the Session
Overview tab shown as the default view when a session is loaded.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _metric_card(card_id: str, header: str) -> dbc.Col:
    """Return a single metric card wrapped in a responsive column.

    Args:
        card_id: The Dash component ID for the card body text.
        header: Human-readable metric label shown in the card header.

    Returns:
        A ``dbc.Col`` containing the styled card.
    """
    card = dbc.Card(
        [
            dbc.CardHeader(
                header,
                className="text-muted small py-1 px-2",
            ),
            dbc.CardBody(
                html.H4(
                    "\u2014",
                    id=card_id,
                    className="mb-0 text-center",
                ),
                className="py-2 px-2",
            ),
        ],
        className="bg-dark border-secondary",
    )
    return dbc.Col(card, xs=6, md=3, className="mb-3")


def _graph_card(graph_id: str, title: str, height: str = "350px") -> dbc.Card:
    """Return a graph wrapped in a titled card.

    Args:
        graph_id: The Dash component ID for the ``dcc.Graph``.
        title: Card header text.
        height: CSS height for the graph div.

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

def build_overview_tab() -> html.Div:
    """Assemble the Session Overview tab.

    Returns:
        A ``html.Div`` containing metric cards, cumulative response and
        event breakdown plots, an event raster, and a signal quality
        heatmap.
    """
    # -- Metric cards -------------------------------------------------------
    metrics_row = dbc.Row(
        [
            _metric_card("card-active", "Active Presses"),
            _metric_card("card-inactive", "Inactive Presses"),
            _metric_card("card-discrimination", "Discrimination Index"),
            _metric_card("card-reinforcers", "Reinforcers"),
        ],
        className="g-2",
    )

    # -- Behavioral plots ---------------------------------------------------
    plots_row = dbc.Row(
        [
            dbc.Col(
                _graph_card("graph-cumulative", "Cumulative Responses"),
                md=6,
            ),
            dbc.Col(
                _graph_card("graph-event-breakdown", "Event Breakdown"),
                md=6,
            ),
        ],
        className="g-2",
    )

    # -- Event raster -------------------------------------------------------
    raster_row = dbc.Row(
        [
            dbc.Col(
                _graph_card("graph-event-raster", "Behavioral Event Raster", height="250px"),
            ),
        ],
        className="g-2",
    )

    # -- Signal quality heatmap ---------------------------------------------
    heatmap_row = dbc.Row(
        [
            dbc.Col(
                _graph_card("graph-signal-heatmap", "Signal Quality Heatmap", height="350px"),
            ),
        ],
        className="g-2",
    )

    return html.Div(
        [
            metrics_row,
            plots_row,
            raster_row,
            heatmap_row,
        ],
        className="pt-2",
    )


__all__ = ["build_overview_tab"]
