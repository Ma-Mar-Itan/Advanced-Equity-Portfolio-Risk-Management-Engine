"""Plotly figures for data-cleaning diagnostics."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app import theme


def distribution_before_after(raw: pd.Series, final: pd.Series) -> go.Figure:
    """Histogram of daily returns before (grey) and after (accent) winsorizing / the custom formula."""
    lo, hi = float(raw.min() * 100), float(raw.max() * 100)
    bins = dict(start=lo, end=hi, size=(hi - lo) / 120)  # same bars for both, so they compare
    fig = go.Figure()
    fig.add_histogram(x=raw * 100, name="Before", xbins=bins, marker_color=theme.PNL_COLOR, opacity=0.9)
    if not raw.reindex(final.index).equals(final):
        fig.add_histogram(x=final * 100, name="After", xbins=bins, marker_color=theme.ACCENT, opacity=0.6)
    fig.update_layout(barmode="overlay", height=300)
    fig.update_xaxes(title_text="Daily return (%)", ticksuffix="%")
    fig.update_yaxes(title_text="Number of days")
    return fig


def returns_timeline(raw: pd.Series, final: pd.Series) -> go.Figure:
    """Daily returns over time; days changed by cleaning are marked in red."""
    changed = raw.reindex(final.index).sub(final).abs() > 1e-12
    fig = go.Figure()
    fig.add_scatter(x=final.index, y=final * 100, mode="lines", name="Return", line=dict(color=theme.INK_3, width=0.8))
    if changed.any():
        fig.add_scatter(
            x=final.index[changed],
            y=raw.reindex(final.index)[changed] * 100,
            mode="markers",
            name="Changed by cleaning",
            marker=dict(color=theme.BREACH, size=6),
        )
    fig.update_layout(height=280)
    fig.update_yaxes(ticksuffix="%")
    return fig


def rolling_vol_chart(vol: pd.DataFrame, focus: str) -> go.Figure:
    """Yearly rolling volatility for every stock: the chosen stock in the accent colour."""
    fig = go.Figure()
    other_label_added = False
    for t in vol.columns:
        if t != focus:
            fig.add_scatter(
                x=vol.index,
                y=vol[t] * 100,
                mode="lines",
                name="Other stocks" if not other_label_added else t,
                showlegend=not other_label_added,
                line=dict(color=theme.RULE, width=0.8),
                hoverinfo="skip",
            )
            other_label_added = True
    fig.add_scatter(x=vol.index, y=vol[focus] * 100, mode="lines", name=focus, line=dict(color=theme.ACCENT, width=1.8))
    fig.update_layout(height=300)
    fig.update_yaxes(ticksuffix="%", title_text="Volatility (% per year)")
    return fig
