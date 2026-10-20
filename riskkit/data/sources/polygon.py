"""Polygon/Massive daily aggregate bars (API key required).

Set ``POLYGON_API_KEY``.  The aggregates endpoint supplies split-adjusted bars;
the adapter follows pagination and uses the common source fallback contract.
"""

from __future__ import annotations

import os
from datetime import date

import pandas as pd

from riskkit.data.sources.base import DataUnavailableError, standardize

API_URL = "https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"


class PolygonSource:
    name = "polygon"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY", "").strip() or None

    @property
    def available(self) -> bool:
        return self.api_key is not None

    def fetch_prices(self, ticker: str, start: date, end: date | None) -> pd.DataFrame:
        import requests

        if not self.available:
            raise DataUnavailableError("No Polygon key: set POLYGON_API_KEY.")
        finish = end or date.today()
        url = API_URL.format(ticker=ticker, start=start.isoformat(), end=finish.isoformat())
        params = {"adjusted": "true", "sort": "asc", "limit": 50_000, "apiKey": self.api_key}
        rows: list[dict] = []
        try:
            while url:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                payload = response.json()
                if payload.get("status") in {"ERROR", "NOT_AUTHORIZED"}:
                    raise DataUnavailableError(payload.get("error") or payload.get("message") or "API error")
                rows.extend(payload.get("results") or [])
                url = payload.get("next_url")
                params = {"apiKey": self.api_key} if url else {}
        except DataUnavailableError:
            raise
        except Exception as exc:
            raise DataUnavailableError(f"Polygon failed for {ticker}: {exc}") from exc
        if not rows:
            raise DataUnavailableError(f"Polygon returned no rows for {ticker}.")
        frame = pd.DataFrame(rows)
        frame.index = pd.to_datetime(frame["t"], unit="ms")
        frame = frame.rename(columns={"c": "close", "v": "volume"})
        frame["adj_close"] = frame["close"]
        return standardize(frame, ticker)

    def currency(self, ticker: str) -> str:
        return "USD"
