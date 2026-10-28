"""Input widgets for the pages. Each function draws controls and returns what the user chose.

Keeping widgets here keeps the pages short: a page calls one function and gets back
plain values (or a new settings object), never raw widget state.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from app import state
from riskkit.config import CleaningSpec, PortfolioSpec, RiskConfig, StressSpec, VarSpec, VolatilitySpec
from riskkit.data.sources import dashboard_source_names


def data_settings(cfg: RiskConfig) -> dict | None:
    """The Data page's settings form. Returns the changed settings when 'Load' is pressed."""
    with st.form("data_settings", border=False):
        c1, c2, c3, c4, c5 = st.columns([3.2, 1, 1, 1, 0.8], vertical_alignment="bottom")
        tickers = c1.multiselect(
            "Stocks",
            options=list(cfg.tickers),
            default=list(cfg.tickers),
            accept_new_options=True,
            help="Type any Yahoo ticker and press Enter, or use the search box below to find one by company name.",
        )
        start = c2.date_input("From", cfg.start, min_value=date(2000, 1, 1))
        sources = list(dashboard_source_names())
        current_source = cfg.source if cfg.source in sources else "yahoo"
        source = c3.selectbox(
            "Price source",
            sources,
            index=sources.index(current_source),
            format_func=lambda s: s.replace("_", " ").title(),
            help="Provider-specific saved files are preferred. When a provider is unavailable or "
            "needs credentials, the saved public Yahoo snapshot is used and identified as "
            "Yahoo in the results. WRDS appears only when it is configured.",
        )
        benchmark = c4.text_input("Benchmark", cfg.benchmark, help="SPY tracks the S&P 500 (the whole US market).")
        offline = c5.toggle("Offline", cfg.offline, help="Use saved prices only.")
        if st.form_submit_button("Load data", type="primary"):
            return dict(
                tickers=tuple(t.upper() for t in tickers),
                start=start,
                source=source,
                benchmark=benchmark.strip().upper(),
                offline=offline,
            )
    return None


def stock_search() -> str | None:
    """Search any company by name; returns the ticker to add when 'Add' is pressed."""
    c1, c2, c3 = st.columns([2.2, 2.6, 0.8], vertical_alignment="bottom")
    query = c1.text_input("Find any stock in the world", placeholder="e.g. Nestle, Toyota, LVMH")
    hits = state.search(query) if query else None
    if hits is None or hits.empty:
        c2.selectbox("Matches", ["(type a name to search)" if not query else "(no matches, or offline)"], disabled=True)
        return None
    labels = [f"{r.symbol}  ·  {r.name}  ·  {r.exchange}" for r in hits.itertuples()]
    pick = c2.selectbox("Matches", range(len(labels)), format_func=lambda i: labels[i])
    return hits.iloc[pick]["symbol"] if c3.button("Add", width="stretch") else None


WINSOR_LABELS = {"none": "Off", "quantile": "Percentiles", "sigma": "Mean ± k std", "cap": "Fixed cap"}
CALENDAR_LABELS = {"union": "Any stock traded", "common": "All stocks traded", "benchmark": "Benchmark's days"}
FILL_LABELS = {"ffill": "Repeat last price", "interpolate": "Straight line", "drop": "Drop the day"}


def _pick(label: str, options: dict[str, str], current: str, help_text: str | None = None) -> str:
    """A selectbox over option codes, showing friendly labels."""
    codes = list(options)
    return st.selectbox(label, codes, index=codes.index(current), format_func=options.get, help=help_text)


