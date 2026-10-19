"""Charts for the Risk sources and Decisions pages (Module 8). Each function returns a Plotly figure."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app import theme


def share_chart(table: pd.DataFrame, measure: str) -> go.Figure:
    """Each stock's share of the money against its share of the risk."""
    col = "var_share" if measure == "VaR" else "es_share"
    fig = go.Figure()
    fig.add_bar(x=table["stock"], y=table["weight"] * 100, name="Share of the money", marker_color=theme.PNL_COLOR)
    fig.add_bar(x=table["stock"], y=table[col] * 100, name=f"Share of the {measure}", marker_color=theme.ACCENT)
    fig.update_layout(height=320, barmode="group")
    fig.update_yaxes(ticksuffix="%")
    return fig


def sector_chart(by_sector: pd.Series, measure: str) -> go.Figure:
    """Dollar risk by sector, largest first."""
    s = by_sector.sort_values()
    fig = go.Figure(go.Bar(x=s, y=s.index, orientation="h", marker_color=theme.ACCENT,
                           text=[theme.money(v) for v in s], textposition="outside"))
    fig.update_layout(height=max(220, 34 * len(s)), margin=dict(r=90))
    fig.update_xaxes(tickprefix="$", title_text=f"Share of {measure}")
    return fig


def weights_compare(before: pd.Series, after: pd.Series, labels: tuple[str, str]) -> go.Figure:
    """Two splits of the money side by side, per stock."""
    fig = go.Figure()
    fig.add_bar(x=before.index, y=before * 100, name=labels[0], marker_color=theme.PNL_COLOR)
    fig.add_bar(x=after.index, y=after.reindex(before.index) * 100, name=labels[1], marker_color=theme.ACCENT)
    fig.update_layout(height=300, barmode="group")
    fig.update_yaxes(ticksuffix="%")
    return fig


def hedge_chart(table: pd.DataFrame) -> go.Figure:
    """How much each candidate hedge cuts VaR, best at the top."""
    t = table.iloc[::-1]
    fig = go.Figure(go.Bar(x=t["reduction"] * 100, y=t["instrument"], orientation="h", marker_color=theme.ACCENT,
                           text=[f"{v:.0%}" for v in t["reduction"]], textposition="outside"))
    fig.update_layout(height=max(260, 30 * len(t)), margin=dict(r=50))
    fig.update_xaxes(ticksuffix="%", title_text="VaR reduction")
    return fig
