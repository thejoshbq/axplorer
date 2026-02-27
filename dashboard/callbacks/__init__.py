"""Dashboard callback registration."""

from dashboard.callbacks.upload_cb import register_upload_callbacks
from dashboard.callbacks.overview_cb import register_overview_callbacks
from dashboard.callbacks.explorer_cb import register_explorer_callbacks
from dashboard.callbacks.export_cb import register_export_callbacks
from dashboard.callbacks.directory_cb import register_directory_callbacks
from dashboard.callbacks.population_cb import register_population_callbacks


def register_all_callbacks(app):
    """Register all dashboard callbacks on the given Dash app."""
    register_upload_callbacks(app)
    register_overview_callbacks(app)
    register_explorer_callbacks(app)
    register_export_callbacks(app)
    register_directory_callbacks(app)
    register_population_callbacks(app)


__all__ = ["register_all_callbacks"]
