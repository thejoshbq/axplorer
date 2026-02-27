"""Dashboard theme --- DARKLY bootstrap + Plotly figure template.

Defines the DARKLY Bootstrap external stylesheet for Dash and registers a
custom Plotly template (``axplorer_dark``) with dark backgrounds, subtle
grid lines, and sensible defaults for scientific figures.
"""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.io as pio

EXTERNAL_STYLESHEETS = [dbc.themes.DARKLY]

# ---------------------------------------------------------------------------
# Custom Plotly template
# ---------------------------------------------------------------------------

_BG = "#222222"
_PAPER = "#222222"
_FONT_COLOR = "#EEEEEE"
_GRID_COLOR = "#444444"
_AXIS_LINE = "#555555"

_template = go.layout.Template(
    layout=go.Layout(
        # Background
        paper_bgcolor=_BG,
        plot_bgcolor=_PAPER,
        # Typography
        font=dict(family="Inter, Segoe UI, Roboto, sans-serif", size=13, color=_FONT_COLOR),
        title=dict(font=dict(size=16, color=_FONT_COLOR), x=0.02, xanchor="left"),
        # Axes
        xaxis=dict(
            gridcolor=_GRID_COLOR,
            gridwidth=1,
            linecolor=_AXIS_LINE,
            linewidth=1,
            zerolinecolor=_GRID_COLOR,
            zerolinewidth=1,
            title=dict(font=dict(size=13, color=_FONT_COLOR)),
            tickfont=dict(size=11, color=_FONT_COLOR),
        ),
        yaxis=dict(
            gridcolor=_GRID_COLOR,
            gridwidth=1,
            linecolor=_AXIS_LINE,
            linewidth=1,
            zerolinecolor=_GRID_COLOR,
            zerolinewidth=1,
            title=dict(font=dict(size=13, color=_FONT_COLOR)),
            tickfont=dict(size=11, color=_FONT_COLOR),
        ),
        # Legend
        legend=dict(
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor=_GRID_COLOR,
            borderwidth=1,
            font=dict(size=11, color=_FONT_COLOR),
            x=1.0,
            y=1.0,
            xanchor="right",
            yanchor="top",
        ),
        # Margins
        margin=dict(l=60, r=20, t=50, b=50),
        # Color sequence — qualitative palette readable on dark backgrounds
        colorway=[
            "#636EFA",  # blue
            "#EF553B",  # red
            "#00CC96",  # teal
            "#AB63FA",  # purple
            "#FFA15A",  # orange
            "#19D3F3",  # cyan
            "#FF6692",  # pink
            "#B6E880",  # lime
            "#FF97FF",  # magenta
            "#FECB52",  # yellow
        ],
        # Color bar
        coloraxis=dict(
            colorbar=dict(
                tickfont=dict(color=_FONT_COLOR),
                title=dict(font=dict(color=_FONT_COLOR)),
                outlinecolor=_GRID_COLOR,
                outlinewidth=1,
            ),
        ),
    ),
)

pio.templates["axplorer_dark"] = _template
pio.templates.default = "axplorer_dark"

FIGURE_TEMPLATE: str = "axplorer_dark"

# Dashboard-level color overrides for events that are too similar in Pynapse.
DASHBOARD_COLOR_OVERRIDES: dict[str, str] = {
    "active_lever_timeout": "#FFC107",   # amber — distinct from active red
    "timeout_lever_press": "#FFC107",    # amber — distinct from active red
}

__all__ = ["EXTERNAL_STYLESHEETS", "FIGURE_TEMPLATE", "DASHBOARD_COLOR_OVERRIDES"]
