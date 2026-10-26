"""Shared dashboard configuration and cached analytics services."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from riskkit.attribution.scenarios import Scenarios, build_scenarios
from riskkit.config import VAR_MODELS, CleaningSpec, RiskConfig
from riskkit.data.collect import MarketData, collect_market_data
from riskkit.data.pipeline import CleanData, clean_market_data
from riskkit.data.search import search_tickers
from riskkit.portfolio.construction import Portfolio, build_portfolio
from riskkit.stress.engine import StressResults, run_stress
from riskkit.var.engine import VarResult, all_models_today, confidence_window_grid, rolling_var
from riskkit.volatility.analysis import fit_all
from riskkit.volatility.base import VolFit


def config() -> RiskConfig:
    """Return the active configuration, creating the default on first access."""
    if "cfg" not in st.session_state:
        st.session_state["cfg"] = RiskConfig()
    return st.session_state["cfg"]


def update_config(**changes: object) -> None:
    """Apply configuration changes and reset custom weights when tickers change."""
    cfg = config()
    if "tickers" in changes and tuple(changes["tickers"]) != cfg.tickers:
        changes["weights"] = None
    st.session_state["cfg"] = cfg.updated(**changes)


def _data_key(cfg: RiskConfig) -> RiskConfig:
    """Return a cache key that excludes transformations applied after collection."""
    return cfg.updated(cleaning=CleaningSpec())


@st.cache_data(show_spinner="Loading prices...", max_entries=8)
def _market_data(cfg: RiskConfig) -> MarketData:
    """Collect market data once per data setting."""
    return collect_market_data(cfg)


def market_data(cfg: RiskConfig) -> MarketData:
    """Return cached market data for the active collection settings."""
    return _market_data(_data_key(cfg))


def refresh_market_data(cfg: RiskConfig) -> None:
    """Force a fresh download, then forget the cached copy."""
    collect_market_data(_data_key(cfg), refresh=True)
    _market_data.clear()


def clear_market_data() -> None:
    """Forget the in-memory market-data result before a user-requested retry."""
    _market_data.clear()


@st.cache_data(show_spinner="Cleaning...", max_entries=16)
def clean_data(cfg: RiskConfig) -> CleanData:
    """Return cleaned prices, returns, and validation results."""
    return clean_market_data(market_data(cfg), cfg)


@st.cache_data(show_spinner=False, ttl=3600)
def search(query: str) -> pd.DataFrame:
    """Yahoo ticker search (cached for an hour)."""
    return search_tickers(query)


@st.cache_data(show_spinner="Building the portfolio...", max_entries=16)
def portfolio(cfg: RiskConfig) -> Portfolio:
    """Build and cache the configured portfolio history."""
    return build_portfolio(clean_data(cfg), market_data(cfg), cfg)


def series_for(cfg: RiskConfig, name: str) -> pd.Series:
    """Return cleaned log returns for the portfolio or a selected stock."""
    if name == "Portfolio":
        return portfolio(cfg).log_returns.rename("Portfolio")
    return clean_data(cfg).returns[name]


@st.cache_data(show_spinner="Fitting volatility models...", max_entries=16)
def vol_fits(cfg: RiskConfig, name: str) -> dict[str, VolFit]:
    """Fit and cache every configured volatility model for a return series."""
    return fit_all(series_for(cfg, name), cfg.volatility)


@st.cache_data(show_spinner="Computing today's VaR...", max_entries=16)
def var_today(cfg: RiskConfig) -> list[VarResult]:
    """Return current VaR and Expected Shortfall for every model."""
    return all_models_today(portfolio(cfg).log_returns, cfg)


@st.cache_data(show_spinner="Computing VaR for every past day (refitting models)...", max_entries=8)
def var_rolling(cfg: RiskConfig) -> dict[str, pd.DataFrame]:
    """Return look-ahead-safe rolling VaR and Expected Shortfall forecasts."""
    r = portfolio(cfg).log_returns
    return {m: rolling_var(r, cfg, m) for m in VAR_MODELS}


@st.cache_data(show_spinner=False, max_entries=16)
def var_grid(cfg: RiskConfig) -> pd.DataFrame:
    """Return current VaR across the supported confidence levels and windows."""
    return confidence_window_grid(portfolio(cfg).log_returns, cfg, cfg.var.model)


@st.cache_data(show_spinner="Running stress tests...", max_entries=16)
def stress(cfg: RiskConfig) -> StressResults:
    """Run and cache the configured stress scenarios."""
    base = next(r for r in var_today(cfg) if r.model == cfg.var.model)
    return run_stress(cfg, market_data(cfg), clean_data(cfg), portfolio(cfg), base)


@st.cache_data(show_spinner="Building scenarios...", max_entries=16)
def scenarios(cfg: RiskConfig) -> Scenarios:
    """Return stock-level scenarios used for risk attribution."""
    return build_scenarios(clean_data(cfg), market_data(cfg), portfolio(cfg), cfg)


def apply_custom_weights(weights: tuple[float, ...]) -> None:
    """Switch the portfolio to these custom weights and forget weights typed earlier on the Portfolio page."""
    from dataclasses import replace

    for key in [k for k in st.session_state if str(k).startswith("typed_weights_")]:
        del st.session_state[key]
    cfg = config()
    st.session_state["cfg"] = cfg.updated(
        weights=weights, portfolio=replace(cfg.portfolio, scheme="custom", allow_short=False)
    )
