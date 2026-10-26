"""Plotly figures for VaR backtesting results."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app import theme
from riskkit.backtest.traffic_light import zone_limits


def exception_timeline(rollings: dict[str, pd.DataFrame], focus: str) -> go.Figure:
    """One row per model, a mark on every exception day: clusters show up as clumps."""
    fig = go.Figure()
    for name, df in rollings.items():
        days = df.index[df["actual"] > df["var"]]
        fig.add_scatter(
            x=days,
            y=[name] * len(days),
            mode="markers",
            name=name,
            marker=dict(
                symbol="line-ns-open", size=16, line=dict(width=2), color=theme.ACCENT if name == focus else theme.INK_3
            ),
        )
    fig.update_layout(height=220, margin=dict(l=90))
    return fig


def exceptions_by_model(table: pd.DataFrame) -> go.Figure:
    """Actual exceptions per model against the number a correct model would have."""
    fig = go.Figure()
    fig.add_bar(
        x=table["model"],
        y=table["exceptions"],
        name="Actual",
        marker_color=theme.ACCENT,
        text=table["exceptions"],
        textposition="outside",
    )
    fig.add_bar(
        x=table["model"],
        y=table["expected"],
        name="Expected",
        marker_color=theme.PNL_COLOR,
        text=[f"{v:.0f}" for v in table["expected"]],
        textposition="outside",
    )
    fig.update_layout(height=300, barmode="group")
    return fig


def traffic_light_chart(rz: pd.DataFrame, p: float) -> go.Figure:
    """Exceptions in the last 250 days, every day, over the Basel green / yellow / red bands."""
    yellow, red = zone_limits(250, p)
    top = max(red + 3, int(rz["exceptions"].max()) + 2)
    fig = go.Figure()
    for lo, hi, color, name in (
        (0, yellow, theme.WITHIN, "Green zone"),
        (yellow, red, theme.WATCH, "Yellow zone"),
        (red, top, theme.BREACH, "Red zone"),
    ):
        fig.add_hrect(y0=lo - 0.5, y1=hi - 0.5, fillcolor=color, opacity=0.10, line_width=0)
        fig.add_scatter(
            x=[None], y=[None], mode="markers", name=name, marker=dict(color=color, size=9), hoverinfo="skip"
        )
    fig.add_scatter(
        x=rz.index,
        y=rz["exceptions"],
        mode="lines",
        line=dict(color=theme.INK, width=1.6, shape="hv"),
        name="Exceptions in last 250 days",
    )
    fig.update_layout(height=300)
    fig.update_yaxes(range=[-0.5, top - 0.5], title_text="Exceptions, last 250 days")
    return fig
