"""Yahoo Finance through the yfinance package: free, worldwide, no key.

Yahoo is unofficial and blocks bursts of requests, so every call here is spaced
out and retried a couple of times before giving up.
"""

from __future__ import annotations

import time
from datetime import date, timedelta

import pandas as pd

from riskkit.data.sources.base import DataUnavailableError, standardize

PAUSE_SECONDS = 0.6      # polite gap between Yahoo calls
RETRIES = 3

_YAHOO_COLUMNS = {"Close": "close", "Adj Close": "adj_close", "Volume": "volume"}


def _with_retries(call, what: str):
    """Run a Yahoo call, waiting longer after each failure (Yahoo rate-limits bursts)."""
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            time.sleep(PAUSE_SECONDS * (1 + 2 * attempt))
            return call()
        except Exception as exc:  # network error, rate limit, unknown ticker
            last_error = exc
    raise DataUnavailableError(f"Yahoo failed for {what}: {last_error}")


class YahooSource:
    """Daily prices and quote currency from Yahoo Finance."""

    name = "yahoo"

    def fetch_prices(self, ticker: str, start: date, end: date | None) -> pd.DataFrame:
        """Download daily close, adjusted close and volume for one ticker."""
        import yfinance as yf  # imported here so the engine loads even without yfinance

        stop = (end or date.today()) + timedelta(days=1)  # Yahoo's end date is exclusive

        def download() -> pd.DataFrame:
            df = yf.download(ticker, start=start, end=stop, auto_adjust=False,
                             progress=False, threads=False, multi_level_index=False)
            if df is None or df.empty:
                raise DataUnavailableError(f"Yahoo returned no rows for {ticker}.")
            return df

        raw = _with_retries(download, ticker)
        return standardize(raw.rename(columns=_YAHOO_COLUMNS), ticker)

    def currency(self, ticker: str) -> str:
        """Quote currency as Yahoo reports it ('USD', 'EUR', 'GBp' for pence...)."""
        import yfinance as yf

        return str(_with_retries(lambda: yf.Ticker(ticker).fast_info["currency"], ticker))
