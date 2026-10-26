"""Portfolio tests using small return series with analytically known results."""

import pandas as pd
import pytest

from riskkit.config import PortfolioSpec, RiskConfig
from riskkit.portfolio import construction, drawdown, weights

DATES = pd.bdate_range("2024-01-31", periods=4)  # Jan 31, Feb 1, Feb 2, Feb 5


def test_cap_weights_redistributes_excess():
    """A 50% cap on (70, 20, 10) moves the extra 20% to the others in proportion (2:1)."""
    w = weights.cap_weights(pd.Series([0.7, 0.2, 0.1], index=list("ABC")), 0.5)
    assert w.tolist() == pytest.approx([0.5, 0.2 + 0.2 * 2 / 3, 0.1 + 0.2 / 3])
    with pytest.raises(ValueError):
        weights.cap_weights(pd.Series([0.5, 0.5]), 0.4)


def test_market_cap_and_inverse_vol():
    """Bigger company -> bigger weight; jumpier stock -> smaller weight."""
    mc = weights.market_cap_weights(pd.Series({"A": 10.0, "B": 10.0}), pd.Series({"A": 3.0, "B": 1.0}))
    assert mc["A"] == pytest.approx(0.75)
    r = pd.DataFrame({"A": [0.01, -0.01] * 5, "B": [0.02, -0.02] * 5})
    assert weights.inverse_vol_weights(r)["A"] == pytest.approx(2 / 3)


def test_market_cap_targets_use_only_dated_share_history():
    """A later buyback must not alter an earlier rebalance weight."""
    idx = pd.to_datetime(["2024-01-02", "2024-02-01"])
    prices = pd.DataFrame({"A": [10.0, 10.0], "B": [10.0, 10.0]}, index=idx)
    returns = prices.pct_change(fill_method=None).fillna(0.0)
    shares = pd.DataFrame({"A": [3.0, 1.0], "B": [1.0, 1.0]}, index=idx)
    cfg = RiskConfig(tickers=("A", "B"), portfolio=PortfolioSpec(scheme="market_cap"))
    out = weights.target_weights(cfg, prices, returns, shares, idx)
    assert out.loc[idx[0], "A"] == pytest.approx(0.75)
    assert out.loc[idx[1], "A"] == pytest.approx(0.50)


def test_rebalance_dates_skip_unfinished_period():
    """Month ends only; the running month (February here) is not a rebalance yet."""
    idx = pd.bdate_range("2024-01-01", "2024-02-15")
    assert list(weights.rebalance_dates(idx, "monthly")) == [pd.Timestamp("2024-01-31")]
    assert len(weights.rebalance_dates(idx, "none")) == 0


def test_buy_and_hold_by_hand():
    """$1 split 50/50; A +10% then +10%, B flat: value 1.05 then 1.105, weights drift to A."""
    r = pd.DataFrame({"A": [0.10, 0.10], "B": [0.0, 0.0]}, index=DATES[1:3])
    targets = pd.DataFrame([[0.5, 0.5]], index=[DATES[0]], columns=["A", "B"])
    sim = construction.simulate(r, targets, 0.0, DATES[0])
    assert sim["value"].tolist() == pytest.approx([1.0, 1.05, 1.105])
    assert sim["weights"].iloc[-1]["A"] == pytest.approx(0.605 / 1.105)


def test_rebalance_with_costs():
    """Rebalancing back to 50/50 trades 5% of value; at 100bp the cost is 0.05% of value."""
    r = pd.DataFrame({"A": [0.10, 0.0], "B": [-0.10, 0.0]}, index=DATES[1:3])
    targets = pd.DataFrame([[0.5, 0.5], [0.5, 0.5]], index=[DATES[0], DATES[1]], columns=["A", "B"])
    sim = construction.simulate(r, targets, 100.0, DATES[0])
    assert sim["turnover"].iloc[0] == pytest.approx(0.10)
    assert sim["costs"].iloc[0] == pytest.approx(0.10 * 1.0 * 0.01)
    assert sim["weights"].iloc[1].tolist() == pytest.approx([0.5, 0.5])


def test_short_position_gains_when_stock_falls():
    """150% long A, -50% short B; B falls 10%: the short makes +5%."""
    r = pd.DataFrame({"A": [0.0], "B": [-0.10]}, index=DATES[1:2])
    targets = pd.DataFrame([[1.5, -0.5]], index=[DATES[0]], columns=["A", "B"])
    sim = construction.simulate(r, targets, 0.0, DATES[0])
    assert sim["value"].iloc[-1] == pytest.approx(1.05)


def test_drawdown_numbers():
    """100 -> 120 -> 90 -> 130: worst fall is 90/120 - 1 = -25%, recovered on the last day."""
    v = pd.Series([100.0, 120, 90, 130], index=DATES)
    assert drawdown.max_drawdown(v) == pytest.approx(-0.25)
    ep = drawdown.drawdown_episodes(v)
    assert ep.loc[0, "peak"] == DATES[1] and ep.loc[0, "recovery"] == DATES[3]


def test_short_weights_need_the_switch():
    """Negative custom weights are refused unless long-short is switched on."""
    with pytest.raises(ValueError, match="short"):
        RiskConfig(tickers=("A", "B"), weights=(1.2, -0.2))
    RiskConfig(tickers=("A", "B"), weights=(1.2, -0.2), portfolio=PortfolioSpec(allow_short=True))
