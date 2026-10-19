"""The one interface every volatility model shares.

A model takes daily returns in and gives back a VolFit: the volatility it estimated
for every day, a forecast for the days ahead, and its parameters. The VaR code
(Module 5) only ever sees VolFit, so it works with any model.

Timing rule (no look-ahead): sigma on day t uses returns up to day t-1 only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass(frozen=True)
class VolFit:
    """What every volatility model returns. All volatilities are DAILY (not yearly)."""

    name: str
    sigma: pd.Series                 # volatility for each day, known the evening before
    forecast: np.ndarray             # forecast volatility for 1, 2, ..., horizon days ahead
    params: dict[str, float] = field(default_factory=dict)

    @property
    def next_day(self) -> float:
        """Tomorrow's volatility forecast."""
        return float(self.forecast[0])

    def std_residuals(self, returns: pd.Series) -> pd.Series:
        """Each return divided by the volatility expected for that day (should look like plain noise)."""
        return (returns / self.sigma).dropna()


class VolModel(Protocol):
    """Anything that can turn a return series into a VolFit."""

    name: str

    def fit(self, returns: pd.Series, horizon: int = 10) -> VolFit:
        """Estimate volatility for every day and forecast `horizon` days ahead."""
        ...


def annualize(daily_vol: pd.Series | float | np.ndarray) -> pd.Series | float | np.ndarray:
    """Daily volatility -> yearly volatility (x sqrt(252))."""
    return daily_vol * np.sqrt(TRADING_DAYS)


def horizon_vol(fit: VolFit, days: int) -> float:
    """Volatility of the total return over the next `days` days (adds up each day's variance)."""
    return float(np.sqrt(np.sum(fit.forecast[:days] ** 2)))
