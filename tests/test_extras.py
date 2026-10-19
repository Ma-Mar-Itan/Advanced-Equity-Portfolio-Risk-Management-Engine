"""Tests for Module 8 (risk attribution and decision tools)."""

import numpy as np
import pandas as pd
import pytest

from riskkit.attribution import euler
from riskkit.attribution.scenarios import Scenarios, var_es_simple
from riskkit.decisions import hedge, optimize, whatif


def scenarios(n=1000, seed=4):
    """Three stocks: A risky, B calm, C moves against A. Equal weights, $1M."""
    rng = np.random.default_rng(seed)
    a = rng.standard_normal(n) * 0.03
    b = rng.standard_normal(n) * 0.005
    c = -0.5 * a + rng.standard_normal(n) * 0.01
    assets = pd.DataFrame({"A": a, "B": b, "C": c})
    bench = pd.Series(a * 0.8 + rng.standard_normal(n) * 0.002)
    return Scenarios(assets, bench, pd.Series(1 / 3, index=list("ABC")), 1e6, 0.99)


def test_shares_add_up_to_the_total():
    """ES and VaR shares add up to the portfolio ES and VaR; the risky stock carries most."""
    sc = scenarios()
    var, es = var_es_simple(sc.portfolio(), 0.99)
    assert euler.component_es(sc).sum() == pytest.approx(es)
    assert euler.component_var(sc).sum() == pytest.approx(var)
    assert euler.component_es(sc).idxmax() == "A"


def test_diversification_saves_risk():
    """The basket's VaR is below the sum of the stand-alone VaRs."""
    d = euler.diversification(scenarios())
    assert d["var"] < d["sum_standalone"] and d["benefit"] > 0


def test_whatif_pro_rata_keeps_value_and_cash_grows_it():
    """Pro-rata funding keeps the value; cash funding adds the trade amount; weights still sum to 1."""
    w = pd.Series({"A": 0.5, "B": 0.5})
    w2, v2 = whatif.trade_weights(w.copy(), 100.0, "A", 10.0, "pro_rata")
    assert v2 == 100 and w2["A"] == pytest.approx(0.6) and w2.sum() == pytest.approx(1)
    w3, v3 = whatif.trade_weights(w.copy(), 100.0, "A", 10.0, "cash")
    assert v3 == 110 and w3["A"] == pytest.approx(60 / 110)


def test_best_hedge_is_short_the_risky_stock():
    """The best hedge shorts something that moves with the risk, and cuts VaR."""
    h = hedge.best_hedges(scenarios(), "BENCH")
    assert h.loc[0, "size"] < 0 and h.loc[0, "reduction"] > 0.2


def test_optimizers_lower_risk_and_respect_cap():
    """Both optimizers cut risk versus equal weights; weights are within the cap and sum to 1."""
    sc = scenarios()
    for w in (optimize.min_es_weights(sc, 0.6), optimize.min_vol_weights(sc, 0.6)):
        assert w.sum() == pytest.approx(1, abs=1e-6) and w.max() <= 0.6 + 1e-6
        assert var_es_simple(sc.portfolio(w), 0.99)[1] < var_es_simple(sc.portfolio(), 0.99)[1]
