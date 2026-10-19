"""Module 4 in one call, plus the volatility analyses shown on the Volatility page.

- fit_all: run every model on one return series (same interface for each)
- volatility_regimes: label each day calm / normal / stormy by its volatility
- scale_to_today: rescale past returns to today's volatility (the trick Module 5 uses)
- leverage_effect: does a down day raise tomorrow's volatility more than an up day?
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.config import VolatilitySpec
from riskkit.volatility.base import VolFit, VolModel
from riskkit.volatility.ewma import EWMAVol
from riskkit.volatility.garch import GarchVol
from riskkit.volatility.rolling import RollingVol

REGIMES = ("Calm", "Normal", "Stormy")


def build_models(spec: VolatilitySpec) -> list[VolModel]:
    """The four models of the brief, configured from the settings."""
    return [RollingVol(spec.rolling_window), EWMAVol(spec.ewma_lambda),
            GarchVol(False, spec.garch_dist, spec.garch_mean), GarchVol(True, spec.garch_dist, spec.garch_mean)]


def fit_all(returns: pd.Series, spec: VolatilitySpec) -> dict[str, VolFit]:
    """Fit every model to the same returns; keyed by model name."""
    return {m.name: m.fit(returns, spec.horizon) for m in build_models(spec)}


def volatility_regimes(sigma: pd.Series, calm: float = 1 / 3, stormy: float = 2 / 3) -> pd.Series:
    """Label each day by where its volatility sits: lowest third Calm, top third Stormy."""
    low, high = sigma.quantile(calm), sigma.quantile(stormy)
    labels = np.where(sigma <= low, REGIMES[0], np.where(sigma >= high, REGIMES[2], REGIMES[1]))
    return pd.Series(labels, index=sigma.index, name="regime")


def regime_table(returns: pd.Series, regimes: pd.Series) -> pd.DataFrame:
    """For each regime: share of days, typical daily move, worst day, share of big losses (< -3%)."""
    df = pd.concat([returns.rename("r"), regimes], axis=1).dropna()
    rows = []
    for name in REGIMES:
        r = df.loc[df["regime"] == name, "r"]
        rows.append({"regime": name, "share of days": len(r) / len(df), "typical move": r.std(),
                     "worst day": r.min(), "days below -3%": int((r < -0.03).sum())})
    return pd.DataFrame(rows)


def scale_to_today(returns: pd.Series, fit: VolFit) -> pd.Series:
    """Each past return x (tomorrow's volatility / that day's volatility).

    A -2% day in a calm year becomes bigger if today is stormy, and smaller if today is calm.
    This is volatility-scaled ("filtered") historical simulation, used in Module 5.
    """
    sigma = fit.sigma.reindex(returns.index)
    return (returns * fit.next_day / sigma).dropna()


def leverage_effect(returns: pd.Series, days_after: int = 5) -> pd.DataFrame:
    """Model-free check of the leverage effect: how big are the next few days' moves after each kind of day?

    Groups days by their return, then averages the absolute size of the following `days_after`
    returns. If down days are followed by bigger moves than up days of the same size, bad news
    raises volatility more than good news.
    """
    future = returns.abs().rolling(days_after).mean().shift(-days_after)
    df = pd.concat([returns.rename("r"), future.rename("next")], axis=1).dropna()
    bins = [-np.inf, -0.03, -0.015, -0.005, 0.005, 0.015, 0.03, np.inf]
    labels = ["below -3%", "-3% to -1.5%", "-1.5% to -0.5%", "-0.5% to +0.5%", "+0.5% to +1.5%",
              "+1.5% to +3%", "above +3%"]
    df["move"] = pd.cut(df["r"], bins, labels=labels)
    out = df.groupby("move", observed=False)["next"].agg(["mean", "count"]).reset_index()
    return out.rename(columns={"mean": f"avg move next {days_after} days", "count": "days"})
