"""Replay a real crisis on TODAY's portfolio.

Each stock gets the daily returns it actually had during the crisis; the portfolio is held
(no trading) through the window. A stock that did not exist yet gets a stand-in:
its beta (sensitivity to the market, measured on recent data) x the benchmark's daily return.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from riskkit.stress.scenarios import HistoricalScenario
from riskkit.var.historical import var_es


def betas(asset_returns: pd.DataFrame, bench_returns: pd.Series, window: int) -> pd.Series:
    """Each stock's beta to the benchmark over the last `window` days: how much it moves when the market moves 1%."""
    a = asset_returns.iloc[-window:]
    b = bench_returns.reindex(a.index)
    return a.apply(lambda col: col.cov(b) / b.var())


def crisis_returns(asset_returns: pd.DataFrame, bench_returns: pd.Series, beta: pd.Series,
                   start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.DataFrame, list[str]]:
    """Daily simple returns of each stock in the window, with beta stand-ins for missing stocks (listed in the 2nd output)."""
    window = asset_returns.loc[start:end]
    bench = bench_returns.reindex(window.index).fillna(0.0)
    proxied = [t for t in window.columns if window[t].isna().mean() > 0.5]
    filled = window.copy()
    for t in window.columns:
        stand_in = beta[t] * bench
        filled[t] = window[t].fillna(stand_in) if t not in proxied else stand_in
    return filled.iloc[1:], proxied           # first row has no previous price inside the window


@dataclass(frozen=True)
class Replay:
    """A crisis replayed on today's portfolio. Dollar values are on today's portfolio value."""

    name: str
    loss: float                      # total loss over the window, share of value (positive = loss)
    worst_day: float                 # worst single-day loss
    max_drawdown: float              # deepest fall inside the window
    path: pd.Series                  # portfolio value path (starting at 1)
    by_stock: pd.Series              # each stock's contribution to the total loss (share of value)
    proxied: list[str]


def replay(scenario: HistoricalScenario, weights: pd.Series, asset_returns: pd.DataFrame,
           bench_returns: pd.Series, beta: pd.Series) -> Replay:
    """Buy today's split at the start of the crisis and hold it to the end."""
    start, end = scenario.dates
    r, proxied = crisis_returns(asset_returns, bench_returns, beta, start, end)
    growth = (1 + r).cumprod()
    holdings = growth * weights
    path = pd.concat([pd.Series([1.0], index=[start]), holdings.sum(axis=1)])
    daily = path.pct_change().dropna()
    by_stock = -(holdings.iloc[-1] - weights)
    return Replay(scenario.name, float(1 - path.iloc[-1]), float(-daily.min()),
                  float(-(path / path.cummax() - 1).min()), path, by_stock, proxied)


def stressed_var_es(daily_portfolio_returns: pd.Series, end: pd.Timestamp, confidence: float,
                    days: int = 250) -> tuple[float, float]:
    """1-day VaR/ES as if the next day were drawn from the `days` days ending at the crisis end."""
    window = daily_portfolio_returns.loc[:end].iloc[-days:]
    return var_es(np.log1p(window.to_numpy()), confidence)


def worst_window_var(daily_portfolio_returns: pd.Series, confidence: float, days: int = 250) -> tuple[float, pd.Timestamp]:
    """Basel 2.5 stressed VaR: the highest 1-day VaR over any `days`-day window in history, and when it ended."""
    logs = np.log1p(daily_portfolio_returns.dropna())
    best, when = 0.0, logs.index[days - 1]
    for i in range(days, len(logs) + 1, 5):        # every 5th day is plenty for a search
        v = var_es(logs.iloc[i - days:i].to_numpy(), confidence)[0]
        if v > best:
            best, when = v, logs.index[i - 1]
    return best, when


def todays_portfolio_history(weights: pd.Series, asset_returns: pd.DataFrame, bench_returns: pd.Series,
                             beta: pd.Series) -> pd.Series:
    """Daily returns of today's split over the full history (beta stand-ins before a stock existed)."""
    filled = asset_returns.copy()
    for t in filled.columns:
        filled[t] = filled[t].fillna(beta[t] * bench_returns.reindex(filled.index))
    return (filled * weights).sum(axis=1).dropna()
