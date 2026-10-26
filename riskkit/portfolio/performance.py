"""Headline numbers for the portfolio, the benchmark comparison, and the portfolio checks.

- Annual return: the steady yearly growth rate that gets from the start value to the end value.
- Annual volatility: the typical size of a day's move, scaled to a year (x sqrt(252)).
- Sharpe ratio: extra return over the safe rate, per unit of volatility (higher = better reward for risk).
- Beta: how much the portfolio moves when the market moves 1% (1.2 = 1.2% on average).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.data.validation import Check
from riskkit.portfolio.construction import Portfolio
from riskkit.portfolio.drawdown import max_drawdown

TRADING_DAYS = 252


def annual_return(value: pd.Series) -> float:
    """Compound yearly growth rate between the first and last value."""
    years = len(value.iloc[1:]) / TRADING_DAYS
    return float((value.iloc[-1] / value.iloc[0]) ** (1 / years) - 1)


def annual_volatility(returns: pd.Series) -> float:
    """Standard deviation of daily returns, scaled to a year."""
    return float(returns.std() * np.sqrt(TRADING_DAYS))


def sharpe_ratio(returns: pd.Series, risk_free_daily: pd.Series) -> float:
    """Average daily return above the risk-free rate, divided by its volatility, scaled to a year."""
    excess = returns - risk_free_daily.reindex(returns.index).fillna(0.0)
    return float(excess.mean() / excess.std() * np.sqrt(TRADING_DAYS))


def summary_stats(p: Portfolio, risk_free_daily: pd.Series) -> dict[str, float]:
    """The headline numbers shown at the top of the Portfolio page."""
    r = p.returns
    return {
        "start value": float(p.value.iloc[0]),
        "end value": float(p.value.iloc[-1]),
        "total return": float(p.value.iloc[-1] / p.value.iloc[0] - 1),
        "annual return": annual_return(p.value),
        "annual volatility": annual_volatility(r),
        "sharpe": sharpe_ratio(r, risk_free_daily),
        "max drawdown": max_drawdown(p.value),
        "best day": float(r.max()),
        "worst day": float(r.min()),
        "positive days": float((r > 0).mean()),
        "worst day $": float(p.pnl.min()),
        "total costs": float(p.costs.sum()),
        "average turnover": float(p.turnover[p.turnover > 0].mean()) if (p.turnover > 0).any() else 0.0,
    }


def benchmark_value(benchmark_prices: pd.Series, like: pd.Series) -> pd.Series:
    """The benchmark rescaled to start at the portfolio's first value, on the portfolio's dates."""
    b = benchmark_prices.reindex(like.index).ffill().bfill()
    return b / b.iloc[0] * like.iloc[0]


def benchmark_comparison(p: Portfolio, benchmark_prices: pd.Series) -> dict[str, float]:
    """Portfolio versus the market: beta, correlation, tracking error and return gap per year."""
    b = benchmark_prices.reindex(p.value.index).ffill().pct_change().reindex(p.returns.index)
    both = pd.concat([p.returns, b], axis=1, keys=["p", "b"]).dropna()
    beta = both["p"].cov(both["b"]) / both["b"].var()
    gap = both["p"] - both["b"]
    bvalue = benchmark_value(benchmark_prices, p.value)
    return {
        "beta": float(beta),
        "correlation": float(both["p"].corr(both["b"])),
        "tracking error": float(gap.std() * np.sqrt(TRADING_DAYS)),
        "benchmark annual return": annual_return(bvalue),
        "excess annual return": annual_return(p.value) - annual_return(bvalue),
    }


def portfolio_checks(p: Portfolio) -> list[Check]:
    """The brief's portfolio checks: weights add up and the P&L is calculated correctly."""
    sums = p.targets.sum(axis=1)
    weights_ok = bool(np.allclose(sums, 1.0))
    pnl_from_stocks = p.contributions.sum(axis=1) - p.costs
    pnl_ok = bool(np.allclose(pnl_from_stocks, p.pnl, rtol=1e-9, atol=1e-6 * p.value.abs().max()))
    total_ok = bool(np.isclose(p.pnl.sum(), p.value.iloc[-1] - p.value.iloc[0]))
    return [
        Check("Weights sum to 100% on every rebalance", weights_ok, f"{len(sums)} rebalances checked"),
        Check("Daily P&L = sum of stock P&Ls - costs", pnl_ok, "every day matches" if pnl_ok else "mismatch"),
        Check("P&L adds up to the change in value", total_ok, "ok" if total_ok else "mismatch"),
    ]
