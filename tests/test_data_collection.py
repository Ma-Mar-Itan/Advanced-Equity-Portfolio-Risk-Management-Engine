"""Offline tests for market-data collection and source fallbacks."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from riskkit.config import RiskConfig
from riskkit.data import cache, collect, fx, search
from riskkit.data.sources import DASHBOARD_SOURCES, SOURCES, dashboard_source_names
from riskkit.data.sources.base import DataUnavailableError, standardize


class FakeSource:
    """A pretend price source: prices rise by 1 a day from 100, or fail for chosen tickers."""

    def __init__(self, name="fake", fail=()):
        self.name, self.fail, self.calls = name, set(fail), 0

    def fetch_prices(self, ticker, start, end):
        """Return a deterministic ten-day fixture or raise the configured failure."""
        self.calls += 1
        if ticker in self.fail:
            raise DataUnavailableError(ticker)
        idx = pd.bdate_range("2024-01-01", periods=10)
        px = 100 + np.arange(10.0)
        return standardize(pd.DataFrame({"close": px, "adj_close": px, "volume": 1e6}, index=idx), ticker)

    def currency(self, ticker):
        """Everything fake is in dollars."""
        return "USD"


def test_config_rejects_weights_not_summing_to_one():
    """The brief's check 'weights sum to 100%' is enforced when the config is made."""
    with pytest.raises(ValueError, match="100%"):
        RiskConfig(tickers=("A", "B"), weights=(0.5, 0.4))


def test_config_equal_weights_by_default():
    """No weights given means every stock gets the same share."""
    cfg = RiskConfig(tickers=("A", "B", "C", "D"))
    assert cfg.weight_of("C") == pytest.approx(0.25)


def test_standardize_strips_time_zone_and_duplicates():
    """Sources return messy tables; standardize makes them uniform."""
    idx = pd.to_datetime(["2024-01-02 05:00", "2024-01-02 05:00", "2024-01-03 05:00"]).tz_localize("UTC")
    raw = pd.DataFrame({"close": [1.0, 2.0, 3.0], "volume": [1, 1, 1]}, index=idx)
    out = standardize(raw, "X")
    assert list(out.columns) == ["close", "adj_close", "volume"]
    assert out.index.tz is None and len(out) == 2


def test_cache_is_used_on_second_call(tmp_path):
    """The second request for the same ticker on the same day never reaches the source."""
    src = FakeSource()
    cache.load_prices("AAA", [src], tmp_path)
    df, where = cache.load_prices("AAA", [src], tmp_path)
    assert src.calls == 1 and where == "fake (saved)" and len(df) == 10


def test_stale_cache_is_used_until_refresh_is_requested(tmp_path):
    """Ordinary startup is cache-first; only an explicit refresh reaches the network."""
    src = FakeSource()
    cache.load_prices("AAA", [src], tmp_path)
    path = cache.cache_path(tmp_path, "fake", "AAA")
    old = pd.Timestamp("2020-01-01").timestamp()
    import os

    os.utime(path, (old, old))
    _, where = cache.load_prices("AAA", [src], tmp_path)
    assert src.calls == 1 and "refresh available" in where
    cache.load_prices("AAA", [src], tmp_path, refresh=True)
    assert src.calls == 2


def test_fallback_source_used_when_primary_fails(tmp_path):
    """If the first shop is closed, the second one is tried."""
    primary, backup = FakeSource("p", fail={"AAA"}), FakeSource("b")
    _, where = cache.load_prices("AAA", [primary, backup], tmp_path)
    assert where == "b"


def test_missing_everywhere_raises(tmp_path):
    """No source and no saved file: a clear error, not silent empty data."""
    with pytest.raises(DataUnavailableError):
        cache.load_prices("AAA", [FakeSource(fail={"AAA"})], tmp_path)


def test_fx_conversion_and_pence():
    """100 pence at 1.25 dollars per pound is 1.25 dollars."""
    idx = pd.bdate_range("2024-01-01", periods=3)
    pence = pd.Series([100.0, 100.0, 100.0], index=idx)
    rate = pd.Series([1.25, 1.25], index=idx[:2])  # last day missing: carried forward
    major, divisor = fx.major_currency("GBp")
    out = fx.convert_prices(pence, rate, divisor)
    assert major == "GBP" and list(out) == [1.25, 1.25, 1.25]
    assert fx.fx_ticker("EUR") == "EURUSD=X" and not fx.needs_conversion("USD")


def test_search_keeps_only_tradeable_types():
    """News items and odd types from Yahoo's search are dropped."""
    hits = [
        {"symbol": "NESN.SW", "shortname": "Nestle", "exchDisp": "Swiss", "quoteType": "EQUITY"},
        {"symbol": "XYZ", "quoteType": "OPTION"},
    ]
    table = search.quotes_to_table(hits)
    assert table["symbol"].tolist() == ["NESN.SW"]


def test_brief_price_sources_are_registered():
    """The source selector exposes the supported public and keyed adapters."""
    assert {"yahoo", "stooq", "tiingo", "alpha_vantage", "polygon"} <= set(SOURCES)


def test_requested_dashboard_sources_are_exposed():
    """All requested providers are selectable; WRDS stays conditional."""
    assert DASHBOARD_SOURCES == ("yahoo", "stooq", "alpha_vantage", "polygon")
    assert dashboard_source_names() == DASHBOARD_SOURCES


@pytest.mark.parametrize("provider", ["stooq", "alpha_vantage", "polygon"])
def test_provider_uses_saved_yahoo_as_public_fallback(tmp_path, provider):
    """Unavailable providers load public saved data with honest provenance."""
    yahoo = FakeSource("yahoo")
    cache.load_prices("SPY", [yahoo], tmp_path)
    primary = FakeSource(provider, fail={"SPY"})
    frame, where = cache.load_prices("SPY", [primary, yahoo], tmp_path)
    assert primary.calls == 0
    assert len(frame) == 10
    assert where == "yahoo (saved)"


@pytest.mark.parametrize("provider", ["stooq", "alpha_vantage", "polygon"])
def test_source_chain_always_ends_with_public_yahoo_fallback(provider):
    """Changing the dashboard provider never strands the shipped public cache."""
    cfg = RiskConfig(source=provider, fallback_source=None)
    assert [source.name for source in collect.build_sources(cfg)] == [provider, "yahoo"]


def test_collect_market_data_offline(tmp_path, monkeypatch):
    """End to end with the fake source: prices, benchmark and risk-free rate line up."""
    monkeypatch.setattr(collect, "build_sources", lambda cfg: [FakeSource()])
    cfg = RiskConfig(tickers=("AAA", "BBB"), benchmark="IDX", start=date(2023, 1, 1), cache_dir=tmp_path)
    md = collect.collect_market_data(cfg)
    assert list(md.prices.columns) == ["AAA", "BBB"] and len(md.benchmark) == 10
    assert md.risk_free.notna().all() and md.failed == ()
