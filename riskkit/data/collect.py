"""Market-data collection and provenance tracking.

The collector retrieves adjusted prices, benchmark data, the risk-free rate,
company profiles, and point-in-time share counts. Price cleaning is handled by
``riskkit.data.pipeline``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.cache import load_prices, seed_from_snapshot
from riskkit.data.fx import convert_prices, fx_ticker, major_currency, needs_conversion
from riskkit.data.reference import StockProfile, load_profile, risk_free_daily
from riskkit.data.shares import load_shares
from riskkit.data.sources import DataUnavailableError, PriceSource, get_source


@dataclass(frozen=True)
class MarketData:
    """Raw market data and source provenance for one configuration.

    Price histories are retained from 2000 so historical stress periods remain
    available. Downstream calculations apply the configured analysis window.
    """

    prices: pd.DataFrame  # adjusted close in the base currency, dates x tickers
    benchmark: pd.Series  # benchmark adjusted close (base currency)
    risk_free: pd.Series  # daily risk-free return on each date
    profiles: dict[str, StockProfile]
    origin: dict[str, str]  # ticker (or 'risk-free', 'fx:EUR') -> where it came from
    failed: tuple[str, ...]  # tickers nothing could be found for
    shares: pd.DataFrame = field(default_factory=pd.DataFrame)  # point-in-time shares for size weighting

    @property
    def as_of(self) -> pd.Timestamp:
        """The latest date with a price for every stock."""
        return self.prices.dropna().index.max()


def build_sources(cfg: RiskConfig) -> list[PriceSource]:
    """Build the cache/fetch chain, ending with the public Yahoo snapshot.

    Provider-specific saved files keep priority.  Yahoo is always the final
    fallback for a non-Yahoo primary so every dashboard choice can use the
    shipped no-key cache when that provider is down or has no saved file.
    """
    sources: list[PriceSource] = []
    for name in (cfg.source, cfg.fallback_source, "yahoo"):
        if not name or any(source.name == name for source in sources):
            continue
        source = get_source(name)
        if name == cfg.source or getattr(source, "available", True):
            sources.append(source)
    return sources


def price_in_base(
    ticker: str, local: pd.Series, currency: str, cfg: RiskConfig, sources: list[PriceSource], origin: dict[str, str]
) -> pd.Series:
    """One stock's adjusted prices converted from its quote currency into the base currency."""
    if not needs_conversion(currency, cfg.base_currency):
        return local
    major, divisor = major_currency(currency)
    rate = None
    if major != cfg.base_currency:
        fx, where = load_prices(fx_ticker(major, cfg.base_currency), sources[:1], cfg.cache_dir, offline=cfg.offline)
        rate = fx["adj_close"]
        origin[f"fx:{major}"] = where
    return convert_prices(local, rate, divisor)


def collect_market_data(cfg: RiskConfig, refresh: bool = False) -> MarketData:
    """Fetch prices, benchmark, risk-free rate and profiles for every stock in the config."""
    seed_from_snapshot(cfg.cache_dir)
    sources = build_sources(cfg)
    columns: dict[str, pd.Series] = {}
    profiles: dict[str, StockProfile] = {}
    shares: dict[str, pd.Series] = {}
    origin: dict[str, str] = {}
    failed: list[str] = []

    for ticker in (*cfg.tickers, cfg.benchmark):
        try:
            table, where = load_prices(ticker, sources, cfg.cache_dir, refresh=refresh, offline=cfg.offline)
        except DataUnavailableError:
            failed.append(ticker)
            continue
        profile, _ = load_profile(ticker, cfg.cache_dir, offline=cfg.offline, refresh=refresh)
        currency = "USD" if where.startswith("tiingo") else profile.currency
        columns[ticker] = price_in_base(ticker, table["adj_close"], currency, cfg, sources, origin)
        profiles[ticker] = profile
        origin[ticker] = where
        if ticker in cfg.tickers and cfg.portfolio.scheme == "market_cap":
            try:
                shares[ticker], origin[f"shares:{ticker}"] = load_shares(
                    ticker, cfg.cache_dir, refresh=refresh, offline=cfg.offline
                )
            except DataUnavailableError:
                # The portfolio builder reports all missing point-in-time histories
                # together with a precise corrective action.
                pass

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
    share_frame = pd.DataFrame(shares).sort_index() if shares else pd.DataFrame(columns=stocks)
    return MarketData(prices, benchmark, risk_free, profiles, origin, tuple(failed), share_frame)


def summary_table(md: MarketData, cfg: RiskConfig) -> pd.DataFrame:
    """One row per stock: name, sector, currency, first date, number of days since cfg.start, source."""
    since = md.prices.loc[pd.Timestamp(cfg.start) :]
    rows = []
    for t in md.prices.columns:
        p = md.profiles[t]
        rows.append(
            {
                "ticker": t,
                "name": p.name,
                "sector": p.sector,
                "currency": p.currency,
                "first price": md.prices[t].first_valid_index().date(),
                "days since start": int(since[t].notna().sum()),
                "source": md.origin[t],
            }
        )
    return pd.DataFrame(rows).set_index("ticker")
