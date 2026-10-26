"""EWMA (RiskMetrics) volatility: recent days count more, older days fade away.

    variance_t = lambda * variance_{t-1} + (1 - lambda) * return_{t-1}^2

With lambda = 0.94, yesterday's squared return gets weight 6%, the day before 5.64%,
and so on, shrinking by 6% each day back. EWMA has no pull towards a long-run level,
so its forecast for every future day equals tomorrow's.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.volatility.base import VolFit

SEED_DAYS = 30


def ewma_variance(returns: np.ndarray, lam: float, seed_days: int = SEED_DAYS) -> np.ndarray:
    """Variance for each day plus one extra value for tomorrow (length n + 1), started from the sample variance."""
    var = np.empty(len(returns) + 1)
    var[0] = np.var(returns[:seed_days])
    for t, r in enumerate(returns):
        var[t + 1] = lam * var[t] + (1 - lam) * r * r
    return var


class EWMAVol:
    """Exponentially weighted volatility with memory `lam`."""

    def __init__(self, lam: float = 0.94) -> None:
        self.lam = lam
        self.name = "EWMA"

    def fit(self, returns: pd.Series, horizon: int = 10) -> VolFit:
        """sigma_t from the EWMA recursion; the first SEED_DAYS are dropped as warm-up."""
        var = ewma_variance(returns.to_numpy(), self.lam)
        sigma = pd.Series(np.sqrt(var[:-1]), index=returns.index).iloc[SEED_DAYS:]
        half_life = np.log(0.5) / np.log(self.lam)
        return VolFit(
            self.name,
            sigma,
            np.full(horizon, np.sqrt(var[-1])),
            {"lambda": self.lam, "half-life (days)": float(half_life)},
        )
