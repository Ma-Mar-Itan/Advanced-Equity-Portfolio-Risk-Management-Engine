"""Tests for historical and hypothetical stress scenarios."""

import numpy as np
import pandas as pd
import pytest

from app.charts.stress import loss_chart
from riskkit.stress import historical, hypothetical
from riskkit.stress.scenarios import HistoricalScenario

IDX = pd.bdate_range("2019-12-02", periods=40)


def test_market_shock_uses_beta():
    """Market -10%: a beta-2 stock at 50% weight loses 10% of the portfolio, a beta-0 stock nothing."""
    loss = hypothetical.market_shock(pd.Series({"A": 0.5, "B": 0.5}), pd.Series({"A": 2.0, "B": 0.0}), -0.10)
    assert loss["A"] == pytest.approx(0.10) and loss["B"] == 0 and loss.sum() == pytest.approx(0.10)


def test_sector_shock_with_spillover():
    """Tech -20% hits only tech without spillover; with 50% spillover others move half their beta share."""
    w, beta = pd.Series({"T": 0.5, "E": 0.5}), pd.Series({"T": 1.0, "E": 1.0})
    sec = pd.Series({"T": "Technology", "E": "Energy"})
    assert hypothetical.sector_shock(w, beta, sec, "Technology", -0.2).tolist() == pytest.approx([0.10, 0.0])
    assert hypothetical.sector_shock(w, beta, sec, "Technology", -0.2, 0.5)["E"] == pytest.approx(0.05)


def test_correlation_spike_raises_risk():
    """Two uncorrelated stocks: pushing correlation to 1 raises portfolio volatility by sqrt(2)."""
    rng = np.random.default_rng(0)
    r = pd.DataFrame(rng.standard_normal((5000, 2)) * 0.01, columns=["A", "B"])
    ratio = hypothetical.correlation_shock_ratio(r, pd.Series({"A": 0.5, "B": 0.5}), 1.0)
    assert ratio == pytest.approx(np.sqrt(2), rel=0.03)


def test_replay_and_stand_in():
    """B did not exist: it gets beta x the benchmark. A falls 10% once: portfolio path and loss add up."""
    a = pd.Series(0.0, index=IDX)
    a.iloc[5] = -0.10
    assets = pd.DataFrame({"A": a, "B": np.nan})
    bench = pd.Series(0.0, index=IDX)
    bench.iloc[6] = -0.05
    sc = HistoricalScenario("test", str(IDX[0].date()), str(IDX[-1].date()), "")
    rep = historical.replay(sc, pd.Series({"A": 0.5, "B": 0.5}), assets, bench, pd.Series({"A": 1.0, "B": 2.0}))
    assert rep.proxied == ["B"]
    assert rep.loss == pytest.approx(1 - (0.5 * 0.9 + 0.5 * 0.9))
    assert rep.by_stock.sum() == pytest.approx(rep.loss)


def test_volatility_shock_doubles_var():
    """Doubling every replayed day roughly doubles VaR."""
    rng = np.random.default_rng(1)
    scen = rng.standard_normal(1000) * 0.01
    base = hypothetical.volatility_shock(scen, 1.0, 0.99)[0]
    assert hypothetical.volatility_shock(scen, 2.0, 0.99)[0] == pytest.approx(2 * base, rel=0.03)


def test_loss_chart_legend_explains_both_scenario_colours():
    table = pd.DataFrame(
        {
            "scenario": ["Crisis", "Market -10%"],
            "kind": ["Historical", "Hypothetical"],
            "loss_usd": [2_000_000.0, 1_000_000.0],
        }
    )

    figure = loss_chart(table)

    legend_traces = [trace for trace in figure.data if trace.showlegend is not False]
    assert [trace.name for trace in legend_traces] == ["Historical crisis replay", "Hypothetical shock"]
