"""Rolling volatility: the standard deviation of the last N daily returns, all weighted equally.

Simple and transparent, but slow to react, and a crash drops out of the window
all at once N days later (the 'ghost' effect).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.volatility.base import TRADING_DAYS, VolFit


def rolling_volatility(
    returns: pd.DataFrame | pd.Series, window: int = 21, annualize: bool = True
) -> pd.DataFrame | pd.Series:
    """Standard deviation of the last `window` daily returns (including today), yearly if `annualize`."""
    vol = returns.rolling(window).std().dropna(how="all")
    return vol * np.sqrt(TRADING_DAYS) if annualize else vol


class RollingVol:
    """Equal-weight volatility of the previous `window` days."""

    def __init__(self, window: int = 63) -> None:
        self.window = window
        self.name = f"Rolling {window}d"

    def fit(self, returns: pd.Series, horizon: int = 10) -> VolFit:
        """sigma_t = std of returns t-window ... t-1; the forecast is flat at the latest value."""
        sigma = returns.rolling(self.window).std().shift(1).dropna()
        latest = float(returns.iloc[-self.window :].std())
        return VolFit(self.name, sigma, np.full(horizon, latest), {"window": self.window})