def cleaning_controls(spec: CleaningSpec) -> CleaningSpec | str:
    """Render cleaning controls and return validated settings or an error message."""
    st.markdown("**Dates and gaps**")
    calendar = _pick("Keep a day when", CALENDAR_LABELS, spec.calendar)
    fill = _pick("Missing price", FILL_LABELS, spec.fill_method)
    fill_limit = st.number_input("Fill at most this many days in a row", 0, 30, spec.fill_limit)
    stale_days = st.number_input("Stale after this many unchanged days (0 = off)", 0, 60, spec.stale_days)
    stale_action = st.radio(
        "Stale prices",
        ["flag", "remove"],
        index=["flag", "remove"].index(spec.stale_action),
        horizontal=True,
        format_func={"flag": "Flag only", "remove": "Remove"}.get,
    )
    st.markdown("**Returns**")
    kind = st.radio(
        "Return type",
        ["log", "simple"],
        index=["log", "simple"].index(spec.return_type),
        horizontal=True,
        format_func=str.capitalize,
    )
    method = _pick(
        "Winsorize",
        WINSOR_LABELS,
        spec.winsor_method,
        "Clip extreme days. Off by default: crashes are real and a risk model should see them.",
    )
    lower, upper, k, cap = spec.winsor_lower, spec.winsor_upper, spec.winsor_k, spec.winsor_cap
    if method == "quantile":
        c1, c2 = st.columns(2)
        cut_low = c1.number_input("Clip worst %", 0.0, 10.0, lower * 100, 0.05, format="%.2f")
        cut_high = c2.number_input("Clip best %", 0.0, 10.0, (1 - upper) * 100, 0.05, format="%.2f")
        lower, upper = cut_low / 100, 1 - cut_high / 100
    elif method == "sigma":
        k = st.slider("k (standard deviations)", 2.0, 12.0, k, 0.5)
    elif method == "cap":
        cap = st.slider("Largest allowed daily move", 0.02, 0.50, cap, 0.01, format="%.2f")
    expression = st.text_area(
        "Custom formula on returns `r` (optional)",
        spec.custom_expression,
        height=68,
        placeholder="e.g.  clip(r, -0.2, 0.2)   or   r - mean(r)",
        help="Use r plus: abs, sqrt, log, log1p, exp, sign, clip(x, lo, hi), mean, median, "
        "std, rolling_mean(x, n), rolling_std(x, n), lag(x, n), where(cond, a, b), np.",
    )
    try:
        return CleaningSpec(
            calendar,
            fill,
            int(fill_limit),
            int(stale_days),
            stale_action,
            kind,
            method,
            lower,
            upper,
            k,
            cap,
            expression,
        )
    except ValueError as exc:
        return str(exc)


SCHEME_LABELS = {"equal": "Equal", "custom": "Custom", "market_cap": "By company size", "inverse_vol": "By calmness"}
REBALANCE_LABELS = {
    "none": "Never (buy and hold)",
    "daily": "Daily",
    "monthly": "Monthly",
    "quarterly": "Quarterly",
    "yearly": "Yearly",
}


def weight_editor(cfg: RiskConfig, allow_short: bool) -> tuple[tuple[float, ...] | None, str | None]:
    """An editable table of custom weights in %. Returns (weights as fractions, error message).

    What the user typed is kept separately from the (possibly rescaled) weights, so editing one
    cell never makes the other cells jump around.
    """
    store = f"typed_weights_{'_'.join(cfg.tickers)}"
    if store not in st.session_state:
        st.session_state[store] = (
            [w * 100 for w in cfg.weights] if cfg.weights else [100 / len(cfg.tickers)] * len(cfg.tickers)
        )
        st.session_state[store + "_v"] = 0
    table = pd.DataFrame({"Stock": list(cfg.tickers), "Weight %": st.session_state[store]})
    edited = st.data_editor(
        table,
        hide_index=True,
        width="stretch",
        key=f"{store}_{st.session_state[store + '_v']}",
        disabled=["Stock"],
        column_config={
            "Weight %": st.column_config.NumberColumn(format="%.2f", step=0.5, min_value=None if allow_short else 0.0)
        },
    )
    typed = edited["Weight %"].fillna(0.0).tolist()
    if typed != st.session_state[store]:
        st.session_state[store], st.session_state[store + "_v"] = typed, st.session_state[store + "_v"] + 1
        st.rerun()
    raw = np.array(typed) / 100
    total = raw.sum()
    rescale = st.toggle("Rescale to 100% automatically", True)
    st.caption(f"Total entered: {total:.2%}  ·  long {raw[raw > 0].sum():.0%}  ·  short {abs(raw[raw < 0].sum()):.0%}")
    if abs(total) < 1e-9:
        return None, "The weights add up to zero."
    if rescale:
        raw = raw / total
    elif abs(total - 1) > 1e-6:
        return None, f"Weights add up to {total:.2%}; make them 100% or switch rescaling on."
    return tuple(round(float(x), 12) for x in raw), None


