"""Price cleaning and return transformation pipeline.

Order: cut to the chosen dates -> one calendar -> stale prices -> fill gaps ->
returns -> winsorize (optional) -> custom formula (optional) -> validation checks.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.cleaning import align_calendar, fill_missing, handle_stale, log_from_mask
from riskkit.data.collect import MarketData
from riskkit.data.returns import to_returns
from riskkit.data.transforms import apply_custom_expression, winsorize
from riskkit.data.validation import Check, run_checks


@dataclass(frozen=True)
class CleanData:
    """Cleaned prices, transformed returns, audit log, and validation results."""

    prices: pd.DataFrame  # clean price matrix (dates x stocks)
    raw_returns: pd.DataFrame  # returns straight from the clean prices
    returns: pd.DataFrame  # after winsorizing and the custom formula (what later modules use)
    log: pd.DataFrame  # every change made, one row each
    checks: list[Check]

    def changed_returns(self) -> int:
        """How many daily returns winsorizing and the custom formula changed in total."""
        return self.count("winsorize") + self.count("formula")

    def count(self, step: str) -> int:
        """How many cells a cleaning step touched (summary rows with no date are not counted)."""
        rows = self.log[(self.log["step"] == step) & self.log["date"].notna()]
        return len(rows)


def changed_cells(before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    """True where a value differs between two tables (compared on the dates both share)."""
    common = before.reindex(after.index)
    return (common - after).abs() > 1e-12


def window(md: MarketData, cfg: RiskConfig) -> pd.DataFrame:
    """The raw prices between the config's start and end dates."""
    return md.prices.loc[pd.Timestamp(cfg.start) : pd.Timestamp(cfg.end) if cfg.end else None]


def clean_market_data(md: MarketData, cfg: RiskConfig) -> CleanData:
    """Run every cleaning step in order and validate the result."""
    spec = cfg.cleaning
    prices, log_cal = align_calendar(window(md, cfg), spec.calendar, md.benchmark)
    prices, log_stale = handle_stale(prices, spec.stale_days, spec.stale_action)
    prices, log_fill = fill_missing(prices, spec.fill_method, spec.fill_limit)
    raw_returns = to_returns(prices, spec.return_type)
    returns, log_win = winsorize(
        raw_returns,
        spec.winsor_method,
        lower=spec.winsor_lower,
        upper=spec.winsor_upper,
        k=spec.winsor_k,
        cap=spec.winsor_cap,
    )
    before_formula = returns
    returns = apply_custom_expression(returns, spec.custom_expression)
    log_formula = log_from_mask(changed_cells(before_formula, returns), "formula", "return changed by custom formula")
    logs = [x for x in (log_cal, log_stale, log_fill, log_win, log_formula) if not x.empty]
    log = pd.concat(logs, ignore_index=True) if logs else log_cal.iloc[0:0].copy()
    # Mixed timestamp/ISO values are expected because different cleaning stages
    # contribute to one audit log.  Declaring that format avoids pandas' ambiguous
    # parsing warning while preserving invalid summary rows as missing dates.
    log["date"] = pd.to_datetime(log["date"], format="mixed", errors="coerce")
    return CleanData(prices, raw_returns, returns, log, run_checks(cfg, prices, raw_returns, returns))
