"""Dashboard layout components."""

from dashboard.layouts.sidebar import build_sidebar
from dashboard.layouts.upload import build_upload_zone
from dashboard.layouts.overview import build_overview_tab
from dashboard.layouts.explorer import build_explorer_tab
from dashboard.layouts.export_panel import build_export_tab
from dashboard.layouts.population import build_population_tab


def build_layout():
    """Assemble the full dashboard layout: sidebar + tabbed main area."""
    import dash_bootstrap_components as dbc
    from dash import dcc, html

    sidebar = build_sidebar()
    main_tabs = dbc.Tabs(
        [
            dbc.Tab(build_overview_tab(), label="Session Overview", tab_id="tab-overview"),
            dbc.Tab(build_explorer_tab(), label="Peri-Event Explorer", tab_id="tab-explorer"),
            dbc.Tab(build_population_tab(), label="Population Explorer", tab_id="tab-population"),
            dbc.Tab(build_export_tab(), label="Export", tab_id="tab-export"),
        ],
        id="main-tabs",
        active_tab="tab-overview",
    )

    return dbc.Container(
        [
            dcc.Store(id="session-token", storage_type="session"),
            dcc.Store(id="session-metadata", storage_type="session"),
            dcc.Store(id="dataset-sessions", storage_type="session"),
            dcc.Store(id="population-token", storage_type="session"),
            dbc.Row(
                [
                    dbc.Col(sidebar, width=3, className="bg-dark p-3 vh-100 overflow-auto"),
                    dbc.Col(main_tabs, width=9, className="p-3"),
                ],
                className="g-0",
            ),
        ],
        fluid=True,
        className="vh-100",
    )


__all__ = [
    "build_layout",
    "build_sidebar",
    "build_upload_zone",
    "build_overview_tab",
    "build_explorer_tab",
    "build_population_tab",
    "build_export_tab",
]
