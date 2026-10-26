"""Price sources and a lookup by name."""

from riskkit.data.sources.alpha_vantage import AlphaVantageSource
from riskkit.data.sources.base import PRICE_COLUMNS, DataUnavailableError, PriceSource
from riskkit.data.sources.polygon import PolygonSource
from riskkit.data.sources.stooq import StooqSource
from riskkit.data.sources.tiingo import TiingoSource
from riskkit.data.sources.yahoo import YahooSource

SOURCES = {
    "yahoo": YahooSource,
    "stooq": StooqSource,
    "tiingo": TiingoSource,
    "alpha_vantage": AlphaVantageSource,
    "polygon": PolygonSource,
}

# Dashboard sources use the same cache-first fallback chain. Provider-specific
# cache entries retain priority over the versioned Yahoo snapshot.
DASHBOARD_SOURCES = ("yahoo", "stooq", "alpha_vantage", "polygon")


def dashboard_source_names() -> tuple[str, ...]:
    """Dashboard choices, plus WRDS only when a usable adapter is installed."""
    names = list(DASHBOARD_SOURCES)
    if "wrds" in SOURCES:
        wrds = get_source("wrds")
        if getattr(wrds, "available", False):
            names.append("wrds")
    return tuple(names)


def get_source(name: str) -> PriceSource:
    """Build a price source from its registered name."""
    if name not in SOURCES:
        raise ValueError(f"Unknown price source '{name}'. Choose from {sorted(SOURCES)}.")
    return SOURCES[name]()


__all__ = [
    "PRICE_COLUMNS",
    "DataUnavailableError",
    "PriceSource",
    "SOURCES",
    "get_source",
    "DASHBOARD_SOURCES",
    "dashboard_source_names",
    "AlphaVantageSource",
    "PolygonSource",
    "StooqSource",
    "TiingoSource",
    "YahooSource",
]
