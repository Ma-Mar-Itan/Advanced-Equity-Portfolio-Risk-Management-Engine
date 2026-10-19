"""Charts for the Data page (Module 1). Each function returns a Plotly figure."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app import theme


def growth_of_one_dollar(prices: pd.DataFrame) -> pd.DataFrame:
    """What $1 put into each stock on the first day would be worth on each later day."""
    return prices / prices.bfill().iloc[0]


def spread_labels(values: pd.Series, min_gap: float = 0.085) -> pd.Series:
    """Label heights on a log axis (powers of ten), nudged apart so no two labels overlap."""
    heights = np.log10(values).sort_values()
    for i in range(1, len(heights)):
        heights.iloc[i] = max(heights.iloc[i], heights.iloc[i - 1] + min_gap)
    return heights


def growth_chart(growth: pd.DataFrame, height: int = 520) -> go.Figure:
    """Log-scale lines of growth of $1: the best performer in the accent colour, the rest grey."""
    final = growth.iloc[-1]
    best = final.idxmax()
    label_y = spread_labels(final)
    fig = go.Figure()
    for t in growth.columns:
        focus = t == best
        fig.add_scatter(x=growth.index, y=growth[t], name=t, mode="lines",
                        line=dict(color=theme.ACCENT if focus else theme.INK_3, width=2.4 if focus else 1.1),
                        hovertemplate=f"{t} %{{x|%d %b %Y}}: $%{{y:,.2f}}<extra></extra>")
        fig.add_annotation(x=growth.index[-1], y=label_y[t], text=f"{t}  ${final[t]:,.0f}", showarrow=False,
                           xanchor="left", xshift=6, font=dict(size=12, color=theme.ACCENT if focus else theme.INK_2))
    fig.update_layout(height=height, showlegend=False, margin=dict(l=10, r=120, t=20, b=10))
    fig.update_xaxes(range=[growth.index[0], growth.index[-1]])
    fig.update_yaxes(type="log", title_text="Value of $1 (log scale)", tickprefix="$")
    return fig
