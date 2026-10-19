"""Find any stock in the world by name: type 'Nestle', get 'NESN.SW' (Swiss listing).

Yahoo's ticker spelling adds an exchange suffix outside the US:
.L London, .PA Paris, .DE Germany, .SW Switzerland, .T Tokyo, .HK Hong Kong, .TO Toronto...
"""

from __future__ import annotations

import pandas as pd

SEARCH_COLUMNS = ["symbol", "name", "exchange", "type"]
USEFUL_TYPES = {"EQUITY", "ETF", "INDEX", "MUTUALFUND"}


def quotes_to_table(quotes: list[dict]) -> pd.DataFrame:
    """Turn Yahoo's raw search hits into a tidy table of stocks, funds and indexes."""
    rows = [
        {
            "symbol": q.get("symbol"),
            "name": q.get("longname") or q.get("shortname") or q.get("symbol"),
            "exchange": q.get("exchDisp") or q.get("exchange"),
            "type": q.get("typeDisp") or q.get("quoteType"),
        }
        for q in quotes
        if q.get("symbol") and q.get("quoteType") in USEFUL_TYPES
    ]
    return pd.DataFrame(rows, columns=SEARCH_COLUMNS)


def search_tickers(query: str, max_results: int = 10) -> pd.DataFrame:
    """Search Yahoo for tickers matching a company name or symbol. Empty table if offline."""
    import yfinance as yf

    if not query.strip():
        return pd.DataFrame(columns=SEARCH_COLUMNS)
    try:
        hits = yf.Search(query, max_results=max_results, news_count=0).quotes
    except Exception:
        return pd.DataFrame(columns=SEARCH_COLUMNS)
    return quotes_to_table(hits)
