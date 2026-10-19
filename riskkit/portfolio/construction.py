"""Turn weights and stock returns into one portfolio: value, daily P&L and returns.

How the simulation works, day by day:
  1. Each stock holding grows by that stock's return:    holding_i *= (1 + R_i)
  2. Portfolio value = sum of holdings; P&L = change in value.
  3. On a rebalance date, trade back to the target weights and pay the trading cost.
Between rebalances the weights drift (winners become bigger slices).

Stocks combine with SIMPLE returns (log returns don't add up across stocks), so
log returns from Module 2 are converted back first.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.collect import MarketData
from riskkit.data.pipeline import CleanData
from riskkit.data.returns import log_to_simple
from riskkit.portfolio.weights import rebalance_dates, shares_from_profiles, target_weights


@dataclass(frozen=True)
class Portfolio:
    """Everything Module 3 produces. Dollar series are already scaled to the chosen value basis."""

    value: pd.Series            # portfolio value each day ($), starting the day before the first return
    pnl: pd.Series              # daily profit and loss ($)
    returns: pd.Series          # daily simple return of the portfolio
    log_returns: pd.Series      # daily log return (what the risk models will use)
    weights: pd.DataFrame       # actual weights at each day's close (drift + rebalancing)
    targets: pd.DataFrame       # target weights on each rebalance date
    contributions: pd.DataFrame # each stock's daily P&L ($)
    costs: pd.Series            # trading costs paid each day ($)
    turnover: pd.Series         # amount traded each day, as a share of portfolio value

    @property
    def current_weights(self) -> pd.Series:
        """The weights held at the latest close."""
        return self.weights.iloc[-1]


def simple_asset_returns(cd: CleanData, kind: str) -> pd.DataFrame:
    """Module 2's returns as simple returns (converted back if they are log returns)."""
    return log_to_simple(cd.returns) if kind == "log" else cd.returns


def simulate(asset_returns: pd.DataFrame, targets: pd.DataFrame, cost_bps: float,
             start_date: pd.Timestamp) -> dict[str, object]:
    """Run the holdings day by day starting from $1 at `start_date` (pure arithmetic, no scaling).

    `targets` holds the weights to trade to: its first row is the starting split, later rows are
    rebalance dates. Returns plain arrays and tables; `build_portfolio` dresses them up.
    """
    tickers, dates = list(asset_returns.columns), asset_returns.index
    R = asset_returns.to_numpy()
    rebalance_rows = {d: targets.loc[d].to_numpy() for d in targets.index[1:]}
    holdings = targets.iloc[0].to_numpy() * 1.0            # $1 split by the starting weights
    value = np.empty(len(dates) + 1)
    value[0] = 1.0
    weights = np.empty((len(dates) + 1, len(tickers)))
    weights[0] = holdings
    contrib, costs, turnover = np.zeros_like(R), np.zeros(len(dates)), np.zeros(len(dates))
    for t, d in enumerate(dates):
        contrib[t] = holdings * R[t]                        # each stock's P&L today
        holdings = holdings + contrib[t]
        v = holdings.sum()
        if d in rebalance_rows:
            wanted = rebalance_rows[d] * v
            turnover[t] = np.abs(wanted - holdings).sum() / v
            costs[t] = turnover[t] * v * cost_bps / 10_000
            v -= costs[t]
            holdings = rebalance_rows[d] * v
        value[t + 1] = v
        weights[t + 1] = holdings / v
    all_dates = pd.DatetimeIndex([start_date]).append(dates)
    return {"value": pd.Series(value, index=all_dates), "weights": pd.DataFrame(weights, all_dates, tickers),
            "contributions": pd.DataFrame(contrib, dates, tickers), "costs": pd.Series(costs, dates),
            "turnover": pd.Series(turnover, dates)}


def scale_factor(raw_value: pd.Series, cfg: RiskConfig) -> float:
    """Dollars per simulated $1: so the portfolio starts at, or is worth today, cfg.portfolio_value."""
    anchor = raw_value.iloc[-1] if cfg.portfolio.value_basis == "today" else raw_value.iloc[0]
    return cfg.portfolio_value / anchor


def build_portfolio(cd: CleanData, md: MarketData, cfg: RiskConfig) -> Portfolio:
    """Module 3 in one call: clean returns + settings -> the portfolio's daily history."""
    asset_returns = simple_asset_returns(cd, cfg.cleaning.return_type)
    prices = cd.prices.reindex(columns=asset_returns.columns)
    start = prices.index[prices.index < asset_returns.index[0]][-1]
    dates = pd.DatetimeIndex([start]).append(rebalance_dates(asset_returns.index, cfg.portfolio.rebalance))
    shares = shares_from_profiles(md.profiles, list(asset_returns.columns))
    targets = target_weights(cfg, prices, asset_returns, shares, dates)
    sim = simulate(asset_returns, targets, cfg.portfolio.cost_bps, start)
    k = scale_factor(sim["value"], cfg)
    value = sim["value"] * k
    simple = value.pct_change().iloc[1:]
    return Portfolio(value=value, pnl=value.diff().iloc[1:], returns=simple, log_returns=np.log1p(simple),
                     weights=sim["weights"], targets=targets, contributions=sim["contributions"] * k,
                     costs=sim["costs"] * k, turnover=sim["turnover"])
