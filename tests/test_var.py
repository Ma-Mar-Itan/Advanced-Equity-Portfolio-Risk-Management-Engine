"""Tests for Module 5 (VaR and ES)."""

import numpy as np
import pandas as pd
import pytest

from riskkit.config import RiskConfig, VarSpec
from riskkit.var import engine, historical, models


def returns(n=900, seed=3):
    """Calm returns with one stormy stretch near the end."""
    rng = np.random.default_rng(seed)
    r = rng.standard_normal(n) * 0.01
    r[-100:] *= 3
    return pd.Series(r, index=pd.bdate_range("2020-01-01", periods=n))


def test_tail_size_rule():
    """500 scenarios at 99% -> 5 in the tail; tiny samples still keep one."""
    assert historical.tail_size(500, 0.99) == 5 and historical.tail_size(250, 0.99) == 3
    assert historical.tail_size(10, 0.99) == 1


def test_var_es_by_hand():
    """100 scenarios at 95%: the 5 worst losses are 10..6%: VaR = 6%, ES = 8%."""
    simple = np.array([-0.10, -0.09, -0.08, -0.07, -0.06] + [0.01] * 95)
    var, es = historical.var_es(np.log1p(simple), 0.95)
    assert var == pytest.approx(0.06) and es == pytest.approx(0.08)


def test_scaling_to_today():
    """A -1% day from a period half as volatile as today becomes -2%."""
    out = models.scaled_scenarios(np.array([-0.01]), np.array([0.005]), 0.01)
    assert out[0] == pytest.approx(-0.02)


def test_scaled_var_reacts_to_storm_plain_hs_less():
    """After a stormy stretch, EWMA-scaled VaR jumps more than plain HS (which still averages calm days in)."""
    cfg = RiskConfig(window=500)
    r = returns()
    hs = engine.today_var(r, cfg, "HS").var_1d
    ewma = engine.today_var(r, cfg, "EWMA-HS").var_1d
    assert ewma > hs


def test_rolling_var_has_no_look_ahead():
    """Changing a return on day t must not change the VaR forecast for day t (only later ones)."""
    cfg = RiskConfig(window=250, var=VarSpec(refit_every=100))
    r = returns(800)
    shocked = r.copy()
    shocked.iloc[700] = -0.25
    for model in ("HS", "EWMA-HS", "GJR-HS"):
        a, b = engine.rolling_var(r, cfg, model), engine.rolling_var(shocked, cfg, model)
        d = r.index[700]
        assert a.loc[:d, "var"].equals(b.loc[:d, "var"])
        assert b.loc[r.index[701], "var"] >= a.loc[r.index[701], "var"]


def test_horizon_and_confidence_ordering():
    """sqrt rule gives 1-day x sqrt(10); more confidence -> bigger VaR; ES >= VaR."""
    cfg = RiskConfig(window=500)
    res = engine.today_var(returns(), cfg, "HS")
    assert res.var_h == pytest.approx(res.var_1d * np.sqrt(10)) and res.es_1d >= res.var_1d
    v95, v99 = (engine.today_var(returns(), cfg, "HS", c).var_1d for c in (0.95, 0.99))
    assert v99 > v95


def test_overlapping_horizon_runs():
    """Real 10-day stretches give a positive 10-day VaR bigger than the 1-day one."""
    cfg = RiskConfig(window=500, var=VarSpec(horizon_method="overlapping"))
    res = engine.today_var(returns(), cfg, "HS")
    assert res.var_h > res.var_1d > 0
