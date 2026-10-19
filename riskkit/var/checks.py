"""The brief's VaR validation checks, each pass/fail with a plain reason."""

from __future__ import annotations

import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.validation import Check
from riskkit.var.engine import VarResult, today_var
from riskkit.volatility.analysis import volatility_regimes
from riskkit.volatility.ewma import EWMAVol


def var_checks(log_returns: pd.Series, cfg: RiskConfig, results: list[VarResult], rolling: pd.DataFrame) -> list[Check]:
    """VaR > 0, more confidence -> bigger VaR, 10-day > 1-day, ES >= VaR, VaR higher in stormy times."""
    model = cfg.var.model
    levels = [today_var(log_returns, cfg, model, c).var_1d for c in (0.95, 0.99, 0.995)]
    stormy = volatility_regimes(EWMAVol(cfg.volatility.ewma_lambda).fit(log_returns).sigma)
    by_regime = rolling["var"].groupby(stormy.reindex(rolling.index)).mean()
    return [
        Check("VaR is a positive loss", all(r.var_1d > 0 for r in results), "all models"),
        Check("Higher confidence gives larger VaR", levels[0] < levels[1] < levels[2],
              " < ".join(f"{v:.2%}" for v in levels) + f" ({model})"),
        Check(f"{cfg.var.horizon}-day VaR > 1-day VaR", all(r.var_h > r.var_1d for r in results), "all models"),
        Check("ES ≥ VaR", all(r.es_1d >= r.var_1d for r in results), "all models"),
        Check("VaR rises when volatility is high", by_regime.get("Stormy", 0) > by_regime.get("Calm", 0),
              f"average VaR {by_regime.get('Calm', float('nan')):.2%} calm vs {by_regime.get('Stormy', float('nan')):.2%} stormy"),
    ]
