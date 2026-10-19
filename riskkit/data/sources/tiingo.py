"""Tiingo: an official price API with a free key (30+ years of adjusted prices).

Free plan: 500 different tickers a month, 50 requests an hour, 1,000 a day.
Coverage is mostly US-listed stocks and ETFs, quoted in US dollars.

The key is read from the environment variable TIINGO_API_KEY, or from the
one-line file V2/tiingo_key.txt (keep that file private).
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd

from riskkit.data.sources.base import DataUnavailableError, standardize

API_URL = "https://api.tiingo.com/tiingo/daily/{ticker}/prices"
KEY_FILE = Path(__file__).resolve().parents[3] / "tiingo_key.txt"


def read_api_key() -> str | None:
    """Find the Tiingo key: environment variable first, then tiingo_key.txt. None if absent."""
    key = os.environ.get("TIINGO_API_KEY", "").strip()
    if not key and KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
    return key or None


def tiingo_symbol(ticker: str) -> str:
    """Translate a Yahoo-style ticker to Tiingo's spelling (BRK-B stays BRK-B; dots become dashes)."""
    return ticker.replace(".", "-").lower()


class TiingoSource:
    """Daily prices from Tiingo's end-of-day endpoint."""

    name = "tiingo"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or read_api_key()

    @property
    def available(self) -> bool:
        """True when a key is configured, so Tiingo can actually be called."""
        return self.api_key is not None

    def fetch_prices(self, ticker: str, start: date, end: date | None) -> pd.DataFrame:
        """Download daily close, adjusted close and volume for one ticker."""
        import requests

        if not self.available:
            raise DataUnavailableError("No Tiingo key: set TIINGO_API_KEY or create tiingo_key.txt.")
        params = {"startDate": start.isoformat(), "token": self.api_key, "format": "json"}
        if end is not None:
            params["endDate"] = end.isoformat()
        try:
            resp = requests.get(API_URL.format(ticker=tiingo_symbol(ticker)), params=params, timeout=20)
            resp.raise_for_status()
            rows = resp.json()
        except Exception as exc:
            raise DataUnavailableError(f"Tiingo failed for {ticker}: {exc}") from exc
        if not isinstance(rows, list) or not rows:
            raise DataUnavailableError(f"Tiingo returned no rows for {ticker}.")
        df = pd.DataFrame(rows).set_index("date")
        df = df.rename(columns={"adjClose": "adj_close"})
        return standardize(df, ticker)

    def currency(self, ticker: str) -> str:
        """Tiingo's end-of-day prices are in US dollars."""
        return "USD"
