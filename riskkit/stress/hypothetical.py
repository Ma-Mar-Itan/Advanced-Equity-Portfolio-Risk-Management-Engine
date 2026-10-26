"""Made-up but plausible shocks applied to today's portfolio.

All functions return losses as a positive share of portfolio value, plus each stock's part.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.var.historical import var_es


def market_shock(weights: pd.Series, beta: pd.Series, shock: float) -> pd.Series:
    """The market moves `shock` (e.g. -0.10); each stock moves beta x shock. Returns each stock's loss."""
    return -(weights * beta * shock)


def sector_shock(
    weights: pd.Series, beta: pd.Series, sectors: pd.Series, sector: str, shock: float, spillover: float = 0.0
) -> pd.Series:
    """Stocks in `sector` move `shock`; the others move beta x shock x spillover. Returns each stock's loss."""
    inside = sectors.reindex(weights.index) == sector
    moves = np.where(inside, shock, beta * shock * spillover)
    return -(weights * moves)


def custom_shock(weights: pd.Series, moves: dict[str, float]) -> pd.Series:
    """Your own move for each stock (missing stocks do not move). Returns each stock's loss."""
    return -(weights * pd.Series(moves).reindex(weights.index).fillna(0.0))


def volatility_shock(scenarios: np.ndarray, multiplier: float, confidence: float) -> tuple[float, float]:
    """VaR/ES if every replayed day were `multiplier` times as big (volatility multiplied)."""
    return var_es(np.asarray(scenarios) * multiplier, confidence)


def blended_correlation(corr: pd.DataFrame, blend: float) -> pd.DataFrame:
    """Move every correlation `blend` of the way towards 1 (crisis: everything falls together)."""
    ones = pd.DataFrame(1.0, index=corr.index, columns=corr.columns)
    return (1 - blend) * corr + blend * ones


def correlation_shock_ratio(asset_returns: pd.DataFrame, weights: pd.Series, blend: float) -> float:
    """How much portfolio volatility rises when correlations jump towards 1 (stressed / normal)."""
    vol = asset_returns.std()
    corr = asset_returns.corr()
    w = weights.reindex(asset_returns.columns).to_numpy()
    d = np.diag(vol.to_numpy())

    def port_vol(c: pd.DataFrame) -> float:
        return float(np.sqrt(w @ d @ c.to_numpy() @ d @ w))

    return port_vol(blended_correlation(corr, blend)) / port_vol(corr)
