"""Stock-level scenarios behind the portfolio VaR, shared by attribution and the decision tools.

Each of the last `window` days becomes one scenario: every stock's simple return that day,
rescaled by the SAME factor the portfolio VaR model uses for that day
(tomorrow's portfolio volatility / that day's portfolio volatility; 1 for plain HS).
Portfolio scenario = sum of weight x stock scenario.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.collect import MarketData
from riskkit.data.pipeline import CleanData
from riskkit.portfolio.construction import Portfolio, simple_asset_returns
from riskkit.var.historical import tail_size
from riskkit.var.models import sigma_today


@dataclass(frozen=True)
class Scenarios:
    """Stock returns per scenario (rows) and stock (columns), today's weights and the portfolio value."""

    assets: pd.DataFrame
    benchmark: pd.Series
    weights: pd.Series
    value: float
    confidence: float

    def portfolio(self, weights: pd.Series | None = None) -> pd.Series:
        """Portfolio return in each scenario (simple returns)."""
        w = self.weights if weights is None else weights
        return self.assets[w.index] @ w

    def tail(self, weights: pd.Series | None = None) -> pd.Index:
        """The scenarios in the loss tail (the k worst for the portfolio)."""
        p = self.portfolio(weights)
        return p.nsmallest(tail_size(len(p), self.confidence)).index


def var_es_simple(port: pd.Series, confidence: float) -> tuple[float, float]:
    """VaR and ES (positive loss shares) from portfolio simple-return scenarios."""
    losses = np.sort(-port.to_numpy())[::-1]
    k = tail_size(len(losses), confidence)
    return float(losses[k - 1]), float(losses[:k].mean())


def build_scenarios(cd: CleanData, md: MarketData, p: Portfolio, cfg: RiskConfig) -> Scenarios:
    """The last `window` days of stock returns, scaled like the portfolio VaR model, with today's weights."""
    assets = simple_asset_returns(cd, cfg.cleaning.return_type).reindex(p.log_returns.index)
    sigma = sigma_today(p.log_returns.to_numpy(), cfg.var.model, cfg)
    factor = np.ones(len(assets)) if sigma is None else sigma[-1] / sigma[:-1]
    scaled = assets.mul(factor, axis=0).iloc[-cfg.window:]
    bench = md.benchmark.pct_change().reindex(p.log_returns.index).fillna(0.0) * factor
    return Scenarios(scaled, bench.iloc[-cfg.window:], p.current_weights, float(p.value.iloc[-1]), cfg.confidence)
