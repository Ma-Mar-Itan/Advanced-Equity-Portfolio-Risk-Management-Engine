"""Module 1 in one call: config in, everything the later modules need out.

collect_market_data(cfg) fetches each stock's adjusted prices (converted to USD),
the benchmark, the risk-free rate and each stock's profile, and records where every
piece came from. Nothing here is cleaned yet: that is Module 2.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.cache import load_prices
from riskkit.data.fx import convert_prices, fx_ticker, major_currency, needs_conversion
from riskkit.data.reference import StockProfile, load_profile, risk_free_daily
from riskkit.data.sources import DataUnavailableError, PriceSource, get_source
from riskkit.data.sources.tiingo import TiingoSource


@dataclass(frozen=True)
class MarketData:
    """Raw market data for one config. Prices keep their full history (from 2000) so
    crises like 2008 stay available; later modules cut at cfg.start themselves."""

    prices: pd.DataFrame            # adjusted close in the base currency, dates x tickers
    benchmark: pd.Series            # benchmark adjusted close (base currency)
    risk_free: pd.Series            # daily risk-free return on each date
    profiles: dict[str, StockProfile]
    origin: dict[str, str]          # ticker (or 'risk-free', 'fx:EUR') -> where it came from
    failed: tuple[str, ...]         # tickers nothing could be found for

    @property
    def as_of(self) -> pd.Timestamp:
        """The latest date with a price for every stock."""
        return self.prices.dropna().index.max()


def build_sources(cfg: RiskConfig) -> list[PriceSource]:
    """The sources to try, in order: the primary, then the fallback if it is usable."""
    sources = [get_source(cfg.source)]
    if cfg.fallback_source and cfg.fallback_source != cfg.source:
        fallback = get_source(cfg.fallback_source)
        if not isinstance(fallback, TiingoSource) or fallback.available:
            sources.append(fallback)
    return sources


def price_in_base(ticker: str, local: pd.Series, currency: str, cfg: RiskConfig,
                  sources: list[PriceSource], origin: dict[str, str]) -> pd.Series:
    """One stock's adjusted prices converted from its quote currency into the base currency."""
    if not needs_conversion(currency, cfg.base_currency):
        return local
    major, divisor = major_currency(currency)
    rate = None
    if major != cfg.base_currency:
        fx, where = load_prices(fx_ticker(major, cfg.base_currency), sources[:1], cfg.cache_dir,
                                offline=cfg.offline)
        rate = fx["adj_close"]
        origin[f"fx:{major}"] = where
    return convert_prices(local, rate, divisor)


def collect_market_data(cfg: RiskConfig, refresh: bool = False) -> MarketData:
    """Fetch prices, benchmark, risk-free rate and profiles for every stock in the config."""
    sources = build_sources(cfg)
    columns: dict[str, pd.Series] = {}
    profiles: dict[str, StockProfile] = {}
    origin: dict[str, str] = {}
    failed: list[str] = []

    for ticker in (*cfg.tickers, cfg.benchmark):
        try:
            table, where = load_prices(ticker, sources, cfg.cache_dir, refresh=refresh, offline=cfg.offline)
        except DataUnavailableError:
            failed.append(ticker)
            continue
        profile, _ = load_profile(ticker, cfg.cache_dir, offline=cfg.offline)
        currency = "USD" if where.startswith("tiingo") else profile.currency
        columns[ticker] = price_in_base(ticker, table["adj_close"], currency, cfg, sources, origin)
        profiles[ticker] = profile
        origin[ticker] = where

    if cfg.benchmark in failed:
        raise DataUnavailableError(f"Could not load the benchmark {cfg.benchmark}.")
    stocks = [t for t in cfg.tickers if t in columns]
    if not stocks:
        raise DataUnavailableError("None of the stocks could be loaded.")
    prices = pd.DataFrame({t: columns[t] for t in stocks}).sort_index()
    benchmark = columns[cfg.benchmark].rename(cfg.benchmark)
    risk_free, origin["risk-free"] = risk_free_daily(prices.index, sources, cfg.cache_dir, offline=cfg.offline)
    if cfg.end is not None:
        cut = pd.Timestamp(cfg.end)
        prices, benchmark, risk_free = prices.loc[:cut], benchmark.loc[:cut], risk_free.loc[:cut]
    return MarketData(prices, benchmark, risk_free, profiles, origin, tuple(failed))


def summary_table(md: MarketData, cfg: RiskConfig) -> pd.DataFrame:
    """One row per stock: name, sector, currency, first date, number of days since cfg.start, source."""
    since = md.prices.loc[pd.Timestamp(cfg.start):]
    rows = []
    for t in md.prices.columns:
        p = md.profiles[t]
        rows.append({
            "ticker": t, "name": p.name, "sector": p.sector, "currency": p.currency,
            "first price": md.prices[t].first_valid_index().date(),
            "days since start": int(since[t].notna().sum()),
            "source": md.origin[t],
        })
    return pd.DataFrame(rows).set_index("ticker")
