"""Statistical tests on VaR exceptions (days the loss beat the VaR).

- Kupiec (1995) "proportion of failures": is the NUMBER of exceptions believable?
- Christoffersen (1998) independence: do exceptions arrive at RANDOM times, or in clusters?
- Christoffersen conditional coverage: both at once.
Each returns a likelihood-ratio statistic and a p-value; p < 5% means the model fails that test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2


@dataclass(frozen=True)
class TestResult:
    """One test: its statistic, p-value and verdict at the chosen significance level."""

    name: str
    statistic: float
    p_value: float
    passed: bool


def _log_likelihood(count: int, trials: int, prob: float) -> float:
    """log of prob^count x (1 - prob)^(trials - count), with 0 x log(0) treated as 0."""
    out = 0.0
    if count > 0:
        out += count * np.log(prob)
    if trials - count > 0:
        out += (trials - count) * np.log(1 - prob)
    return out


def kupiec(exceptions: int, days: int, p: float, significance: float = 0.05) -> TestResult:
    """Kupiec proportion-of-failures test: compare the observed exception rate with the expected rate p."""
    observed = exceptions / days
    lr = -2 * (_log_likelihood(exceptions, days, p) - _log_likelihood(exceptions, days, observed))
    pv = float(chi2.sf(lr, df=1))
    return TestResult("Kupiec: count", float(lr), pv, pv >= significance)


def transition_counts(hits: np.ndarray) -> tuple[int, int, int, int]:
    """How often an exception day / normal day was followed by an exception / normal day: n00, n01, n10, n11."""
    prev, nxt = hits[:-1], hits[1:]
    return (int(np.sum(~prev & ~nxt)), int(np.sum(~prev & nxt)), int(np.sum(prev & ~nxt)), int(np.sum(prev & nxt)))


def christoffersen_independence(hits: np.ndarray, significance: float = 0.05) -> TestResult:
    """Is an exception more likely the day after an exception? (clustering)"""
    hits = np.asarray(hits, dtype=bool)
    n00, n01, n10, n11 = transition_counts(hits)
    pi0 = n01 / (n00 + n01) if n00 + n01 else 0.0
    pi1 = n11 / (n10 + n11) if n10 + n11 else 0.0
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)
    restricted = _log_likelihood(n01 + n11, n00 + n01 + n10 + n11, pi) if 0 < pi < 1 else 0.0
    free = (_log_likelihood(n01, n00 + n01, pi0) if 0 < pi0 < 1 else 0.0) + \
           (_log_likelihood(n11, n10 + n11, pi1) if 0 < pi1 < 1 else 0.0)
    lr = max(0.0, -2 * (restricted - free))
    pv = float(chi2.sf(lr, df=1))
    return TestResult("Christoffersen: timing", float(lr), pv, pv >= significance)


def conditional_coverage(hits: np.ndarray, p: float, significance: float = 0.05) -> TestResult:
    """Right number AND random timing: Kupiec + independence statistics, 2 degrees of freedom."""
    hits = np.asarray(hits, dtype=bool)
    lr = kupiec(int(hits.sum()), len(hits), p).statistic + christoffersen_independence(hits).statistic
    pv = float(chi2.sf(lr, df=2))
    return TestResult("Coverage: both", float(lr), pv, pv >= significance)