def portfolio_controls(cfg: RiskConfig) -> dict | str:
    """Render portfolio controls and return validated configuration changes."""
    spec = cfg.portfolio
    st.markdown("**Stocks**")
    tickers = st.multiselect(
        "Stocks in the portfolio",
        list(cfg.tickers),
        list(cfg.tickers),
        accept_new_options=True,
        label_visibility="collapsed",
        help="Type any Yahoo ticker and press Enter (e.g. SAP.DE, 7203.T). The Data page also "
        "has a search by company name.",
    )
    tickers = tuple(t.strip().upper() for t in tickers)
    if not tickers:
        return "Pick at least one stock."
    if tickers != cfg.tickers:
        return dict(tickers=tickers)
    st.markdown("**How the money is split**")
    scheme = st.radio(
        "Weighting",
        list(SCHEME_LABELS),
        index=list(SCHEME_LABELS).index(spec.scheme),
        format_func=SCHEME_LABELS.get,
        horizontal=True,
        label_visibility="collapsed",
    )
    allow_short, weights, max_weight, lookback = spec.allow_short, cfg.weights, spec.max_weight, spec.vol_lookback
    if scheme == "custom":
        allow_short = st.toggle(
            "Allow short positions (long-short)",
            spec.allow_short,
            help="A negative weight bets against a stock: it gains when the stock falls.",
        )
        weights, error = weight_editor(cfg, allow_short)
        if error:
            return error
    elif scheme in ("market_cap", "inverse_vol"):
        max_weight = st.slider(
            "Maximum weight per stock",
            0.05,
            1.0,
            spec.max_weight,
            0.05,
            format="%.2f",
            help="1.00 = no cap. The excess goes to the other stocks.",
        )
        if scheme == "inverse_vol":
            lookback = st.select_slider("Measure calmness over (trading days)", [21, 63, 126, 252], spec.vol_lookback)
        else:
            st.caption(
                "Uses dated shares outstanding available at each rebalance. If that history is unavailable, "
                "the calculation stops instead of inserting today's share count into the past."
            )
    st.markdown("**Managing it over time**")
    rebalance = _pick(
        "Rebalance to the target split",
        REBALANCE_LABELS,
        spec.rebalance,
        "Between rebalances the weights drift: winners become bigger slices.",
    )
    cost = st.number_input(
        "Trading cost (basis points of amount traded)",
        0.0,
        100.0,
        spec.cost_bps,
        1.0,
        help="1 basis point = 0.01%. 5-10bp is typical for large US stocks.",
    )
    st.markdown("**Money and dates**")
    value = st.number_input("Portfolio value ($)", 10_000.0, 1e11, cfg.portfolio_value, 1_000_000.0, format="%.0f")
    basis = st.radio(
        "That value is",
        ["today", "start"],
        index=["today", "start"].index(spec.value_basis),
        format_func={"today": "what we hold today", "start": "what we invested at the start"}.get,
        key="portfolio_value_basis_v2",
    )
    c1, c2 = st.columns(2)
    start = c1.date_input("From", cfg.start, min_value=date(2000, 1, 1))
    end = c2.date_input("To", cfg.end, min_value=date(2000, 1, 2), help="Empty = up to the latest day")
    try:
        new_spec = PortfolioSpec(scheme, rebalance, allow_short, max_weight, int(lookback), float(cost), basis)
        return dict(portfolio=new_spec, weights=weights, portfolio_value=float(value), start=start, end=end or None)
    except ValueError as exc:
        return str(exc)


