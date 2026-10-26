"""How the money is split between stocks (the weights).

Every function returns a pd.Series indexed by ticker that adds up to 1 (100%).
Target weights are decided on each rebalance date using ONLY data up to that
date, so no scheme peeks into the future.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.config import RiskConfig


def equal_weights(tickers: list[str]) -> pd.Series:
    """The same share for every stock: 10 stocks -> 10% each."""
    return pd.Series(1.0 / len(tickers), index=tickers)


def custom_weights(cfg: RiskConfig, tickers: list[str]) -> pd.Series:
    """The user's own split (equal if none given). Stocks that failed to load are dropped and the rest rescaled."""
    if cfg.weights is None:
        return equal_weights(tickers)
    w = pd.Series(cfg.weights, index=cfg.tickers).reindex(tickers).fillna(0.0)
    if abs(w.sum()) < 1e-12:
        raise ValueError("The custom weights of the loaded stocks add up to zero.")
    return w / w.sum()


def market_cap_weights(prices_today: pd.Series, shares: pd.Series) -> pd.Series:
    """Bigger companies get more: weight = price x shares outstanding, as a share of the total."""
    caps = prices_today * shares.reindex(prices_today.index)
    if caps.isna().any():
        missing = ", ".join(caps[caps.isna()].index)
        raise ValueError(f"No share count for {missing}: market-cap weights are not possible. Pick another scheme.")
    return caps / caps.sum()


def inverse_vol_weights(recent_returns: pd.DataFrame) -> pd.Series:
    """Calmer stocks get more: weight proportional to 1 / volatility over the recent window."""
    inv = 1.0 / recent_returns.std()
    return inv / inv.sum()


def cap_weights(w: pd.Series, max_weight: float) -> pd.Series:
    """Limit any single stock to `max_weight`, handing the excess to the others in proportion."""
    if max_weight >= 1:
        return w
    if max_weight * len(w) < 1 - 1e-12:
        raise ValueError(f"A {max_weight:.0%} cap is impossible with {len(w)} stocks (they could not reach 100%).")
    w = w.copy()
    for _ in range(len(w)):
        over = w > max_weight + 1e-12
        if not over.any():
            break
        excess = (w[over] - max_weight).sum()
        w[over] = max_weight
        free = ~over & (w < max_weight)
        w[free] += excess * w[free] / w[free].sum()
    return w


def rebalance_dates(index: pd.DatetimeIndex, frequency: str) -> pd.DatetimeIndex:
    """Trading days on which we trade back to the target weights (at the close).

    none = never (buy and hold), daily = every day, otherwise the last trading day
    of each month, quarter or year (the current, unfinished period has not ended yet).
    """
    if frequency == "none":
        return pd.DatetimeIndex([])
    if frequency == "daily":
        return index
    period = {"monthly": "M", "quarterly": "Q", "yearly": "Y"}[frequency]
    ends = index.to_series().groupby(index.to_period(period)).max()
    return pd.DatetimeIndex(ends.values[:-1])  # the last period is still running: no rebalance yet


def target_weights(
    cfg: RiskConfig,
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    shares: pd.DataFrame | pd.Series,
    dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Target weights on each date in `dates` (one row per date), using only data up to that date.

    inverse_vol uses equal weights until `vol_lookback` days of history exist.
    """
    spec = cfg.portfolio
    tickers = list(prices.columns)
    rows = {}
    for d in dates:
        if spec.scheme == "equal":
            w = equal_weights(tickers)
        elif spec.scheme == "custom":
            w = custom_weights(cfg, tickers)
        elif spec.scheme == "market_cap":
            if isinstance(shares, pd.Series):
                # Retained for the small pure-function API; production code passes
                # a dated table and never uses current profile shares historically.
                share_row = shares
            else:
                share_row = shares.reindex(index=dates, method="ffill").loc[d]
            w = market_cap_weights(prices.loc[d], share_row)
        else:
            past = returns.loc[:d].tail(spec.vol_lookback)
            w = inverse_vol_weights(past) if len(past) >= spec.vol_lookback else equal_weights(tickers)
        if spec.scheme in ("market_cap", "inverse_vol"):
            w = cap_weights(w, spec.max_weight)
        rows[d] = w
    return pd.DataFrame(rows).T.reindex(columns=tickers)


def exposure(w: pd.Series) -> dict[str, float]:
    """Long, short, net and gross exposure of a set of weights (net is always 100% here)."""
    long, short = float(w[w > 0].sum()), float(-w[w < 0].sum())
    return {"long": long, "short": short, "net": long - short, "gross": long + short}


def shares_from_profiles(profiles: dict, tickers: list[str]) -> pd.Series:
    """Return profile share counts by ticker, using NaN when unavailable."""
    return pd.Series(
        {t: (profiles[t].shares_outstanding if t in profiles else None) for t in tickers}, dtype=float
    ).replace(0, np.nan)
