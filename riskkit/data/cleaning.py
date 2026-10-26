"""Price-calendar alignment, stale-price handling, and gap treatment.

Each step is a small pure function: a price table in, a cleaned table out, plus
audit rows describing each modification.
"""

from __future__ import annotations

import pandas as pd

LOG_COLUMNS = ["step", "date", "ticker", "detail"]


def log_from_mask(mask: pd.DataFrame, step: str, detail: str) -> pd.DataFrame:
    """One log row for every True cell in a dates x stocks mask."""
    hits = mask.stack()
    hits = hits[hits]
    rows = pd.DataFrame(
        {
            "step": step,
            "date": hits.index.get_level_values(0),
            "ticker": hits.index.get_level_values(1),
            "detail": detail,
        }
    )
    return rows[LOG_COLUMNS]


def empty_log() -> pd.DataFrame:
    """A cleaning log with no rows yet."""
    return pd.DataFrame(columns=LOG_COLUMNS)


def align_calendar(prices: pd.DataFrame, calendar: str, benchmark: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Put every stock on one set of trading days.

    union     - keep a day if any stock traded (gaps are filled later)
    common    - keep a day only if every stock traded
    benchmark - keep the benchmark's trading days (US market days for SPY)
    """
    before = len(prices)
    if calendar == "common":
        out = prices.dropna(how="any")
    elif calendar == "benchmark":
        out = prices.reindex(benchmark.dropna().index.intersection(prices.index.union(benchmark.index)))
        out = out.loc[prices.index.min() : prices.index.max()]
    else:
        out = prices.dropna(how="all")
    dropped = before - len(out)
    log = empty_log()
    if dropped:
        log = pd.DataFrame(
            [
                {
                    "step": "calendar",
                    "date": pd.NaT,
                    "ticker": "all",
                    "detail": f"{dropped} days removed by the '{calendar}' calendar",
                }
            ]
        )
    return out, log


def run_lengths(flags: pd.Series) -> pd.Series:
    """How many True values in a row end at each point of a True/False series (0 where False)."""
    groups = (~flags).cumsum()  # a new group starts at every False
    return flags.astype(int).groupby(groups).cumsum()


def find_stale(prices: pd.DataFrame, max_days: int) -> pd.DataFrame:
    """True where a price has been exactly unchanged for more than `max_days` trading days in a row."""
    if max_days <= 0:
        return pd.DataFrame(False, index=prices.index, columns=prices.columns)
    unchanged = prices.diff().eq(0) & prices.notna()
    return unchanged.apply(run_lengths) > max_days


def handle_stale(prices: pd.DataFrame, max_days: int, action: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Log stale prices; with action='remove' also blank them so the fill rule decides what happens."""
    stale = find_stale(prices, max_days)
    verb = "removed" if action == "remove" else "flagged"
    log = log_from_mask(stale, "stale", f"price unchanged for over {max_days} days ({verb})")
    return (prices.mask(stale) if action == "remove" else prices), log


def fill_missing(prices: pd.DataFrame, method: str, limit: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fill gaps inside each stock's history; days that stay incomplete are dropped.

    ffill       - repeat the last known price (at most `limit` days in a row)
    interpolate - draw a straight line between the prices either side (at most `limit` days)
    drop        - fill nothing; any day with a missing price is dropped
    Days before a stock's first price are always dropped (the stock did not exist yet).
    """
    gaps = prices.isna() & prices.ffill().notna() & prices.bfill().notna()  # holes inside a history
    if method == "ffill":
        filled = prices.ffill(limit=limit)
    elif method == "interpolate":
        filled = prices.interpolate(method="time", limit=limit, limit_area="inside")
    else:
        filled = prices.copy()
    was_filled = gaps & filled.notna()
    log = log_from_mask(was_filled, "fill", f"missing price filled ({method})")
    complete = filled.dropna(how="any")
    dropped = len(filled) - len(complete)
    if dropped:
        log = pd.concat(
            [
                log,
                pd.DataFrame(
                    [
                        {
                            "step": "fill",
                            "date": pd.NaT,
                            "ticker": "all",
                            "detail": f"{dropped} days with a missing price dropped",
                        }
                    ]
                ),
            ]
        )
    return complete, log
