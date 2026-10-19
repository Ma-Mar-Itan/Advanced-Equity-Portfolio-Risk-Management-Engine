"""The shape every price source must have.

Yahoo and Tiingo are two shops selling the same groceries. This file defines the
one shopping bag they both fill, so the rest of the engine never knows or cares
which shop the prices came from. Adding a source = one new file with these two methods.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

import pandas as pd

#: Columns every source returns, indexed by trading date (no time zone).
#:   close     - the price printed at the close that day
#:   adj_close - the close corrected for splits and dividends (what risk uses)
#:   volume    - number of shares traded
PRICE_COLUMNS: tuple[str, ...] = ("close", "adj_close", "volume")


class DataUnavailableError(RuntimeError):
    """Raised when a source cannot supply data for a ticker."""


class PriceSource(Protocol):
    """Anything that can hand back daily prices for one ticker."""

    name: str

    def fetch_prices(self, ticker: str, start: date, end: date | None) -> pd.DataFrame:
        """Daily prices for one ticker, with exactly the PRICE_COLUMNS."""
        ...

    def currency(self, ticker: str) -> str:
        """The currency the ticker's prices are quoted in, e.g. 'USD', 'EUR', 'GBp'."""
        ...


def standardize(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Tidy a source's raw table: plain dates as index, the standard columns, sorted, no empty rows."""
    if df is None or df.empty:
        raise DataUnavailableError(f"No prices returned for {ticker}.")
    out = df.copy()
    out.index = pd.to_datetime(out.index)
    if out.index.tz is not None:
        out.index = out.index.tz_localize(None)
    out.index = out.index.normalize()
    out.index.name = "date"
    if "adj_close" not in out:
        out["adj_close"] = out["close"]
    missing = [c for c in PRICE_COLUMNS if c not in out]
    if missing:
        raise DataUnavailableError(f"{ticker}: source table is missing {missing}.")
    out = out[list(PRICE_COLUMNS)].astype(float)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out.dropna(subset=["adj_close"])
