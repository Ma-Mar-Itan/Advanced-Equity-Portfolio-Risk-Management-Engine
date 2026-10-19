"""Turn prices into daily returns.

Simple return: (today - yesterday) / yesterday.  $100 -> $102 is +2%.
Log return:    ln(today / yesterday).           $100 -> $102 is +1.98%.
They are almost equal on normal days. Log returns add up across days (handy for
multi-day risk); simple returns add up across stocks (handy for portfolios).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily percentage change; the first day (no yesterday) is dropped."""
    return prices.pct_change().iloc[1:]


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily natural-log change; the first day is dropped."""
    return np.log(prices / prices.shift(1)).iloc[1:]


def to_returns(prices: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Simple or log returns, chosen by name ('simple' or 'log')."""
    return log_returns(prices) if kind == "log" else simple_returns(prices)


def log_to_simple(r: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Convert log returns back to simple returns (needed to combine stocks into a portfolio)."""
    return np.expm1(r)
