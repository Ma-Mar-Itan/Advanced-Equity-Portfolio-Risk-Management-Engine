"""Alpha Vantage adjusted daily prices (API key required).

Set ``ALPHAVANTAGE_API_KEY``.  The adjusted daily endpoint is a premium endpoint
on current Alpha Vantage plans; errors and rate-limit messages are converted to
``DataUnavailableError`` so the normal fallback chain can continue.
"""

from __future__ import annotations

import os
from datetime import date

import pandas as pd

from riskkit.data.sources.base import DataUnavailableError, standardize

API_URL = "https://www.alphavantage.co/query"


class AlphaVantageSource:
    name = "alpha_vantage"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY", "").strip() or None

    @property
    def available(self) -> bool:
        return self.api_key is not None

    def fetch_prices(self, ticker: str, start: date, end: date | None) -> pd.DataFrame:
        import requests

        if not self.available:
            raise DataUnavailableError("No Alpha Vantage key: set ALPHAVANTAGE_API_KEY.")
        params = {"function": "TIME_SERIES_DAILY_ADJUSTED", "symbol": ticker,
                  "outputsize": "full", "apikey": self.api_key}
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise DataUnavailableError(f"Alpha Vantage failed for {ticker}: {exc}") from exc
        rows = payload.get("Time Series (Daily)") if isinstance(payload, dict) else None
        if not rows:
            message = payload.get("Note") or payload.get("Information") or payload.get("Error Message") \
                if isinstance(payload, dict) else None
            raise DataUnavailableError(f"Alpha Vantage returned no rows for {ticker}: {message or 'unknown error'}")
        frame = pd.DataFrame.from_dict(rows, orient="index").rename(columns={
            "4. close": "close", "5. adjusted close": "adj_close", "6. volume": "volume"
        })
        frame = standardize(frame, ticker)
        stop = pd.Timestamp(end) if end else frame.index.max()
        return frame.loc[pd.Timestamp(start):stop]

    def currency(self, ticker: str) -> str:
        return "USD"
