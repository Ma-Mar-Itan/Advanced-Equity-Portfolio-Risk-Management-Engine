"""The brief's data validation checks, each returned as pass/fail with a short reason."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.returns import to_returns


@dataclass(frozen=True)
class Check:
    """One validation check: its name, whether it passed, and a plain-English detail."""

    name: str
    passed: bool
    detail: str


def check_no_missing(returns: pd.DataFrame) -> Check:
    """Every stock has a return on every date."""
    n = int(returns.isna().sum().sum())
    return Check("No missing return dates", n == 0, "none missing" if n == 0 else f"{n} missing values")


def check_dates_in_order(returns: pd.DataFrame) -> Check:
    """Dates go forward one by one with no duplicates."""
    ok = returns.index.is_monotonic_increasing and returns.index.is_unique
    return Check("Dates in order, no duplicates", ok, "ok" if ok else "unsorted or repeated dates")


def check_weights(cfg: RiskConfig) -> Check:
    """Portfolio weights add up to 100%."""
    total = sum(cfg.weight_of(t) for t in cfg.tickers)
    ok = abs(total - 1) < 1e-6
    return Check("Weights sum to 100%", ok, f"{total:.2%}")


def check_positive_prices(prices: pd.DataFrame) -> Check:
    """No zero or negative prices (they would make returns meaningless)."""
    bad = int((prices <= 0).sum().sum())
    return Check("All prices positive", bad == 0, "ok" if bad == 0 else f"{bad} non-positive prices")


def check_finite(returns: pd.DataFrame) -> Check:
    """No infinite or undefined returns."""
    bad = int((~np.isfinite(returns)).sum().sum())
    return Check("All returns finite", bad == 0, "ok" if bad == 0 else f"{bad} infinite values")


def check_aligned(prices: pd.DataFrame, raw_returns: pd.DataFrame, kind: str) -> Check:
    """The return on day t is computed from the prices of day t and day t-1 (no look-ahead, no shift)."""
    expected = to_returns(prices, kind)
    ok = expected.index.equals(raw_returns.index) and np.allclose(expected, raw_returns, equal_nan=True)
    return Check("Returns aligned with prices", ok, "day t uses prices t-1 and t" if ok else "mismatch")


def run_checks(cfg: RiskConfig, prices: pd.DataFrame, raw_returns: pd.DataFrame,
               returns: pd.DataFrame) -> list[Check]:
    """All Module 2 checks in one list."""
    return [check_no_missing(returns), check_dates_in_order(returns), check_weights(cfg),
            check_positive_prices(prices), check_finite(returns),
            check_aligned(prices, raw_returns, cfg.cleaning.return_type)]
