"""Plotly figures for portfolio performance and holdings."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app import theme

#: Enough distinct, calm colours for a stacked chart of many stocks.
MANY = theme.SERIES + ["#A9A9A3", "#5E7F86", "#C2A46B", "#8E7BA0", "#86A577", "#B98273"]


def value_chart(value: pd.Series, benchmark: pd.Series | None, log_scale: bool = False) -> go.Figure:
    """Portfolio value over time (accent) against the benchmark started at the same value (grey)."""
    fig = go.Figure()
    if benchmark is not None:
        fig.add_scatter(
            x=benchmark.index,
            y=benchmark,
            name=f"{benchmark.name} (market)",
            mode="lines",
            line=dict(color=theme.INK_3, width=1.3),
        )
    fig.add_scatter(x=value.index, y=value, name="Portfolio", mode="lines", line=dict(color=theme.ACCENT, width=2.2))
    fig.update_layout(height=360, hovermode="x unified")
    fig.update_yaxes(tickprefix="$", type="log" if log_scale else "linear")
    return fig


def drawdown_chart(dd: pd.Series) -> go.Figure:
    """Fall below the previous peak each day, as a shaded area under zero."""
    fig = go.Figure(
        go.Scatter(
            x=dd.index,
            y=dd * 100,
            fill="tozeroy",
            mode="lines",
            name="Drawdown",
            line=dict(color=theme.ACCENT, width=1),
            fillcolor="rgba(14,90,99,0.18)",
            hovertemplate="%{x|%d %b %Y}: %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(height=260)
    fig.update_yaxes(ticksuffix="%")
    return fig


def pnl_chart(pnl: pd.Series) -> go.Figure:
    """Daily profit and loss in dollars: gains grey, losses in the breach colour."""
    fig = go.Figure()
    fig.add_bar(
        x=pnl.index,
        y=pnl.where(pnl >= 0),
        name="Gain",
        marker_color=theme.PNL_COLOR,
        marker_line_width=0,
        hovertemplate="%{x|%d %b %Y}: $%{y:,.0f}<extra></extra>",
    )
    fig.add_bar(
        x=pnl.index,
        y=pnl.where(pnl < 0),
        name="Loss",
        marker_color=theme.BREACH,
        marker_line_width=0,
        hovertemplate="%{x|%d %b %Y}: $%{y:,.0f}<extra></extra>",
    )
    fig.update_layout(height=260, bargap=0, barmode="overlay")
    fig.update_yaxes(tickprefix="$")
    return fig


def returns_chart(returns: pd.Series) -> go.Figure:
    """Daily portfolio returns in %: gains grey, losses in the breach colour."""
    values = returns * 100
    fig = go.Figure()
    fig.add_bar(
        x=returns.index,
        y=values.where(returns >= 0),
        name="Gain",
        marker_color=theme.PNL_COLOR,
        marker_line_width=0,
        hovertemplate="%{x|%d %b %Y}: %{y:.2f}%<extra></extra>",
    )
    fig.add_bar(
        x=returns.index,
        y=values.where(returns < 0),
        name="Loss",
        marker_color=theme.BREACH,
        marker_line_width=0,
        hovertemplate="%{x|%d %b %Y}: %{y:.2f}%<extra></extra>",
    )
    fig.update_layout(height=260, bargap=0, barmode="overlay")
    fig.update_yaxes(ticksuffix="%")
    return fig


def distribution_chart(returns: pd.Series) -> go.Figure:
    """Histogram of daily returns with the bell curve a normal distribution would predict."""
    x = returns * 100
    fig = go.Figure(
        go.Histogram(x=x, nbinsx=150, histnorm="probability density", name="Actual days", marker_color=theme.PNL_COLOR)
    )
    grid = np.linspace(x.min(), x.max(), 400)
    bell = np.exp(-0.5 * ((grid - x.mean()) / x.std()) ** 2) / (x.std() * np.sqrt(2 * np.pi))
    fig.add_scatter(x=grid, y=bell, mode="lines", name="Normal bell curve", line=dict(color=theme.ACCENT, width=2))
    fig.update_layout(height=300)
    fig.update_xaxes(ticksuffix="%", title_text="Daily return")
    return fig


def weights_chart(weights: pd.DataFrame) -> go.Figure:
    """Weights over time as stacked bands: shows drift between rebalances (shorts appear below zero)."""
    w = weights.resample("W").last() * 100
    fig = go.Figure()
    for i, t in enumerate(w.columns):
        fig.add_scatter(
            x=w.index,
            y=w[t],
            name=t,
            mode="lines",
            stackgroup="pos" if (w[t] >= 0).all() else "neg",
            line=dict(width=0.5, color=MANY[i % len(MANY)]),
        )
    fig.update_layout(height=320, hovermode="x unified", legend=dict(orientation="h", y=1.08))
    fig.update_yaxes(ticksuffix="%")
    return fig


def contribution_chart(total_by_stock: pd.Series) -> go.Figure:
    """Total dollars each stock added to (or took from) the portfolio, biggest at the top."""
    s = total_by_stock.sort_values()
    fig = go.Figure()
    fig.add_bar(
        x=s.where(s >= 0),
        y=s.index,
        orientation="h",
        name="Added value",
        marker_color=theme.ACCENT,
        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
    )
    fig.add_bar(
        x=s.where(s < 0),
        y=s.index,
        orientation="h",
        name="Reduced value",
        marker_color=theme.BREACH,
        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
    )
    fig.update_layout(height=max(220, 28 * len(s)), barmode="overlay")
    fig.update_xaxes(tickprefix="$")
    return fig
