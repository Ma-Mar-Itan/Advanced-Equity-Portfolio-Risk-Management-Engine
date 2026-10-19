"""Split the portfolio's VaR and ES into each stock's share (Euler allocation).

Like splitting a restaurant bill by what each person ate: each stock's share is its weight
times its average return on the portfolio's worst days, so the shares add up to the total.
- ES share:  -weight x average stock return over the k worst portfolio scenarios (exact)
- VaR share: the same, averaged over the few scenarios around the VaR scenario (smoothed)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.attribution.scenarios import Scenarios, var_es_simple
from riskkit.var.historical import tail_size

VAR_NEIGHBOURS = 2     # scenarios either side of the VaR scenario used to smooth the VaR split


def component_es(sc: Scenarios) -> pd.Series:
    """Each stock's dollar-free share of ES (sums to portfolio ES)."""
    tail = sc.tail()
    return -(sc.weights * sc.assets.loc[tail, sc.weights.index].mean())


def component_var(sc: Scenarios) -> pd.Series:
    """Each stock's share of VaR, smoothed over the scenarios ranked next to the VaR scenario,
    then rescaled so the shares add up exactly to the portfolio VaR."""
    order = sc.portfolio().sort_values().index
    k = tail_size(len(order), sc.confidence)
    near = order[max(0, k - 1 - VAR_NEIGHBOURS): k + VAR_NEIGHBOURS]
    raw = -(sc.weights * sc.assets.loc[near, sc.weights.index].mean())
    return raw * var_es_simple(sc.portfolio(), sc.confidence)[0] / raw.sum()


def attribution_table(sc: Scenarios, sectors: pd.Series) -> pd.DataFrame:
    """Per stock: weight, VaR and ES share ($ and % of total), stand-alone VaR, marginal VaR."""
    cvar, ces = component_var(sc), component_es(sc)
    standalone = pd.Series({t: var_es_simple(sc.assets[t] * abs(sc.weights[t]), sc.confidence)[0]
                            for t in sc.weights.index})
    t = pd.DataFrame({"stock": sc.weights.index, "sector": sectors.reindex(sc.weights.index).values,
                      "weight": sc.weights.values, "var_usd": cvar.values * sc.value, "es_usd": ces.values * sc.value,
                      "var_share": (cvar / cvar.sum()).values, "es_share": (ces / ces.sum()).values,
                      "standalone_usd": standalone.values * sc.value,
                      "marginal": (cvar / sc.weights.replace(0, np.nan)).values})
    return t.sort_values("es_usd", ascending=False).reset_index(drop=True)


def diversification(sc: Scenarios) -> dict[str, float]:
    """Portfolio VaR against the sum of every stock's stand-alone VaR: what mixing them saves."""
    var, es = var_es_simple(sc.portfolio(), sc.confidence)
    alone = sum(var_es_simple(sc.assets[t] * abs(sc.weights[t]), sc.confidence)[0] for t in sc.weights.index)
    return {"var": var * sc.value, "es": es * sc.value, "sum_standalone": alone * sc.value,
            "benefit": (alone - var) * sc.value, "benefit_share": 1 - var / alone if alone else 0.0}


def active_risk(sc: Scenarios, portfolio_returns: pd.Series, benchmark_prices: pd.Series) -> dict[str, float]:
    """Risk of straying from the benchmark: tracking error, VaR of the gap, beta, information ratio."""
    bench = benchmark_prices.pct_change().reindex(portfolio_returns.index)
    gap = (portfolio_returns - bench).dropna().iloc[-len(sc.assets):]
    active_var, active_es = var_es_simple(sc.portfolio() - sc.benchmark, sc.confidence)
    b = bench.reindex(gap.index)
    p = portfolio_returns.reindex(gap.index)
    return {"tracking error": float(gap.std() * np.sqrt(252)), "active VaR": active_var * sc.value,
            "active ES": active_es * sc.value, "beta": float(p.cov(b) / b.var()),
            "information ratio": float(gap.mean() / gap.std() * np.sqrt(252))}
