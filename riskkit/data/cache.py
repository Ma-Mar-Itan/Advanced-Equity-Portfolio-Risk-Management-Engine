"""Keep downloaded prices on disk so we only go to the 'shop' when needed.

One file per source and ticker: data/cache/<source>/<ticker>.parquet, holding the
full history since HISTORY_START (so the 2008 crisis is always available).
Normal dashboard loads are cache-first, even when a saved file is older than a
day.  A network request only happens when the user explicitly refreshes data or
when no saved copy exists.  This keeps startup deterministic and usable offline.
"""

from __future__ import annotations

import shutil
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


def snapshot_dir(cache_dir: Path) -> Path:
    """The saved copy of the cache that ships with the code: data/snapshot next to data/cache."""
    return Path(cache_dir).parent / "snapshot"


def seed_from_snapshot(cache_dir: Path) -> int:
    """Copy snapshot files that are missing from the cache into it, and return how many were copied.

    A fresh install (or the online app, whose disk starts empty) then begins from the shipped
    prices instead of downloading 25 years of history for every stock. The copies count as
    today's files, so nothing is downloaded until "Re-download latest prices" is pressed or a
    stock outside the snapshot is added. Files already in the cache are never overwritten.
    """
    source = snapshot_dir(cache_dir)
    if not source.is_dir():
        return 0
    copied = 0
    for file in source.rglob("*"):
        if not file.is_file():
            continue
        target = Path(cache_dir) / file.relative_to(source)
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
        copied += 1
    return copied


def save_snapshot(cache_dir: Path) -> int:
    """Copy the current cache into the snapshot (run after downloading fresh prices)."""
    target = snapshot_dir(cache_dir)
    count = 0
    for file in Path(cache_dir).rglob("*"):
        if file.is_file() and file.suffix in (".parquet", ".json"):
            dest = target / file.relative_to(cache_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, dest)
            count += 1
    return count


def load_prices(
    ticker: str, sources: list[PriceSource], cache_dir: Path, refresh: bool = False, offline: bool = False
) -> tuple[pd.DataFrame, str]:
    """Full price history for one ticker, plus a label saying where it came from.

    Order: any saved file -> each source in turn (saving the result) -> any older
    saved file after a failed explicit refresh. With offline=True only saved files
    are used. Network access therefore never delays an ordinary cached startup.
    """
    saved = [(s.name, cache_path(cache_dir, s.name, ticker)) for s in sources]
    if not refresh or offline:
        for name, path in saved:
            df = read_cache(path)
            if df is not None:
                freshness = "saved" if is_fresh(path) else "saved, refresh available"
                return df, f"{name} ({freshness})"
    if not offline:
        for source, (name, path) in zip(sources, saved, strict=True):
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
