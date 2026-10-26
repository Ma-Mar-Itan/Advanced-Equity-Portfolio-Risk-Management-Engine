"""VaR backtesting, model comparison, and ranking.

Models are ranked by conditional-coverage results, Basel zone, deviation from
the expected exception count, and average VaR, in that order.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from riskkit.backtest.tests import TestResult, christoffersen_independence, conditional_coverage, kupiec
from riskkit.backtest.traffic_light import ZONES, zone


@dataclass(frozen=True)
class Backtest:
    """Everything known about one model's track record."""

    model: str
    days: int
    exceptions: int
    expected: float
    hits: pd.Series  # True on exception days
    tests: list[TestResult]
    zone_last_250: str
    exceptions_last_250: int

    @property
    def ratio(self) -> float:
        """Actual exceptions / expected exceptions (1.0 = perfect)."""
        return self.exceptions / self.expected

    @property
    def passed_all(self) -> bool:
        """True when every test passes."""
        return all(t.passed for t in self.tests)


def backtest(
    model: str, rolling: pd.DataFrame, confidence: float, significance: float = 0.05, start: pd.Timestamp | None = None
) -> Backtest:
    """Compare each day's VaR forecast with the loss that followed."""
    df = rolling.loc[start:] if start is not None else rolling
    hits = df["actual"] > df["var"]
    p, n, k = 1 - confidence, len(hits), int(hits.sum())
    last = hits.iloc[-250:]
    tests = [
        kupiec(k, n, p, significance),
        christoffersen_independence(hits.to_numpy(), significance),
        conditional_coverage(hits.to_numpy(), p, significance),
    ]
    return Backtest(model, n, k, n * p, hits, tests, zone(int(last.sum()), len(last), p), int(last.sum()))


def exceptions_table(rolling: pd.DataFrame, value: float) -> pd.DataFrame:
    """Every exception day: the VaR forecast, the actual loss, and by how much it was beaten ($)."""
    df = rolling[rolling["actual"] > rolling["var"]]
    return pd.DataFrame(
        {
            "date": df.index,
            "var": df["var"] * value,
            "loss": df["actual"] * value,
            "excess": (df["actual"] - df["var"]) * value,
        }
    ).sort_values("date", ascending=False)


def comparison_table(
    rollings: dict[str, pd.DataFrame],
    confidence: float,
    value: float,
    significance: float = 0.05,
    start: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Return comparison metrics and a deterministic rank for each model."""
    rows = []
    for model, df in rollings.items():
        df = df.loc[start:] if start is not None else df
        bt = backtest(model, df, confidence, significance)
        kp, ind, cc = (t.p_value for t in bt.tests)
        rows.append(
            {
                "model": model,
                "exceptions": bt.exceptions,
                "expected": bt.expected,
                "ratio": bt.ratio,
                "average VaR": df["var"].mean() * value,
                "VaR volatility": df["var"].std() * value,
                "worst daily loss": df["actual"].max() * value,
                "average ES": df["es"].mean() * value,
                "Kupiec p": kp,
                "Christoffersen p": ind,
                "Coverage p": cc,
                "zone": bt.zone_last_250,
                "passes all": bt.passed_all,
            }
        )
    t = pd.DataFrame(rows)
    t["_zone"] = t["zone"].map(ZONES.index)
    t["_miss"] = (t["ratio"] - 1).abs()
    t = t.sort_values(["passes all", "_zone", "_miss", "average VaR"], ascending=[False, True, True, True])
    t["rank"] = np.arange(1, len(t) + 1)
    return t.drop(columns=["_zone", "_miss"]).reset_index(drop=True)
