"""Directory scan layout — path input, scan button, and session table."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, html


def build_directory_zone() -> html.Div:
    """Build the directory scan section.

    Returns:
        A ``html.Div`` containing a text input for the directory path,
        a scan button, status feedback, a DataTable for session selection,
        and a load button.
    """
    path_input = dbc.InputGroup(
        [
            dbc.Input(
                id="input-dir-path",
                type="text",
                placeholder="Enter data directory path...",
                className="bg-dark border-secondary text-light",
            ),
            dbc.Button(
                "Scan",
                id="btn-scan-dir",
                color="info",
                size="sm",
            ),
        ],
        size="sm",
        className="mb-2",
    )

    status = html.Div(
        id="dir-scan-status",
        className="small text-info mt-1 mb-2",
    )

    select_all = dbc.Checkbox(
        id="chk-select-all",
        label="Select All",
        value=False,
        className="small text-muted mb-1",
    )

    session_table = dash_table.DataTable(
        id="table-sessions",
        columns=[
            {"name": "Phase", "id": "phase"},
            {"name": "Animal", "id": "animal_id"},
            {"name": "Sex", "id": "sex"},
            {"name": "FOV", "id": "fov"},
            {"name": "Tracked", "id": "is_tracked"},
            {"name": "NPY (MB)", "id": "npy_size_mb"},
            {"name": "MAT (MB)", "id": "mat_size_mb"},
        ],
        data=[],
        row_selectable="multi",
        selected_rows=[],
        page_size=10,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": "#303030",
            "color": "#ccc",
            "fontWeight": "bold",
            "fontSize": "0.75rem",
        },
        style_cell={
            "backgroundColor": "#222",
            "color": "#ddd",
            "fontSize": "0.75rem",
            "padding": "4px 8px",
            "border": "1px solid #444",
        },
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": "#3a506b",
                "border": "1px solid #5c8db8",
            },
        ],
    )

    load_btn = dbc.Button(
        "Load Selected",
        id="btn-load-selected",
        color="success",
        size="sm",
        className="w-100 mt-2",
        disabled=True,
    )

    load_pop_btn = dbc.Button(
        "Load Population",
        id="btn-load-population",
        color="primary",
        size="sm",
        className="w-100 mt-1",
        disabled=True,
    )

    return html.Div(
        [
            html.H6("Directory", className="text-uppercase text-muted mb-2"),
            path_input,
            status,
            select_all,
            session_table,
            load_btn,
            load_pop_btn,
        ],
    )


__all__ = ["build_directory_zone"]
