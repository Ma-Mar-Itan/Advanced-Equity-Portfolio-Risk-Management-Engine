"""Point-in-time shares outstanding for look-ahead-safe size weighting.

Market-cap weights require the share count that was known on each rebalance
date.  A current profile value is not a historical observation and must never be
backfilled into the past.  This module keeps Yahoo's dated share observations in
their own cache and applies a one-business-day availability lag before use.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from pandas.tseries.offsets import BDay

from riskkit.data.cache import HISTORY_START
from riskkit.data.sources.base import DataUnavailableError


def shares_cache_path(cache_dir: Path, ticker: str) -> Path:
    safe = ticker.replace("^", "_").replace("/", "_").replace("=", "_")
    return Path(cache_dir) / "shares" / f"{safe}.parquet"


def _standardize(series: pd.Series, ticker: str, *, apply_lag: bool = True) -> pd.Series:
    if series is None or series.empty:
        raise DataUnavailableError(f"No dated share counts returned for {ticker}.")
    out = pd.to_numeric(series, errors="coerce").dropna()
    out.index = pd.to_datetime(out.index)
    if out.index.tz is not None:
        out.index = out.index.tz_localize(None)
    out.index = out.index.normalize() + (BDay(1) if apply_lag else BDay(0))
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out = out[out > 0].rename(ticker)
    if out.empty:
        raise DataUnavailableError(f"No valid dated share counts returned for {ticker}.")
    return out


def fetch_shares(ticker: str, start: date = HISTORY_START) -> pd.Series:
    """Download Yahoo's dated shares outstanding and lag availability one day."""
    import yfinance as yf

    try:
        raw = yf.Ticker(ticker).get_shares_full(start=start.isoformat())
    except Exception as exc:
        raise DataUnavailableError(f"Could not load dated share counts for {ticker}: {exc}") from exc
    return _standardize(raw, ticker)


def load_shares(ticker: str, cache_dir: Path, refresh: bool = False,
                offline: bool = False) -> tuple[pd.Series, str]:
    """Return dated shares from cache first, refreshing only when requested."""
    path = shares_cache_path(cache_dir, ticker)
    saved = None
    if path.exists():
        try:
            frame = pd.read_parquet(path)
            saved = _standardize(frame.iloc[:, 0], ticker, apply_lag=False)
        except Exception:
            saved = None
    if saved is not None and (not refresh or offline):
        return saved, "yahoo shares (saved)"
    if not offline:
        try:
            series = fetch_shares(ticker)
            path.parent.mkdir(parents=True, exist_ok=True)
            series.to_frame("shares").to_parquet(path)
            return series, "yahoo shares"
        except DataUnavailableError:
            pass
    if saved is not None:
        return saved, "yahoo shares (saved, could not refresh)"
    raise DataUnavailableError(
        f"No dated share-count history for {ticker}. Market-cap weighting cannot safely use a current share count."
    )


def shares_asof(history: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Last share observation available on each date; never backfill future data."""
    union = history.index.union(dates).sort_values()
    return history.reindex(union).ffill().reindex(dates)
