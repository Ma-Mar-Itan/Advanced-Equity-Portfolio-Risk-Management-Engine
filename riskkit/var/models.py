"""The four VaR models of the brief, and the volatility path each one uses.

HS        - plain historical simulation (no scaling)
EWMA-HS   - past returns rescaled by EWMA volatility
GARCH-HS  - past returns rescaled by GARCH(1,1) volatility
GJR-HS    - past returns rescaled by GJR-GARCH volatility

Scaling: scenario_i = return_i x (volatility forecast for tomorrow / volatility on day i).

No look-ahead: for the rolling (backtest) version, GARCH parameters are re-estimated every
`refit_every` days on data up to that day only, and filtered forward in between.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.config import RiskConfig
from riskkit.volatility.ewma import ewma_variance
from riskkit.volatility.garch import GarchVol, garch_filter

MIN_TRAIN = 500   # days of history needed before the first GARCH fit


def vol_kind(model: str) -> str | None:
    """Which volatility model a VaR model rescales with (None for plain HS)."""
    return {"HS": None, "EWMA-HS": "ewma", "GARCH-HS": "garch", "GJR-HS": "gjr"}[model]


def fit_garch_params(returns: np.ndarray, kind: str, cfg: RiskConfig) -> dict[str, float]:
    """Estimate GARCH or GJR parameters on the returns given (and nothing later)."""
    v = cfg.volatility
    model = GarchVol(asymmetric=kind == "gjr", dist=v.garch_dist, mean=v.garch_mean)
    return model.fit(pd.Series(returns), horizon=1).params


def sigma_today(returns: np.ndarray, model: str, cfg: RiskConfig) -> np.ndarray | None:
    """Volatility for each day in `returns` plus tomorrow (len + 1), fitted on all of `returns`.

    Used for today's VaR, where every return is in the past. None for plain HS.
    """
    kind = vol_kind(model)
    if kind is None:
        return None
    if kind == "ewma":
        return np.sqrt(ewma_variance(returns, cfg.volatility.ewma_lambda))
    return garch_filter(returns, fit_garch_params(returns, kind, cfg))


def sigma_rolling(returns: np.ndarray, model: str, cfg: RiskConfig, first: int) -> dict[int, np.ndarray]:
    """For each refit block, the volatility path known on that block's days (no look-ahead).

    Returns {block start index: sigma array of length len(returns) + 1}, where the parameters were
    estimated on returns[:start] only. EWMA has fixed parameters, so it is one block from day 0.
    """
    kind = vol_kind(model)
    if kind == "ewma":
        return {0: np.sqrt(ewma_variance(returns, cfg.volatility.ewma_lambda))}
    blocks = {}
    for start in range(first, len(returns), cfg.var.refit_every):
        params = fit_garch_params(returns[:start], kind, cfg)
        blocks[start] = garch_filter(returns, params)
    return blocks


def scaled_scenarios(window: np.ndarray, sigma_window: np.ndarray, sigma_next: float) -> np.ndarray:
    """Past returns rescaled to the volatility expected tomorrow."""
    return window * sigma_next / sigma_window
