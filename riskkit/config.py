"""The one settings object that travels through the whole engine.

Think of RiskConfig as an order form filled in once: which stocks, how much of
each, which dates, how much money, how sure we want to be. Every engine function
receives this form instead of a pile of loose arguments.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

#: The example universe from the QFI brief (Phase 1).
DEFAULT_TICKERS: tuple[str, ...] = (
    "AAPL",
    "MSFT",
    "NVDA",
    "JPM",
    "XOM",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "UNH",
)

#: Where downloaded prices are saved (V2/data/cache).
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"


@dataclass(frozen=True)
class CleaningSpec:
    """Price-cleaning and return-transformation settings."""

    calendar: str = "union"  # which days to keep: "union" (any stock traded), "common" (all traded),
    # "benchmark" (the benchmark's trading days)
    fill_method: str = "ffill"  # missing prices: "ffill" (repeat last price), "interpolate", "drop" (drop the day)
    fill_limit: int = 5  # at most this many missing days in a row are filled
    stale_days: int = 5  # a price unchanged for more than this many days is stale (0 = off)
    stale_action: str = "flag"  # "flag" (log only) or "remove" (treat as missing, then the fill rule applies)
    return_type: str = "log"  # "log" or "simple"
    winsor_method: str = "none"  # "none", "quantile", "sigma" (mean +/- k std), "cap" (fixed +/- limit)
    winsor_lower: float = 0.001  # quantile method: lower and upper cut-off probabilities
    winsor_upper: float = 0.999
    winsor_k: float = 6.0  # sigma method: how many standard deviations
    winsor_cap: float = 0.25  # cap method: largest allowed daily move (0.25 = 25%)
    custom_expression: str = ""  # optional formula applied to the returns `r`, e.g. "clip(r, -0.2, 0.2)"

    def __post_init__(self) -> None:
        """Reject unknown option names and impossible numbers."""
        choices = {
            "calendar": ("union", "common", "benchmark"),
            "fill_method": ("ffill", "interpolate", "drop"),
            "stale_action": ("flag", "remove"),
            "return_type": ("log", "simple"),
            "winsor_method": ("none", "quantile", "sigma", "cap"),
        }
        for name, allowed in choices.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f"{name} must be one of {allowed}.")
        if not 0 <= self.winsor_lower < self.winsor_upper <= 1:
            raise ValueError("Winsorizing quantiles must satisfy 0 <= lower < upper <= 1.")
        if self.fill_limit < 0 or self.stale_days < 0 or self.winsor_k <= 0 or self.winsor_cap <= 0:
            raise ValueError("Fill limit, stale days, k and cap must be positive.")


@dataclass(frozen=True)
class PortfolioSpec:
    """Portfolio construction and rebalancing settings."""

    scheme: str = "equal"  # "equal", "custom" (uses RiskConfig.weights), "market_cap", "inverse_vol"
    rebalance: str = "monthly"  # "none" (buy and hold), "daily", "monthly", "quarterly", "yearly"
    allow_short: bool = False  # True = custom weights may be negative (long-short)
    max_weight: float = 1.0  # cap on any one stock for market_cap / inverse_vol (1.0 = no cap)
    vol_lookback: int = 63  # inverse_vol: trading days of history used to measure calmness
    cost_bps: float = 0.0  # trading cost per rebalance, in basis points of the amount traded (1bp = 0.01%)
    value_basis: str = "start"  # "start": portfolio_value invested at the start; "today": worth that amount now

    def __post_init__(self) -> None:
        """Reject unknown option names and impossible numbers."""
        choices = {
            "scheme": ("equal", "custom", "market_cap", "inverse_vol"),
            "rebalance": ("none", "daily", "monthly", "quarterly", "yearly"),
            "value_basis": ("today", "start"),
        }
        for name, allowed in choices.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f"{name} must be one of {allowed}.")
        if not 0 < self.max_weight <= 1:
            raise ValueError("Maximum weight must be between 0% and 100%.")
        if self.vol_lookback < 10 or self.cost_bps < 0:
            raise ValueError("Volatility lookback must be at least 10 days and costs cannot be negative.")


@dataclass(frozen=True)
class VolatilitySpec:
    """Volatility-model settings."""

    rolling_window: int = 63  # rolling model: trading days averaged (63 = about 3 months)
    ewma_lambda: float = 0.94  # EWMA memory: 0.94 is the RiskMetrics standard for daily data
    garch_dist: str = "normal"  # shape of GARCH shocks: "normal" or "t" (Student-t, fatter tails)
    garch_mean: str = "zero"  # GARCH mean return: "zero" or "constant"
    horizon: int = 10  # how many days ahead to forecast

    def __post_init__(self) -> None:
        """Reject impossible values."""
        if not 0.5 < self.ewma_lambda < 1:
            raise ValueError("EWMA lambda must be between 0.5 and 1 (0.94 is standard).")
        if self.rolling_window < 5 or not 1 <= self.horizon <= 250:
            raise ValueError("Rolling window must be at least 5 days and the horizon 1 to 250 days.")
        if self.garch_dist not in ("normal", "t") or self.garch_mean not in ("zero", "constant"):
            raise ValueError("GARCH distribution must be 'normal' or 't'; mean 'zero' or 'constant'.")


VAR_MODELS: tuple[str, ...] = ("HS", "EWMA-HS", "GARCH-HS", "GJR-HS")


@dataclass(frozen=True)
class VarSpec:
    """Value at Risk and Expected Shortfall settings."""

    model: str = "GJR-HS"  # "HS" (plain), or history rescaled by "EWMA-HS", "GARCH-HS", "GJR-HS"
    horizon: int = 10  # the longer horizon reported next to 1 day
    horizon_method: str = "sqrt"  # "sqrt": 1-day x sqrt(horizon) (Basel shortcut); "overlapping": real h-day stretches
    refit_every: int = 63  # rolling VaR: refit GARCH parameters every N days, using only past data

    def __post_init__(self) -> None:
        """Reject unknown models and impossible numbers."""
        if self.model not in VAR_MODELS:
            raise ValueError(f"VaR model must be one of {VAR_MODELS}.")
        if self.horizon_method not in ("sqrt", "overlapping") or not 2 <= self.horizon <= 60:
            raise ValueError("Horizon must be 2-60 days; method 'sqrt' or 'overlapping'.")
        if self.refit_every < 5:
            raise ValueError("Refit at most every 5 days.")


@dataclass(frozen=True)
class StressSpec:
    """Historical and hypothetical stress-test settings."""

    historical: tuple[str, ...] = (
        "2008 financial crisis",
        "COVID crash 2020",
        "Inflation shock 2022",
        "Banking stress 2023",
        "Tech selloff 2021-22",
        "Tariff shock April 2025",
    )
    market_shocks: tuple[float, ...] = (-0.05, -0.10, -0.20)  # whole-market moves; each stock moves beta x shock
    vol_multiplier: float = 2.0  # "volatility doubles": every replayed day scaled by this
    corr_blend: float = 0.5  # correlation spike: correlations moved this far towards 1 (0.5 = halfway)
    sector: str = "Technology"  # sector shock: which sector
    sector_shock: float = -0.15  # ... and how much it falls
    spillover: float = 0.0  # share of the sector shock passed to the other stocks through their beta
    custom_shocks: tuple[tuple[str, float], ...] = ()  # your own scenario: (ticker, move) pairs

    def __post_init__(self) -> None:
        """Reject impossible values."""
        if not 0 < self.vol_multiplier <= 10 or not 0 <= self.corr_blend <= 1 or not 0 <= self.spillover <= 1:
            raise ValueError("Volatility multiplier 0-10, correlation blend and spillover 0-1.")
        if any(not -1 <= s <= 1 for s in (*self.market_shocks, self.sector_shock)):
            raise ValueError("Shocks must be between -100% and +100%.")


@dataclass(frozen=True)
class RiskConfig:
    """Every setting a result depends on. Frozen: change it with ``cfg.updated(...)``.

    weights are the custom split used when portfolio.scheme == "custom" (None = equal).
    They are fractions that sum to 1 (0.10 = 10% of the money); negative = short.
    """

    tickers: tuple[str, ...] = DEFAULT_TICKERS
    weights: tuple[float, ...] | None = None
    start: date = date(2012, 6, 1)  # all 10 default stocks trade from here (META listed May 2012)
    end: date | None = None  # None = up to the latest available day
    portfolio_value: float = 10_000_000.0  # dollars
    confidence: float = 0.99  # 99% VaR = the loss we expect to beat 99 days out of 100
    window: int = 500  # trading days of history behind each VaR estimate
    source: str = "yahoo"  # primary price source registered in riskkit.data.sources
    fallback_source: str | None = "yahoo"  # public saved-data fallback; no API key required
    benchmark: str = "SPY"  # S&P 500 tracker, used as "the whole market"
    base_currency: str = "USD"  # every price is converted into this currency
    cache_dir: Path = field(default=DEFAULT_CACHE_DIR)
    offline: bool = False  # True = use saved prices only, never go online
    cleaning: CleaningSpec = field(default_factory=CleaningSpec)
    portfolio: PortfolioSpec = field(default_factory=PortfolioSpec)
    volatility: VolatilitySpec = field(default_factory=VolatilitySpec)
    var: VarSpec = field(default_factory=VarSpec)
    stress: StressSpec = field(default_factory=StressSpec)

    def __post_init__(self) -> None:
        """Reject impossible settings early, with a message a person can act on."""
        object.__setattr__(self, "tickers", tuple(t.strip().upper() for t in self.tickers))
        if not self.tickers:
            raise ValueError("Pick at least one stock.")
        if len(set(self.tickers)) != len(self.tickers):
            raise ValueError("A stock appears twice in the ticker list.")
        if self.weights is not None:
            object.__setattr__(self, "weights", tuple(float(w) for w in self.weights))
            if len(self.weights) != len(self.tickers):
                raise ValueError(f"{len(self.tickers)} stocks but {len(self.weights)} weights.")
            if not math.isclose(sum(self.weights), 1.0, abs_tol=1e-6):
                raise ValueError(f"Weights must add up to 100% (they add up to {sum(self.weights):.2%}).")
            if min(self.weights) < 0 and not self.portfolio.allow_short:
                raise ValueError("Negative weights need short selling switched on (long-short).")
        if not 0.5 < self.confidence < 1:
            raise ValueError("Confidence must be between 50% and 100%, e.g. 0.99.")
        if self.window < 50:
            raise ValueError("The history window must be at least 50 trading days.")
        if self.portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive.")
        if self.end is not None and self.end <= self.start:
            raise ValueError("End date must be after the start date.")

    def updated(self, **changes: object) -> RiskConfig:
        """Return a copy of this config with some settings changed."""
        return replace(self, **changes)

    def weight_of(self, ticker: str) -> float:
        """The weight of one stock (equal weight when no weights were given)."""
        if self.weights is None:
            return 1.0 / len(self.tickers)
        return self.weights[self.tickers.index(ticker)]
