"""Price sources and a lookup by name."""

from riskkit.data.sources.base import PRICE_COLUMNS, DataUnavailableError, PriceSource
from riskkit.data.sources.tiingo import TiingoSource
from riskkit.data.sources.yahoo import YahooSource

SOURCES = {"yahoo": YahooSource, "tiingo": TiingoSource}


def get_source(name: str) -> PriceSource:
    """Build a price source from its name ('yahoo' or 'tiingo')."""
    if name not in SOURCES:
        raise ValueError(f"Unknown price source '{name}'. Choose from {sorted(SOURCES)}.")
    return SOURCES[name]()


__all__ = ["PRICE_COLUMNS", "DataUnavailableError", "PriceSource", "SOURCES", "get_source",
           "TiingoSource", "YahooSource"]
