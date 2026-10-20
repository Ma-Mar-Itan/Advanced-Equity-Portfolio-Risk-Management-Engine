"""Stooq downloadable daily CSV data (no key).

Plain US equity tickers are translated to Stooq's ``.US`` suffix.  Stooq does
not publish an API stability contract, so this source is best used as a fallback
and all failures degrade cleanly to the next source or local cache.
"""

from __future__ import annotations

from datetime import date
from io import StringIO

import pandas as pd

from riskkit.data.sources.base import DataUnavailableError, standardize

API_URL = "https://stooq.com/q/d/l/"


def stooq_symbol(ticker: str) -> str:
    return ticker.lower() if any(c in ticker for c in ".^=") else f"{ticker.lower()}.us"


class StooqSource:
    name = "stooq"
    available = True

    def fetch_prices(self, ticker: str, start: date, end: date | None) -> pd.DataFrame:
        import requests

        params = {"s": stooq_symbol(ticker), "d1": start.strftime("%Y%m%d"), "i": "d"}
        if end:
            params["d2"] = end.strftime("%Y%m%d")
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            frame = pd.read_csv(StringIO(response.text))
        except Exception as exc:
            raise DataUnavailableError(f"Stooq failed for {ticker}: {exc}") from exc
        if frame.empty or "Date" not in frame or "Close" not in frame:
            raise DataUnavailableError(f"Stooq returned no rows for {ticker}.")
        frame = frame.rename(columns={"Close": "close", "Volume": "volume"}).set_index("Date")
        frame["adj_close"] = frame["close"]
        if "volume" not in frame:
            frame["volume"] = 0.0
        return standardize(frame, ticker)

    def currency(self, ticker: str) -> str:
        return "USD"
