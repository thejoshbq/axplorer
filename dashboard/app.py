"""Axplorer Dashboard — Plotly Dash application entry point."""

from __future__ import annotations

import dash

from dashboard.callbacks import register_all_callbacks
from dashboard.layouts import build_layout
from dashboard.theme import EXTERNAL_STYLESHEETS


def create_app() -> dash.Dash:
    """Create and configure the Dash application.

    Returns:
        A fully configured ``dash.Dash`` instance ready to run.
    """
    app = dash.Dash(
        __name__,
        external_stylesheets=EXTERNAL_STYLESHEETS,
        suppress_callback_exceptions=True,
        title="Axplorer",
        update_title="Axplorer — loading...",
    )

    app.layout = build_layout()
    register_all_callbacks(app)

    return app


def main() -> None:
    """Run the dashboard in development mode."""
    app = create_app()
    app.run(debug=True, port=8050)


if __name__ == "__main__":
    main()
