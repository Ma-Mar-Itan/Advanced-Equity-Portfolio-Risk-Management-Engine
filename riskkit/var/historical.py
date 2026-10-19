"""Historical simulation: line up past days from worst to best and read off the tail.

Rule used everywhere: with N scenarios and tail probability p = 1 - confidence,
the tail holds k = ceil(p x N) scenarios (at least 1).
  VaR = the k-th worst loss        (the edge of the cliff)
  ES  = the average of the k worst (how far the fall is, on average)
Returns are LOG returns; losses are reported as positive SIMPLE losses (0.02 = 2% of value).
"""

from __future__ import annotations

import math

import numpy as np


def tail_size(n: int, confidence: float) -> int:
    """How many of the n scenarios are in the tail: 500 scenarios at 99% -> 5."""
    return max(1, math.ceil(round((1 - confidence) * n, 9)))


def losses_from_log_returns(log_returns: np.ndarray) -> np.ndarray:
    """Positive numbers are losses as a share of value: a -2% simple move is a loss of 0.02."""
    return -np.expm1(log_returns)


def var_es(log_returns: np.ndarray, confidence: float) -> tuple[float, float]:
    """VaR and ES (positive loss fractions) from a set of scenario log returns."""
    losses = losses_from_log_returns(np.asarray(log_returns, dtype=float))
    losses = losses[~np.isnan(losses)]
    k = tail_size(len(losses), confidence)
    worst = np.partition(losses, len(losses) - k)[len(losses) - k:]   # the k largest losses
    return float(worst.min()), float(worst.mean())
