"""Keep downloaded prices on disk so we only go to the 'shop' when needed.

One file per source and ticker: data/cache/<source>/<ticker>.parquet, holding the
full history since HISTORY_START (so the 2008 crisis is always available).
A file written today counts as fresh; older files are refreshed on the next run,
and if the download then fails the old file is used rather than nothing.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from riskkit.data.sources.base import PRICE_COLUMNS, DataUnavailableError, PriceSource

HISTORY_START = date(2000, 1, 1)


def cache_path(cache_dir: Path, source_name: str, ticker: str) -> Path:
    """Where one ticker's prices from one source are saved (^ and / are not allowed in file names)."""
    safe = ticker.replace("^", "_").replace("/", "_").replace("=", "_")
    return Path(cache_dir) / source_name / f"{safe}.parquet"


def read_cache(path: Path) -> pd.DataFrame | None:
    """Read a saved price table, or None if it is missing or unreadable."""
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path)
    except Exception:
        return None
    if not set(PRICE_COLUMNS) <= set(df.columns):
        return None
    return df[list(PRICE_COLUMNS)]


def write_cache(path: Path, df: pd.DataFrame) -> None:
    """Save a price table, creating the folder if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


def is_fresh(path: Path, today: date | None = None) -> bool:
    """True when the file was written today."""
    return path.exists() and date.fromtimestamp(path.stat().st_mtime) == (today or date.today())


def load_prices(ticker: str, sources: list[PriceSource], cache_dir: Path,
                refresh: bool = False, offline: bool = False) -> tuple[pd.DataFrame, str]:
    """Full price history for one ticker, plus a label saying where it came from.

    Order: today's saved file -> each source in turn (saving the result) -> any older
    saved file. With offline=True only saved files are used.
    """
    saved = [(s.name, cache_path(cache_dir, s.name, ticker)) for s in sources]
    if not refresh or offline:
        for name, path in saved:
            if offline or is_fresh(path):
                df = read_cache(path)
                if df is not None:
                    return df, f"{name} (saved)"
    if not offline:
        for source, (name, path) in zip(sources, saved):
            try:
                df = source.fetch_prices(ticker, HISTORY_START, None)
            except DataUnavailableError:
                continue
            write_cache(path, df)
            return df, name
    for name, path in saved:
        df = read_cache(path)
        if df is not None:
            return df, f"{name} (saved, could not refresh)"
    raise DataUnavailableError(f"No prices for {ticker} from {[s.name for s in sources]} or the cache.")
