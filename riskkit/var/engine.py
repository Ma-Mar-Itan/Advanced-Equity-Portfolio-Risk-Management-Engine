"""Current and rolling Value at Risk and Expected Shortfall calculations.

Inputs are daily portfolio log returns. Dollar values use the portfolio value
stored in the active configuration.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from riskkit.config import VAR_MODELS, RiskConfig
from riskkit.var.historical import var_es
from riskkit.var.models import MIN_TRAIN, scaled_scenarios, sigma_rolling, sigma_today


@dataclass(frozen=True)
class VarResult:
    """Today's risk numbers for one model. var/es are positive loss fractions; *_usd in dollars."""

    model: str
    confidence: float
    window: int
    horizon: int
    var_1d: float
    es_1d: float
    var_h: float
    es_h: float
    scenarios: np.ndarray  # the 1-day scenario log returns behind the numbers
    value: float

    @property
    def var_1d_usd(self) -> float:
        """1-day VaR in dollars."""
        return self.var_1d * self.value

    @property
    def es_1d_usd(self) -> float:
        """1-day ES in dollars."""
        return self.es_1d * self.value

    @property
    def var_h_usd(self) -> float:
        """Multi-day VaR in dollars."""
        return self.var_h * self.value

    @property
    def es_h_usd(self) -> float:
        """Multi-day ES in dollars."""
        return self.es_h * self.value


def today_scenarios(log_returns: pd.Series, model: str, cfg: RiskConfig, window: int) -> np.ndarray:
    """Tomorrow's possible returns: the last `window` days, rescaled to tomorrow's volatility if the model scales."""
    r = log_returns.to_numpy()
    sigma = sigma_today(r, model, cfg)
    last = r[-window:]
    return last if sigma is None else scaled_scenarios(last, sigma[-window - 1 : -1], sigma[-1])


def horizon_var_es(
    log_returns: pd.Series, scenarios: np.ndarray, model: str, cfg: RiskConfig, window: int, confidence: float
) -> tuple[float, float]:
    """Multi-day VaR/ES.

    sqrt:        1-day numbers x sqrt(horizon) (assumes days are independent; the Basel shortcut)
    overlapping: real h-day stretches inside the window (scaled models: summed rescaled days)
    """
    h = cfg.var.horizon
    if cfg.var.horizon_method == "sqrt":
        one = var_es(scenarios, confidence)
        return one[0] * np.sqrt(h), one[1] * np.sqrt(h)
    sums = pd.Series(scenarios).rolling(h).sum().dropna().to_numpy()
    return var_es(sums, confidence)


def today_var(
    log_returns: pd.Series,
    cfg: RiskConfig,
    model: str | None = None,
    confidence: float | None = None,
    window: int | None = None,
) -> VarResult:
    """Today's 1-day and multi-day VaR and ES for one model (defaults from the config)."""
    model, confidence, window = model or cfg.var.model, confidence or cfg.confidence, window or cfg.window
    if len(log_returns) < window:
        raise ValueError(f"Only {len(log_returns)} days of returns: the {window}-day window needs more.")
    scen = today_scenarios(log_returns, model, cfg, window)
    v1, e1 = var_es(scen, confidence)
    vh, eh = horizon_var_es(log_returns, scen, model, cfg, window, confidence)
    return VarResult(model, confidence, window, cfg.var.horizon, v1, e1, vh, eh, scen, cfg.portfolio_value)


def all_models_today(log_returns: pd.Series, cfg: RiskConfig) -> list[VarResult]:
    """Today's numbers for all four models at the config's confidence and window."""
    return [today_var(log_returns, cfg, m) for m in VAR_MODELS]


def rolling_var(
    log_returns: pd.Series,
    cfg: RiskConfig,
    model: str | None = None,
    confidence: float | None = None,
    window: int | None = None,
) -> pd.DataFrame:
    """1-day VaR and ES forecast for every past day, using only data before that day.

    Columns: var, es (loss fractions), actual (the loss that then happened). The first forecast
    is made once `window` days (and, for GARCH models, MIN_TRAIN days) of history exist.
    """
    model, confidence, window = model or cfg.var.model, confidence or cfg.confidence, window or cfg.window
    r = log_returns.to_numpy()
    first = max(window, MIN_TRAIN if model in ("GARCH-HS", "GJR-HS") else window)
    blocks = sigma_rolling(r, model, cfg, first) if model != "HS" else {}
    starts = sorted(blocks)
    out = np.full((len(r), 2), np.nan)
    for t in range(first, len(r)):
        past = r[t - window : t]
        if blocks:
            sigma = blocks[max(s for s in starts if s <= t)]
            past = scaled_scenarios(past, sigma[t - window : t], sigma[t])
        out[t] = var_es(past, confidence)
    df = pd.DataFrame(out, index=log_returns.index, columns=["var", "es"])
    df["actual"] = -np.expm1(r)
    return df.dropna()


def confidence_window_grid(
    log_returns: pd.Series, cfg: RiskConfig, model: str, confidences=(0.95, 0.99, 0.995), windows=(250, 500, 750)
) -> pd.DataFrame:
    """Return current one-day VaR for each confidence and estimation-window pair."""
    rows = {
        f"{c:.1%}": {
            f"{w} days": today_var(log_returns, cfg, model, c, w).var_1d for w in windows if len(log_returns) >= w
        }
        for c in confidences
    }
    return pd.DataFrame(rows).T
