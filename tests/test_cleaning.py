"""Tests for Module 2 (cleaning and returns) on a tiny made-up price table."""

import numpy as np
import pandas as pd
import pytest

from riskkit.config import CleaningSpec
from riskkit.data import cleaning, returns, transforms, validation

DATES = pd.bdate_range("2024-01-01", periods=8)


def prices():
    """Two stocks: A has a 1-day hole, B is stuck at 50 for a while and starts late."""
    a = [100, 101, np.nan, 103, 104, 105, 106, 107]
    b = [np.nan, 50, 50, 50, 50, 50, 51, 52]
    return pd.DataFrame({"A": a, "B": b}, index=DATES, dtype=float)


def test_ffill_fills_holes_and_drops_days_before_listing():
    """A's hole is filled with 101; the day before B existed is dropped."""
    out, log = cleaning.fill_missing(prices(), "ffill", limit=5)
    assert out.loc[DATES[2], "A"] == 101 and DATES[0] not in out.index
    assert (log["step"] == "fill").any()


def test_interpolate_draws_a_straight_line():
    """Between 101 and 103 the missing day becomes 102."""
    out, _ = cleaning.fill_missing(prices(), "interpolate", limit=5)
    assert out.loc[DATES[2], "A"] == pytest.approx(102)


def test_drop_method_removes_incomplete_days():
    """With 'drop', any day with a missing price disappears."""
    out, _ = cleaning.fill_missing(prices(), "drop", limit=5)
    assert DATES[2] not in out.index and out.notna().all().all()


def test_stale_prices_found_after_threshold():
    """B is unchanged for 4 days in a row; with a 3-day limit the 4th unchanged day is stale."""
    stale = cleaning.find_stale(prices(), 3)
    assert stale["B"].sum() == 1 and not stale["A"].any()
    assert not cleaning.find_stale(prices(), 0).any().any()


def test_common_calendar_keeps_only_complete_days():
    """'common' keeps only days on which every stock has a price."""
    out, _ = cleaning.align_calendar(prices(), "common", prices()["A"])
    assert out.notna().all().all()


def test_log_and_simple_returns():
    """100 -> 110 is +10% simple and ln(1.1) log; the first day has no return."""
    p = pd.DataFrame({"A": [100.0, 110.0]})
    assert returns.simple_returns(p)["A"].iloc[0] == pytest.approx(0.10)
    assert returns.log_returns(p)["A"].iloc[0] == pytest.approx(np.log(1.1))


def test_winsorize_cap_clips_and_logs():
    """A 40% day is clipped to the 25% cap and recorded in the log."""
    r = pd.DataFrame({"A": [0.01, 0.40, -0.02]}, index=DATES[:3])
    out, log = transforms.winsorize(r, "cap", cap=0.25)
    assert out["A"].max() == 0.25 and len(log) == 1


def test_custom_expression_and_safety():
    """A formula works on r; anything sneaky is refused."""
    r = pd.DataFrame({"A": [0.01, 0.03], "B": [0.02, 0.04]})
    out = transforms.apply_custom_expression(r, "r - mean(r)")
    assert out["A"].tolist() == pytest.approx([-0.01, 0.01])
    with pytest.raises(ValueError):
        transforms.apply_custom_expression(r, "().__class__")
    with pytest.raises(ValueError):
        transforms.apply_custom_expression(r, "1 + 1")


def test_alignment_check_catches_a_shifted_series():
    """Shifting returns by one day (look-ahead) fails the alignment check."""
    p = prices().ffill().dropna()
    raw = returns.log_returns(p)
    assert validation.check_aligned(p, raw, "log").passed
    assert not validation.check_aligned(p, raw.shift(-1), "log").passed


def test_cleaning_spec_rejects_unknown_options():
    """Typos in option names fail early."""
    with pytest.raises(ValueError):
        CleaningSpec(fill_method="magic")


def test_pipeline_logs_formula_changes(tmp_path):
    """Changes made by the custom formula show up in the log and the 'changed' count."""
    from datetime import date

    from riskkit.config import RiskConfig
    from riskkit.data.collect import MarketData
    from riskkit.data.pipeline import clean_market_data

    idx = pd.bdate_range("2024-01-01", periods=6)
    px = pd.DataFrame({"A": [100, 120, 100, 101, 102, 103.0], "B": [50, 51, 52, 53, 54, 55.0]}, index=idx)
    md = MarketData(px, px["A"], pd.Series(0.0, index=idx), {}, {}, ())
    cfg = RiskConfig(tickers=("A", "B"), start=date(2024, 1, 1),
                     cleaning=CleaningSpec(custom_expression="clip(r, -0.1, 0.1)"))
    cd = clean_market_data(md, cfg)
    assert cd.count("formula") == 2 and cd.changed_returns() == 2 and all(c.passed for c in cd.checks)