def volatility_controls(cfg: RiskConfig, series_options: list[str]) -> tuple[VolatilitySpec | str, dict]:
    """Render volatility controls and return model and display settings."""
    spec = cfg.volatility
    st.markdown("**What to measure**")
    series = st.selectbox("Series", series_options, help="The whole portfolio, or any single stock")
    yearly = st.toggle("Show as yearly volatility", True, help="Daily volatility x sqrt(252)")
    st.markdown("**Models**")
    window = st.select_slider("Rolling window (trading days)", [21, 42, 63, 126, 252], spec.rolling_window)
    lam = st.slider(
        "EWMA lambda (memory)",
        0.80,
        0.995,
        spec.ewma_lambda,
        0.005,
        format="%.3f",
        help="Higher = longer memory, smoother. 0.94 is the RiskMetrics standard.",
    )
    dist = st.radio(
        "GARCH shock shape",
        ["normal", "t"],
        index=["normal", "t"].index(spec.garch_dist),
        horizontal=True,
        format_func={"normal": "Normal", "t": "Fat-tailed (t)"}.get,
    )
    mean = st.radio(
        "GARCH mean return",
        ["zero", "constant"],
        index=["zero", "constant"].index(spec.garch_mean),
        horizontal=True,
        format_func=str.capitalize,
    )
    horizon = st.slider("Forecast horizon (days)", 1, 60, spec.horizon)
    view = {"series": series, "yearly": yearly}
    try:
        return VolatilitySpec(int(window), float(lam), dist, mean, int(horizon)), view
    except ValueError as exc:
        return str(exc), view


VAR_LABELS = {
    "HS": "Plain history (HS)",
    "EWMA-HS": "History scaled by EWMA",
    "GARCH-HS": "History scaled by GARCH",
    "GJR-HS": "History scaled by GJR-GARCH",
}


def var_controls(cfg: RiskConfig) -> dict | str:
    """Render VaR controls and return validated configuration changes."""
    spec = cfg.var
    st.markdown("**Model**")
    model = st.radio(
        "VaR model",
        list(VAR_LABELS),
        index=list(VAR_LABELS).index(spec.model),
        format_func=VAR_LABELS.get,
        label_visibility="collapsed",
    )
    st.markdown("**How sure, how much history**")
    confidence = st.select_slider(
        "Confidence",
        [0.90, 0.95, 0.975, 0.99, 0.995, 0.999],
        cfg.confidence,
        format_func=lambda c: f"{c:.1%}",
        help="99% = the loss we expect to beat 99 days in 100",
    )
    window = st.select_slider("Window (past trading days used)", [100, 250, 500, 750, 1000, 1500], cfg.window)
    st.markdown("**Longer horizon**")
    horizon = st.slider("Horizon (days)", 2, 60, spec.horizon)
    method = st.radio(
        "Method",
        ["sqrt", "overlapping"],
        index=["sqrt", "overlapping"].index(spec.horizon_method),
        format_func={"sqrt": "1-day × √days (Basel)", "overlapping": "Real multi-day stretches"}.get,
    )
    refit = st.select_slider(
        "Rolling VaR: refit GARCH every (days)",
        [21, 63, 126, 252],
        spec.refit_every,
        help="More often = more faithful but slower. Only past data is ever used.",
    )
    try:
        return dict(
            confidence=float(confidence), window=int(window), var=VarSpec(model, int(horizon), method, int(refit))
        )
    except ValueError as exc:
        return str(exc)


