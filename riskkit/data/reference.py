"""Facts about each stock (name, sector, size, currency) and the risk-free rate.

- Sector: tech, banks, energy... used later for "risk by sector".
- Market cap: a company's total stock-market value, used for "weight by size".
- Risk-free rate: what a safe 3-month US government bill pays (Yahoo ticker ^IRX).
Profiles are saved as small JSON files and refreshed weekly.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from riskkit.data.cache import load_prices
from riskkit.data.sources.base import DataUnavailableError, PriceSource

RISK_FREE_TICKER = "^IRX"          # 13-week US T-bill yield, in percent per year
FALLBACK_RISK_FREE = 0.02          # 2% a year, used only if ^IRX cannot be loaded
TRADING_DAYS = 252
PROFILE_MAX_AGE = timedelta(days=7)


@dataclass(frozen=True)
class StockProfile:
    """Descriptive facts about one listed company or fund."""

    ticker: str
    name: str
    sector: str
    industry: str
    country: str
    currency: str
    shares_outstanding: float | None
    market_cap: float | None


#: Offline fallback for the brief's 10 stocks and the benchmark (approximate share counts).
KNOWN_PROFILES: dict[str, StockProfile] = {
    p.ticker: p for p in [
        StockProfile("AAPL", "Apple", "Technology", "Consumer Electronics", "United States", "USD", 14.9e9, None),
        StockProfile("MSFT", "Microsoft", "Technology", "Software", "United States", "USD", 7.43e9, None),
        StockProfile("NVDA", "NVIDIA", "Technology", "Semiconductors", "United States", "USD", 24.4e9, None),
        StockProfile("JPM", "JPMorgan Chase", "Financial Services", "Banks", "United States", "USD", 2.78e9, None),
        StockProfile("XOM", "Exxon Mobil", "Energy", "Oil & Gas", "United States", "USD", 4.3e9, None),
        StockProfile("AMZN", "Amazon", "Consumer Cyclical", "Internet Retail", "United States", "USD", 10.6e9, None),
        StockProfile("META", "Meta Platforms", "Communication Services", "Internet Content", "United States", "USD", 2.52e9, None),
        StockProfile("GOOGL", "Alphabet", "Communication Services", "Internet Content", "United States", "USD", 12.1e9, None),
        StockProfile("TSLA", "Tesla", "Consumer Cyclical", "Auto Manufacturers", "United States", "USD", 3.22e9, None),
        StockProfile("UNH", "UnitedHealth", "Healthcare", "Healthcare Plans", "United States", "USD", 0.905e9, None),
        StockProfile("SPY", "S&P 500 tracker (SPDR)", "Index fund", "Index fund", "United States", "USD", None, None),
    ]
}


def unknown_profile(ticker: str) -> StockProfile:
    """A placeholder profile when nothing is known about a ticker (assumes USD)."""
    return StockProfile(ticker, ticker, "Unknown", "Unknown", "Unknown", "USD", None, None)


def fetch_profile(ticker: str) -> StockProfile:
    """Ask Yahoo for a ticker's name, sector, country, currency and size."""
    import yfinance as yf

    try:
        info = yf.Ticker(ticker).get_info() or {}
    except Exception as exc:
        raise DataUnavailableError(f"No profile for {ticker}: {exc}") from exc
    if not info.get("currency"):
        raise DataUnavailableError(f"Yahoo has no profile for {ticker}.")
    return StockProfile(
        ticker=ticker,
        name=info.get("longName") or info.get("shortName") or ticker,
        sector=info.get("sector") or ("Index fund" if info.get("quoteType") == "ETF" else "Unknown"),
        industry=info.get("industry") or "Unknown",
        country=info.get("country") or "Unknown",
        currency=info["currency"],
        shares_outstanding=info.get("sharesOutstanding"),
        market_cap=info.get("marketCap"),
    )


def _profile_path(cache_dir: Path, ticker: str) -> Path:
    """Where one ticker's profile JSON is saved."""
    return Path(cache_dir) / "profiles" / f"{ticker.replace('^', '_')}.json"


def load_profile(ticker: str, cache_dir: Path, offline: bool = False) -> tuple[StockProfile, str]:
    """A ticker's profile and where it came from: saved file (under a week old) -> Yahoo -> built-in table."""
    path = _profile_path(cache_dir, ticker)
    saved = StockProfile(**json.loads(path.read_text())) if path.exists() else None
    age = date.today() - date.fromtimestamp(path.stat().st_mtime) if path.exists() else None
    if saved and (offline or age <= PROFILE_MAX_AGE):
        return saved, "saved"
    if not offline:
        try:
            profile = fetch_profile(ticker)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(profile), indent=1))
            return profile, "yahoo"
        except DataUnavailableError:
            pass
    if saved:
        return saved, "saved (could not refresh)"
    if ticker in KNOWN_PROFILES:
        return KNOWN_PROFILES[ticker], "built-in table"
    return unknown_profile(ticker), "unknown"


def risk_free_daily(index: pd.DatetimeIndex, sources: list[PriceSource], cache_dir: Path,
                    offline: bool = False) -> tuple[pd.Series, str]:
    """Daily risk-free return on each date (annual T-bill yield / 252), and where it came from."""
    try:
        bills, origin = load_prices(RISK_FREE_TICKER, sources, cache_dir, offline=offline)
        annual = bills["adj_close"] / 100
        daily = (annual / TRADING_DAYS).reindex(index.union(annual.index)).ffill().reindex(index)
        return daily.bfill().rename("risk_free"), origin
    except DataUnavailableError:
        flat = pd.Series(FALLBACK_RISK_FREE / TRADING_DAYS, index=index, name="risk_free")
        return flat, f"flat {FALLBACK_RISK_FREE:.0%} a year (T-bill data unavailable)"
