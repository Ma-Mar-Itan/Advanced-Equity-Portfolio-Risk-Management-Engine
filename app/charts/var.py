"""Charts for the VaR & ES page (Module 5). Each function returns a Plotly figure."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app import theme
from riskkit.var.engine import VarResult
from riskkit.var.historical import losses_from_log_returns, tail_size


def scenario_histogram(res: VarResult) -> go.Figure:
    """The possible tomorrows as dollar P&L, with the VaR and ES lines on the loss side."""
    pnl = -losses_from_log_returns(res.scenarios) * res.value
    fig = go.Figure(go.Histogram(x=pnl, nbinsx=80, marker_color=theme.PNL_COLOR, name="Possible tomorrows",
                                 hovertemplate="$%{x:,.0f}: %{y} days<extra></extra>"))
    for x, label, color, side in ((-res.var_1d_usd, f"VaR {theme.money(res.var_1d_usd)}", theme.ACCENT, "left"),
                                  (-res.es_1d_usd, f"ES {theme.money(res.es_1d_usd)}", theme.BREACH, "right")):
        fig.add_vline(x=x, line=dict(color=color, width=2, dash="dash"))
        fig.add_annotation(x=x, y=1, yref="paper", text=label, showarrow=False, xanchor=side,
                           xshift=4 if side == "left" else -4, font=dict(color=color, size=12))
    fig.update_layout(height=320, showlegend=False)
    fig.update_xaxes(tickprefix="$", title_text="Profit or loss tomorrow")
    fig.update_yaxes(title_text="Number of scenarios")
    return fig


def tail_chart(res: VarResult, show: int = 30) -> go.Figure:
    """The worst scenarios, worst first: the tail (averaged into ES) in the breach colour, VaR as a line."""
    losses = np.sort(losses_from_log_returns(res.scenarios) * res.value)[::-1][:show]
    k = tail_size(len(res.scenarios), res.confidence)
    colors = [theme.BREACH if i < k else theme.PNL_COLOR for i in range(len(losses))]
    fig = go.Figure(go.Bar(x=np.arange(1, len(losses) + 1), y=losses, marker_color=colors,
                           hovertemplate="#%{x}: loss $%{y:,.0f}<extra></extra>"))
    fig.add_hline(y=res.var_1d_usd, line=dict(color=theme.ACCENT, dash="dash"),
                  annotation_text=f"VaR = #{k} worst", annotation_position="top right")
    fig.update_layout(height=300)
    fig.update_xaxes(title_text="Rank (1 = worst scenario)")
    fig.update_yaxes(tickprefix="$", title_text="Loss")
    return fig


def models_chart(results: list[VarResult]) -> go.Figure:
    """VaR and ES in dollars for each model, side by side."""
    names = [r.model for r in results]
    fig = go.Figure()
    fig.add_bar(x=names, y=[r.var_1d_usd for r in results], name="VaR", marker_color=theme.ACCENT,
                text=[theme.money(r.var_1d_usd) for r in results], textposition="outside")
    fig.add_bar(x=names, y=[r.es_1d_usd for r in results], name="Expected Shortfall", marker_color=theme.ACCENT_SOFT,
                text=[theme.money(r.es_1d_usd) for r in results], textposition="outside")
    fig.update_layout(height=300, barmode="group")
    fig.update_yaxes(tickprefix="$")
    return fig


def rolling_chart(rolling: dict[str, pd.DataFrame], focus: str, value: float) -> go.Figure:
    """Daily P&L (grey) against each model's VaR line (drawn below zero); days beyond the focus model's VaR in red."""
    base = rolling[focus]
    pnl = -base["actual"] * value
    fig = go.Figure()
    fig.add_bar(x=base.index, y=pnl, name="Daily P&L", marker_color=theme.PNL_COLOR, marker_line_width=0)
    for name, df in rolling.items():
        is_focus = name == focus
        fig.add_scatter(x=df.index, y=-df["var"] * value, name=f"{name} VaR", mode="lines",
                        line=dict(color=theme.ACCENT if is_focus else theme.INK_3, width=1.6 if is_focus else 0.7),
                        visible=True if is_focus or name == "HS" else "legendonly")
    breach = base["actual"] > base["var"]
    fig.add_scatter(x=base.index[breach], y=pnl[breach], mode="markers", name="Loss beyond VaR",
                    marker=dict(color=theme.BREACH, size=5))
    fig.update_layout(height=380, bargap=0, hovermode="x unified")
    fig.update_yaxes(tickprefix="$")
    return fig


def var_vs_es_chart(df: pd.DataFrame, value: float) -> go.Figure:
    """VaR and ES over time for one model: ES always sits above, the gap is the depth of the tail."""
    fig = go.Figure()
    fig.add_scatter(x=df.index, y=df["es"] * value, name="Expected Shortfall", mode="lines",
                    line=dict(color=theme.ACCENT_SOFT, width=1.4))
    fig.add_scatter(x=df.index, y=df["var"] * value, name="VaR", mode="lines", line=dict(color=theme.ACCENT, width=1.4))
    fig.update_layout(height=300, hovermode="x unified")
    fig.update_yaxes(tickprefix="$")
    return fig
