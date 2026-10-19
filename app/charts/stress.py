"""Charts for the Stress page (Module 7). Each function returns a Plotly figure."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app import theme


def loss_chart(table: pd.DataFrame) -> go.Figure:
    """Loss of every scenario in dollars, worst at the top: real crises in the accent colour, made-up shocks grey."""
    t = table.iloc[::-1]
    colors = np.where(t["kind"] == "Historical", theme.ACCENT, theme.PNL_COLOR)
    fig = go.Figure(go.Bar(x=t["loss_usd"], y=t["scenario"], orientation="h", marker_color=colors,
                           text=[theme.money(v) for v in t["loss_usd"]], textposition="outside",
                           hovertemplate="%{y}: loss $%{x:,.0f}<extra></extra>"))
    fig.update_layout(height=max(300, 34 * len(t)), margin=dict(l=10, r=80))
    fig.update_xaxes(tickprefix="$", title_text="Loss on today's portfolio")
    return fig


def stressed_var_chart(table: pd.DataFrame, base_var_usd: float, basel_usd: float, value: float) -> go.Figure:
    """1-day VaR in each stressed setting against today's VaR (dashed) and the Basel worst-year VaR (dotted)."""
    t = table.dropna(subset=["stressed_var"])
    fig = go.Figure()
    fig.add_bar(x=t["scenario"], y=t["stressed_var"] * value, name="Stressed VaR", marker_color=theme.ACCENT)
    fig.add_bar(x=t["scenario"], y=t["stressed_es"] * value, name="Stressed ES", marker_color=theme.ACCENT_SOFT)
    fig.add_hline(y=base_var_usd, line=dict(color=theme.INK, dash="dash"), annotation_text="Today's VaR")
    fig.add_hline(y=basel_usd, line=dict(color=theme.BREACH, dash="dot"), annotation_text="Worst year in history (Basel)")
    fig.update_layout(height=320, barmode="group")
    fig.update_yaxes(tickprefix="$")
    return fig


def contribution_chart(losses_usd: pd.Series, title_axis: str = "Loss") -> go.Figure:
    """Each stock's (or sector's) part of a scenario's loss; gains in the accent colour."""
    s = losses_usd.sort_values()
    fig = go.Figure(go.Bar(x=s, y=s.index, orientation="h", marker_color=np.where(s >= 0, theme.BREACH, theme.ACCENT),
                           hovertemplate="%{y}: $%{x:,.0f}<extra></extra>"))
    fig.update_layout(height=max(220, 30 * len(s)))
    fig.update_xaxes(tickprefix="$", title_text=title_axis)
    return fig


def path_chart(path: pd.Series, value: float) -> go.Figure:
    """Today's portfolio value, day by day, if the crisis replayed from tomorrow."""
    fig = go.Figure(go.Scatter(x=path.index, y=path * value, mode="lines", line=dict(color=theme.ACCENT, width=2),
                               fill="tozeroy", fillcolor="rgba(14,90,99,0.08)",
                               hovertemplate="%{x|%d %b %Y}: $%{y:,.0f}<extra></extra>"))
    fig.update_layout(height=300)
    fig.update_yaxes(tickprefix="$", range=[path.min() * value * 0.95, path.max() * value * 1.02])
    return fig
