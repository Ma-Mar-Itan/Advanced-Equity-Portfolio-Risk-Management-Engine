"""Optimizer: the split of money with the lowest risk, with a cap per stock.

- Lowest Expected Shortfall: a linear programme (Rockafellar & Uryasev, 2000) over the scenarios:
    minimise  a + 1 / (p N) x sum(u_j)
    such that u_j >= -(scenario_j . w) - a,  u_j >= 0,  sum(w) = 1,  0 <= w_i <= cap
  At the optimum, a is the VaR and the objective is the ES.
- Lowest volatility: the classic minimum-variance split (same constraints).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize

from riskkit.attribution.scenarios import Scenarios, var_es_simple


def min_es_weights(sc: Scenarios, cap: float = 1.0) -> pd.Series:
    """Long-only weights (each at most `cap`) that minimise Expected Shortfall over the scenarios."""
    R = sc.assets[sc.weights.index].to_numpy()
    n_scen, n = R.shape
    p = 1 - sc.confidence
    # variables: w (n), a (1), u (n_scen)
    c = np.concatenate([np.zeros(n), [1.0], np.full(n_scen, 1 / (p * n_scen))])
    a_ub = np.hstack([-R, -np.ones((n_scen, 1)), -np.eye(n_scen)])           # -R w - a - u <= 0
    b_ub = np.zeros(n_scen)
    a_eq = np.concatenate([np.ones(n), [0.0], np.zeros(n_scen)])[None, :]
    bounds = [(0, cap)] * n + [(None, None)] + [(0, None)] * n_scen
    res = linprog(c, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=[1.0], bounds=bounds, method="highs")
    if not res.success:
        raise ValueError(f"The optimizer found no answer ({res.message}). Try a looser cap.")
    return pd.Series(res.x[:n], index=sc.weights.index).clip(lower=0)


def min_vol_weights(sc: Scenarios, cap: float = 1.0) -> pd.Series:
    """Long-only weights (each at most `cap`) with the lowest scenario volatility."""
    cov = sc.assets[sc.weights.index].cov().to_numpy() * 1e4      # scaled up so the solver sees the differences
    n = len(cov)
    res = minimize(lambda w: w @ cov @ w, np.full(n, 1 / n), method="SLSQP", bounds=[(0, cap)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"ftol": 1e-12, "maxiter": 500})
    return pd.Series(res.x, index=sc.weights.index).clip(lower=0)


def compare_splits(sc: Scenarios, new: pd.Series, history: pd.DataFrame) -> pd.DataFrame:
    """Risk and past return of today's split against the new one."""
    rows = []
    for name, w in (("Today's split", sc.weights), ("Optimized split", new / new.sum())):
        var, es = var_es_simple(sc.portfolio(w), sc.confidence)
        past = history[w.index] @ w
        rows.append({"split": name, "VaR": var * sc.value, "ES": es * sc.value,
                     "volatility": float(past.std() * np.sqrt(252)), "return": float(past.mean() * 252),
                     "largest weight": float(w.max())})
    return pd.DataFrame(rows)
