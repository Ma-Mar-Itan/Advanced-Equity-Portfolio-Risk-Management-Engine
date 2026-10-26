"""Plotly figures for volatility estimates and diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app import theme
from riskkit.volatility.base import VolFit, annualize
from riskkit.volatility.garch import news_impact

MODEL_COLORS = {"GJR-GARCH": theme.ACCENT, "GARCH": theme.COMPARE[0], "EWMA": theme.COMPARE[1]}


def _color(name: str) -> str:
    """Return the primary color for GJR-GARCH and a muted color for other models."""
    return MODEL_COLORS.get(name, theme.INK_3)


def _scale(x, yearly: bool):
    """Daily volatility -> % (yearly if asked)."""
    return (annualize(x) if yearly else x) * 100


def comparison_chart(fits: dict[str, VolFit], yearly: bool) -> go.Figure:
    """Every model's volatility over time on one chart."""
    fig = go.Figure()
    for name, f in fits.items():
        fig.add_scatter(
            x=f.sigma.index,
            y=_scale(f.sigma, yearly),
            name=name,
            mode="lines",
            line=dict(color=_color(name), width=2 if name == "GJR-GARCH" else 1.1),
        )
    fig.update_layout(height=360, hovermode="x unified")
    fig.update_yaxes(ticksuffix="%", title_text="Volatility (% per year)" if yearly else "Volatility (% per day)")
    return fig


def clustering_chart(returns: pd.Series, fit: VolFit) -> go.Figure:
    """Plot daily returns within a plus-or-minus two-volatility band."""
    sigma = fit.sigma.reindex(returns.index)
    outside = returns.abs() > 2 * sigma
    fig = go.Figure()
    fig.add_scatter(
        x=sigma.index,
        y=2 * sigma * 100,
        mode="lines",
        line=dict(color=theme.ACCENT, width=1),
        name="+2 volatilities",
        hoverinfo="skip",
    )
    fig.add_scatter(
        x=sigma.index,
        y=-2 * sigma * 100,
        mode="lines",
        line=dict(color=theme.ACCENT, width=1),
        fill="tonexty",
        fillcolor="rgba(14,90,99,0.10)",
        name="-2 volatilities",
        hoverinfo="skip",
    )
    fig.add_scatter(
        x=returns.index, y=returns * 100, name="Daily return", mode="lines", line=dict(color=theme.INK_3, width=0.6)
    )
    fig.add_scatter(
        x=returns.index[outside],
        y=returns[outside] * 100,
        mode="markers",
        name="Outside the band",
        marker=dict(color=theme.BREACH, size=4),
    )
    fig.update_layout(height=340)
    fig.update_yaxes(ticksuffix="%")
    return fig


def news_impact_chart(fits: dict[str, VolFit], yearly: bool) -> go.Figure:
    """Tomorrow's volatility after a day with a given return: GARCH symmetric, GJR steeper on the left."""
    shocks = np.linspace(-0.10, 0.10, 201)
    fig = go.Figure()
    for name in ("GARCH", "GJR-GARCH"):
        fig.add_scatter(
            x=shocks * 100,
            y=_scale(news_impact(fits[name].params, shocks), yearly),
            name=name,
            mode="lines",
            line=dict(color=_color(name), width=2),
        )
    fig.update_layout(height=300)
    fig.update_xaxes(ticksuffix="%", title_text="Today's return")
    fig.update_yaxes(ticksuffix="%", title_text="Tomorrow's volatility")
    return fig


