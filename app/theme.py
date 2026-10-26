"""Design tokens, chart theme and number formatting - defined once, used everywhere.

Concept: ink on paper-grey with a single accent. The model selected in the header is
the only coloured series; everything else is grey. State colours (within / watch /
breach) appear only as small dots and text, never as large areas.
"""

from __future__ import annotations

import math

import plotly.graph_objects as go
import plotly.io as pio

# --------------------------------------------------------------------------- tokens
# Neutral greys with no blue tint, black ink for figures, one petrol accent that
# marks the model in focus. Everything that is not in focus is grey.
CANVAS = "#EFEFEC"
SURFACE = "#FFFFFF"
INK = "#161616"
INK_2 = "#4B4B48"
INK_3 = "#666662"
RULE = "#DADAD5"
RULE_SOFT = "#ECECE8"
ACCENT = "#0E5A63"  # petrol: the selected model, the series that matters
ACCENT_SOFT = "#9CC1C4"  # its light partner (ES next to VaR, "after" next to "before")

WITHIN, WATCH, BREACH = "#2E6B45", "#9A6200", "#A3271B"
STATE = {"green": WITHIN, "yellow": WATCH, "red": BREACH, "within": WITHIN, "watch": WATCH, "breach": BREACH}

# Only for charts where the reader picks a few series to compare (after accent and ink).
COMPARE = ["#B07A1E", "#6E4F86", "#55803F", "#9A4E3C", "#3E6F9C", "#7D7A3A"]
SERIES = [ACCENT, INK_2] + COMPARE  # generic order for multi-series charts
SEQ = ["#EEF4F4", "#D2E3E4", "#A9C9CC", "#76A6AB", "#47808A", "#22626C", "#0E4850"]
DIVERGING = [[0.0, "#0E5A63"], [0.5, "#F4F4F1"], [1.0, "#9A6A3A"]]

PNL_COLOR = "#C6C6C0"
OTHER_BAR = "#C6C6C0"
EXCEPTION_COLOR = BREACH

# Backwards-compatible names used by chart modules
MUTED, AXIS, GRID = INK_3, "#C8C8C2", RULE_SOFT
GOOD, WARNING, CRITICAL, SERIOUS = WITHIN, WATCH, BREACH, WATCH
ZONE_COLOR = {"green": WITHIN, "yellow": WATCH, "red": BREACH}

_ALL_MODELS = [
    "HS",
    "AgeWeighted-HS",
    "EWMA-HS",
    "GARCH-HS",
    "GJR-HS",
    "FHS-GJR-t",
    "Normal",
    "Cornish-Fisher",
    "EVT",
    "MC-t-Copula",
]
_focus = {"model": "FHS-GJR-t"}


def set_focus(model: str) -> None:
    """The model selected in the header: drawn in the accent everywhere."""
    _focus["model"] = model


def focus() -> str:
    return _focus["model"]


FONT = '"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif'
FONT_FIG = '"IBM Plex Sans Condensed", "IBM Plex Sans", system-ui, sans-serif'


def _template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family=FONT, size=12, color=INK_2),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        colorway=SERIES,
        margin=dict(l=4, r=12, t=28, b=4),
        height=320,
        title=dict(text=""),
        xaxis=dict(
            showgrid=False,
            linecolor=AXIS,
            tickcolor=AXIS,
            ticks="outside",
            ticklen=3,
            zeroline=False,
            tickfont=dict(color=INK_3, family=FONT_FIG, size=11),
            title_font=dict(size=11),
        ),
        yaxis=dict(
            gridcolor=RULE_SOFT,
            gridwidth=1,
            zeroline=False,
            showline=False,
            tickfont=dict(color=INK_3, family=FONT_FIG, size=11),
            title_font=dict(size=11, color=INK_3),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            xanchor="left",
            x=0,
            title_text="",
            font=dict(color=INK_2, size=11.5),
            bgcolor="rgba(0,0,0,0)",
            itemwidth=30,
        ),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=RULE, font=dict(family=FONT, color=INK, size=12)),
        bargap=0.3,
        coloraxis=dict(colorbar=dict(thickness=10, outlinewidth=0, tickfont=dict(color=INK_3, size=11))),
    )
    return t


pio.templates["risk"] = _template()
pio.templates.default = "plotly_white+risk"


def color(model: str) -> str:
    """Line colour for a model: accent if in focus, ink for plain HS, a muted hue otherwise."""
    if model == focus():
        return ACCENT
    if model == "HS":
        return INK
    others = [m for m in _ALL_MODELS if m not in (focus(), "HS")]
    return COMPARE[others.index(model) % len(COMPARE)] if model in others else INK_3


def bar_color(model: str) -> str:
    """Bar colour for a model in an all-models chart: only the focus model is coloured."""
    return ACCENT if model == focus() else OTHER_BAR


def line_style(model: str, width: float = 1.8) -> dict:
    return dict(color=color(model), width=width + (0.4 if model == focus() else 0))


# --------------------------------------------------------------------------- formatting
def money(x: float | None, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    a, sign = abs(x), "−" if x < 0 else ""
    if a >= 1e9:
        return f"{sign}${a / 1e9:.{digits}f}B"
    if a >= 1e6:
        return f"{sign}${a / 1e6:.{digits + 1}f}M"
    if a >= 1e3:
        return f"{sign}${a / 1e3:.{digits}f}K"
    return f"{sign}${a:,.0f}"


def signed_money(x: float) -> str:
    return ("+" if x > 0 else "") + money(x)


def pct(x: float | None, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:.{digits}%}".replace("-", "−")


def signed_pct(x: float, digits: int = 1) -> str:
    return ("+" if x > 0 else "") + pct(x, digits)


def conf_label(c: float) -> str:
    return f"{c * 100:g}%"
