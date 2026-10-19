"""Tests for Module 6 (backtesting)."""

import numpy as np
import pandas as pd
import pytest

from riskkit.backtest import compare, tests, traffic_light


def test_kupiec_textbook_value():
    """250 days at 99% with 10 exceptions: LR about 12.96, clearly rejected; 2-3 exceptions pass."""
    r = tests.kupiec(10, 250, 0.01)
    assert r.statistic == pytest.approx(12.96, abs=0.05) and not r.passed
    assert tests.kupiec(3, 250, 0.01).passed


def test_christoffersen_spots_clusters():
    """The same 10 exceptions: spread out passes, bunched together fails."""
    spread = np.zeros(1000, dtype=bool)
    spread[::100] = True
    bunched = np.zeros(1000, dtype=bool)
    bunched[500:510] = True
    assert tests.christoffersen_independence(spread).passed
    assert not tests.christoffersen_independence(bunched).passed
    assert tests.transition_counts(bunched)[3] == 9


def test_basel_zone_limits():
    """The binomial rule reproduces the official Basel table: yellow from 5, red from 10."""
    assert traffic_light.zone_limits(250, 0.01) == (5, 10)
    assert traffic_light.zone(4) == "green" and traffic_light.zone(5) == "yellow" and traffic_light.zone(10) == "red"


def test_ranking_prefers_honest_model():
    """A model with the right number of well-spread exceptions ranks above one that is broken in a cluster."""
    idx = pd.bdate_range("2015-01-01", periods=1500)
    actual = pd.Series(0.01, index=idx)
    good_var = pd.Series(0.02, index=idx)
    good_var.iloc[::100] = 0.005           # 15 spread exceptions (expected 15)
    bad_var = pd.Series(0.02, index=idx)
    bad_var.iloc[700:740] = 0.005          # 40 exceptions in a row
    roll = {m: pd.DataFrame({"var": v, "es": v * 1.2, "actual": actual}) for m, v in (("good", good_var), ("bad", bad_var))}
    table = compare.comparison_table(roll, 0.99, 1.0)
    assert table.loc[0, "model"] == "good" and table.loc[0, "passes all"]
    assert compare.exceptions_table(roll["good"], 1.0)["excess"].gt(0).all()
