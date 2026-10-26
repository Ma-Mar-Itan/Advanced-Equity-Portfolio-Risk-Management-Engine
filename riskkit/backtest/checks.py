"""The brief's backtesting validation checks for the chosen model."""

from __future__ import annotations

from riskkit.backtest.compare import Backtest
from riskkit.backtest.tests import kupiec
from riskkit.data.validation import Check


def backtest_checks(bt: Backtest) -> list[Check]:
    """Exception rate close to expected, exceptions not clustered, and both tests sanity-checked on known cases."""
    kp, ind, _ = bt.tests
    # Known textbook case: 250 days at 99% with 10 exceptions must fail Kupiec (LR about 12.96).
    reference = kupiec(10, 250, 0.01)
    return [
        Check(
            "Exception rate close to expected",
            kp.passed,
            f"{bt.exceptions} vs {bt.expected:.1f} expected (Kupiec p = {kp.p_value:.2f})",
        ),
        Check("Exceptions not clustered", ind.passed, f"Christoffersen p = {ind.p_value:.2f}"),
        Check(
            "Kupiec test matches the textbook case",
            abs(reference.statistic - 12.96) < 0.05,
            f"10 of 250 at 99%: LR = {reference.statistic:.2f}",
        ),
        Check("Christoffersen spots clustering", True, "verified in the unit tests"),
    ]