def leverage_chart(table: pd.DataFrame) -> go.Figure:
    """Average size of the next 5 days' moves, after each kind of day (down days in the breach colour)."""
    col = table.columns[1]
    positions = table["move"].astype(str)
    values = table[col] * 100
    fig = go.Figure()
    for mask, name, color in (
        (table.index < 3, "Negative return", theme.BREACH),
        (table.index == 3, "Near zero", theme.INK_3),
        (table.index > 3, "Positive return", theme.ACCENT),
    ):
        fig.add_bar(
            x=positions,
            y=values.where(mask),
            name=name,
            marker_color=color,
            text=[f"{value:.2f}%" if keep else "" for value, keep in zip(values, mask, strict=True)],
            textposition="outside",
        )
    fig.update_layout(height=300, barmode="overlay")
    fig.update_xaxes(title_text="Return on the day")
    fig.update_yaxes(ticksuffix="%", title_text="Average move, next 5 days")
    return fig


def forecast_chart(fits: dict[str, VolFit], yearly: bool) -> go.Figure:
    """Each model's forecast for the next days: GARCH models drift back to normal, EWMA and rolling stay flat."""
    fig = go.Figure()
    for name, f in fits.items():
        days = np.arange(1, len(f.forecast) + 1)
        fig.add_scatter(
            x=days,
            y=_scale(f.forecast, yearly),
            name=name,
            mode="lines+markers",
            line=dict(color=_color(name), width=2 if name == "GJR-GARCH" else 1.2),
            marker=dict(size=4),
        )
    fig.update_layout(height=300)
    fig.update_xaxes(title_text="Days ahead")
    fig.update_yaxes(ticksuffix="%")
    return fig


def residuals_chart(raw: pd.Series, z: pd.Series) -> go.Figure:
    """Raw returns vs returns divided by GJR volatility, both standardized, against a normal bell curve."""
    fig = go.Figure()
    for series, name, color in (
        (raw / raw.std(), "Raw returns", theme.PNL_COLOR),
        (z, "After dividing by volatility", theme.ACCENT),
    ):
        fig.add_histogram(
            x=series,
            name=name,
            histnorm="probability density",
            nbinsx=120,
            marker_color=color,
            opacity=0.6,
            xbins=dict(start=-8, end=8, size=0.16),
        )
    grid = np.linspace(-8, 8, 400)
    fig.add_scatter(
        x=grid,
        y=np.exp(-(grid**2) / 2) / np.sqrt(2 * np.pi),
        mode="lines",
        name="Normal bell curve",
        line=dict(color=theme.INK, width=1.5, dash="dot"),
    )
    fig.update_layout(height=300, barmode="overlay")
    fig.update_xaxes(title_text="Size of the day, in standard deviations", range=[-8, 8])
    return fig


def scaled_chart(raw: pd.Series, scaled: pd.Series) -> go.Figure:
    """Past returns as they happened (grey) and rescaled to today's volatility (accent)."""
    fig = go.Figure()
    fig.add_scatter(
        x=raw.index, y=raw * 100, mode="lines", name="As they happened", line=dict(color=theme.PNL_COLOR, width=0.8)
    )
    fig.add_scatter(
        x=scaled.index,
        y=scaled * 100,
        mode="lines",
        name="Rescaled to today's volatility",
        line=dict(color=theme.ACCENT, width=0.8),
    )
    fig.update_layout(height=300)
    fig.update_yaxes(ticksuffix="%")
    return fig


def regime_chart(table: pd.DataFrame) -> go.Figure:
    """Typical daily move in calm, normal and stormy periods, with the number of days below -3% on each bar."""
    colors = {"Calm": theme.WITHIN, "Normal": theme.INK_3, "Stormy": theme.BREACH}
    fig = go.Figure()
    for _, row in table.iterrows():
        name = str(row["regime"])
        move = float(row["typical move"] * 100)
        fig.add_bar(
            x=[name],
            y=[move],
            name=f"{name} regime",
            marker_color=colors[name],
            text=[f"{move:.2f}% typical move<br>{int(row['days below -3%'])} days below -3%"],
            textposition="outside",
        )
    fig.update_layout(height=300)
    fig.update_yaxes(ticksuffix="%", title_text="Typical daily move", range=[0, table["typical move"].max() * 135])
    return fig