def backtest_controls(cfg: RiskConfig, first_day, last_day, default_day=None) -> tuple[dict | str, dict]:
    """Render backtesting controls, including shared VaR settings."""
    st.markdown("**Model to inspect**")
    model = st.radio(
        "Model",
        list(VAR_LABELS),
        index=list(VAR_LABELS).index(cfg.var.model),
        format_func=VAR_LABELS.get,
        label_visibility="collapsed",
    )
    confidence = st.select_slider(
        "Confidence",
        [0.95, 0.975, 0.99, 0.995],
        cfg.confidence if cfg.confidence in (0.95, 0.975, 0.99, 0.995) else 0.99,
        format_func=lambda c: f"{c:.1%}",
    )
    window = st.select_slider(
        "VaR window (days)", [250, 500, 750, 1000], cfg.window if cfg.window in (250, 500, 750, 1000) else 500
    )
    st.markdown("**Test settings**")
    significance = st.select_slider(
        "Test significance",
        [0.01, 0.05, 0.10],
        0.05,
        format_func=lambda s: f"{s:.0%}",
        help="A test fails when its p-value is below this. 5% is standard.",
    )
    start = st.date_input(
        "Backtest from",
        default_day or first_day,
        min_value=first_day,
        max_value=last_day,
        help="Default: the first day with a full VaR window. The brief's example (first 750 days for estimation, "
        "the rest for testing) starts around late May 2015 for the default portfolio.",
    )
    view = {"significance": significance, "start": start}
    try:
        from dataclasses import replace

        return dict(confidence=float(confidence), window=int(window), var=replace(cfg.var, model=model)), view
    except ValueError as exc:
        return str(exc), view


def stress_controls(cfg: RiskConfig, sectors: list[str]) -> StressSpec | str:
    """Render stress-test controls and return validated settings."""
    from riskkit.stress.scenarios import LIBRARY

    spec = cfg.stress
    st.markdown("**Real crises to replay**")
    hist = st.multiselect("Historical scenarios", list(LIBRARY), list(spec.historical), label_visibility="collapsed")
    st.markdown("**Market falls**")
    market = st.multiselect(
        "Market moves (each stock moves beta × this)",
        [-0.03, -0.05, -0.10, -0.15, -0.20, -0.30, -0.40],
        list(spec.market_shocks),
        format_func=lambda s: f"{s:+.0%}",
    )
    st.markdown("**Volatility and correlation**")
    vol = st.slider("Volatility multiplied by", 1.0, 5.0, spec.vol_multiplier, 0.25)
    corr = st.slider(
        "Correlation spike: move correlations towards 1 by",
        0.0,
        1.0,
        spec.corr_blend,
        0.05,
        format="%.2f",
        help="1.00 = everything moves together; diversification disappears",
    )
    st.markdown("**Sector shock**")
    sector = st.selectbox("Sector", sectors, sectors.index(spec.sector) if spec.sector in sectors else 0)
    shock = st.slider("Sector move", -0.50, 0.20, spec.sector_shock, 0.01, format="%.2f")
    spill = st.slider(
        "Spillover to other stocks",
        0.0,
        1.0,
        spec.spillover,
        0.05,
        format="%.2f",
        help="Share of the sector move passed to every other stock, scaled by its beta",
    )
    st.markdown("**Your own scenario**")
    custom = dict(spec.custom_shocks)
    table = pd.DataFrame({"Stock": list(cfg.tickers), "Move %": [custom.get(t, 0.0) * 100 for t in cfg.tickers]})
    edited = st.data_editor(
        table,
        hide_index=True,
        width="stretch",
        disabled=["Stock"],
        key="custom_shocks",
        column_config={"Move %": st.column_config.NumberColumn(format="%.1f", step=1.0)},
    )
    moves = tuple(
        (stock, float(move) / 100)
        for stock, move in zip(edited["Stock"], edited["Move %"].fillna(0), strict=True)
        if move
    )
    try:
        return StressSpec(
            tuple(hist),
            tuple(sorted(market, reverse=True)),
            float(vol),
            float(corr),
            sector,
            float(shock),
            float(spill),
            moves,
        )
    except ValueError as exc:
        return str(exc)
