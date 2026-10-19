"""GARCH(1,1) and GJR-GARCH(1,1): volatility that reacts to shocks AND drifts back to normal.

GARCH:      variance_t = omega + alpha * shock_{t-1}^2 + beta * variance_{t-1}
GJR-GARCH:  adds gamma * shock_{t-1}^2 on DOWN days only (the leverage effect:
            bad news raises future volatility more than good news of the same size).

- alpha: how strongly yesterday's surprise moves today's volatility
- beta:  how much of yesterday's volatility carries over (memory)
- persistence = alpha + gamma/2 + beta: close to 1 means storms last long
- long-run volatility: the level volatility drifts back to

Fitted with the `arch` package on returns in percent (it is numerically happier there).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.volatility.base import TRADING_DAYS, VolFit

SCALE = 100.0   # arch works on percent returns


class GarchVol:
    """GARCH(1,1) when asymmetric=False, GJR-GARCH(1,1) when asymmetric=True."""

    def __init__(self, asymmetric: bool = False, dist: str = "normal", mean: str = "zero") -> None:
        self.asymmetric, self.dist, self.mean = asymmetric, dist, mean
        self.name = "GJR-GARCH" if asymmetric else "GARCH"

    def fit(self, returns: pd.Series, horizon: int = 10) -> VolFit:
        """Estimate the parameters on all returns given, then filter sigma and forecast ahead."""
        from arch import arch_model

        model = arch_model(returns * SCALE, mean="Zero" if self.mean == "zero" else "Constant",
                           vol="GARCH", p=1, o=1 if self.asymmetric else 0, q=1,
                           dist="t" if self.dist == "t" else "normal", rescale=False)
        res = model.fit(disp="off", show_warning=False)
        sigma = res.conditional_volatility / SCALE
        variance_path = res.forecast(horizon=horizon, reindex=False).variance.to_numpy()[-1]
        return VolFit(self.name, sigma, np.sqrt(variance_path) / SCALE, garch_params(res.params, res))


def garch_params(p: pd.Series, res) -> dict[str, float]:
    """The fitted numbers in plain names, plus persistence, long-run volatility and half-life."""
    omega, alpha, beta = p["omega"], p["alpha[1]"], p["beta[1]"]
    gamma = p.get("gamma[1]", 0.0)
    persistence = alpha + gamma / 2 + beta
    out = {"omega": omega / SCALE**2, "alpha": alpha, "gamma": gamma, "beta": beta, "persistence": persistence}
    if persistence < 1:
        out["long-run vol (yearly)"] = float(np.sqrt(omega / (1 - persistence)) / SCALE * np.sqrt(TRADING_DAYS))
        out["half-life (days)"] = float(np.log(0.5) / np.log(persistence))
    if "nu" in p:
        out["t degrees of freedom"] = p["nu"]
    if "mu" in p:
        out["mean daily return"] = p["mu"] / SCALE
    out["log-likelihood"], out["AIC"] = float(res.loglikelihood), float(res.aic)
    return {k: float(v) for k, v in out.items()}


def news_impact(params: dict[str, float], shocks: np.ndarray) -> np.ndarray:
    """Tomorrow's volatility (daily) after a day with return `shock`, starting from the long-run level.

    For GARCH the curve is symmetric; for GJR down days push volatility up more (the leverage effect).
    """
    p = params
    persistence = p["alpha"] + p["gamma"] / 2 + p["beta"]
    long_run_var = p["omega"] / (1 - persistence) if persistence < 1 else p["omega"]
    var = p["omega"] + (p["alpha"] + p["gamma"] * (shocks < 0)) * shocks**2 + p["beta"] * long_run_var
    return np.sqrt(var)


def garch_filter(returns: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Run fitted GARCH / GJR parameters over returns: volatility for each day, plus one for tomorrow.

    Output has len(returns) + 1 values; value t uses returns before t only. Used by rolling VaR,
    which refits the parameters every few weeks and filters forward with them in between.
    """
    mu = params.get("mean daily return", 0.0)
    omega, alpha, beta, gamma = params["omega"], params["alpha"], params["beta"], params.get("gamma", 0.0)
    persistence = alpha + gamma / 2 + beta
    shocks = returns - mu
    var = np.empty(len(returns) + 1)
    var[0] = omega / (1 - persistence) if persistence < 1 else np.var(shocks)
    for t, e in enumerate(shocks):
        var[t + 1] = omega + (alpha + gamma * (e < 0)) * e * e + beta * var[t]
    return np.sqrt(var)
