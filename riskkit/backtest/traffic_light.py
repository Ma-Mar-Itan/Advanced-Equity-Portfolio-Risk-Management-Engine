"""Basel traffic light: how many exceptions are acceptable over the last 250 days at 99%?

The 1996 Basel table: 0-4 green, 5-9 yellow, 10 or more red. Those cut-offs come from the
binomial distribution: green while a correct model would show that many exceptions with
less than 95% cumulative probability, red once it passes 99.99%. The same rule gives the
zones for any window length and confidence level.
"""

from __future__ import annotations

import pandas as pd
from scipy.stats import binom

ZONES = ("green", "yellow", "red")


def zone_limits(days: int = 250, p: float = 0.01) -> tuple[int, int]:
    """Smallest exception counts that start the yellow and the red zone (Basel: 5 and 10)."""
    yellow = next(k for k in range(days + 1) if binom.cdf(k, days, p) >= 0.95)
    red = next(k for k in range(days + 1) if binom.cdf(k, days, p) >= 0.9999)
    return yellow, red


def zone(exceptions: int, days: int = 250, p: float = 0.01) -> str:
    """'green', 'yellow' or 'red' for a number of exceptions."""
    yellow, red = zone_limits(days, p)
    return "red" if exceptions >= red else "yellow" if exceptions >= yellow else "green"


def rolling_zone(hits: pd.Series, days: int = 250, p: float = 0.01) -> pd.DataFrame:
    """For every day: exceptions in the previous `days` days and the resulting zone."""
    count = hits.astype(int).rolling(days).sum().dropna().astype(int)
    yellow, red = zone_limits(days, p)
    zones = count.map(lambda k: "red" if k >= red else "yellow" if k >= yellow else "green")
    return pd.DataFrame({"exceptions": count, "zone": zones})
