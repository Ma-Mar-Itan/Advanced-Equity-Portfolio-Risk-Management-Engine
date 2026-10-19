"""Module 7 in one call: run every scenario on today's portfolio and rank them.

Output table: one row per scenario with its loss, worst day, stressed VaR and ES.
For hypothetical volatility / correlation shocks the 'loss' is their stressed 1-day VaR.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from riskkit.config import RiskConfig
from riskkit.data.collect import MarketData
from riskkit.portfolio.construction import Portfolio
from riskkit.stress import historical, hypothetical
from riskkit.stress.scenarios import LIBRARY
from riskkit.var.engine import VarResult


@dataclass(frozen=True)
class StressResults:
    """Everything the Stress page shows."""

    table: pd.DataFrame                       # one row per scenario, worst first
    by_stock: dict[str, pd.Series]            # scenario -> each stock's loss (share of value)
    replays: dict[str, historical.Replay]
    betas: pd.Series
    basel_svar: float
    basel_svar_end: pd.Timestamp
    value: float


def run_stress(cfg: RiskConfig, md: MarketData, p: Portfolio, base: VarResult) -> StressResults:
    """Run the historical replays and the hypothetical shocks chosen in the config."""
    spec, value, conf = cfg.stress, float(p.value.iloc[-1]), cfg.confidence
    weights = p.current_weights
    assets = md.prices[weights.index].pct_change()
    bench = md.benchmark.pct_change()
    beta = historical.betas(assets.dropna(), bench, cfg.window)
    sectors = pd.Series({t: md.profiles[t].sector for t in weights.index})
    history = historical.todays_portfolio_history(weights, assets, bench, beta)
    rows, by_stock, replays = [], {}, {}

    for name in spec.historical:
        sc = LIBRARY[name]
        rep = historical.replay(sc, weights, assets, bench, beta)
        svar, ses = historical.stressed_var_es(history, sc.dates[1], conf)
        note = sc.story + (f"; stand-in for {', '.join(rep.proxied)}" if rep.proxied else "")
        rows.append(dict(scenario=name, kind="Historical", loss=rep.loss, worst_day=rep.worst_day,
                         stressed_var=svar, stressed_es=ses, note=note))
        by_stock[name], replays[name] = rep.by_stock, rep

    def add_shock(name: str, losses: pd.Series, note: str) -> None:
        rows.append(dict(scenario=name, kind="Hypothetical", loss=float(losses.sum()), worst_day=float(losses.sum()),
                         stressed_var=np.nan, stressed_es=np.nan, note=note))
        by_stock[name] = losses

    for s in spec.market_shocks:
        add_shock(f"Market {s:+.0%}", hypothetical.market_shock(weights, beta, s), "each stock moves beta x shock")
    add_shock(f"{spec.sector} {spec.sector_shock:+.0%}",
              hypothetical.sector_shock(weights, beta, sectors, spec.sector, spec.sector_shock, spec.spillover),
              f"spillover to other stocks {spec.spillover:.0%}")
    if spec.custom_shocks:
        add_shock("Your scenario", hypothetical.custom_shock(weights, dict(spec.custom_shocks)), "your own moves")

    vvar, ves = hypothetical.volatility_shock(base.scenarios, spec.vol_multiplier, conf)
    rows.append(dict(scenario=f"Volatility x{spec.vol_multiplier:g}", kind="Hypothetical", loss=vvar,
                     worst_day=vvar, stressed_var=vvar, stressed_es=ves, note="stressed 1-day VaR"))
    ratio = hypothetical.correlation_shock_ratio(assets.dropna().iloc[-cfg.window:], weights, spec.corr_blend)
    rows.append(dict(scenario=f"Correlation spike ({spec.corr_blend:.0%} to 1)", kind="Hypothetical",
                     loss=base.var_1d * ratio, worst_day=base.var_1d * ratio, stressed_var=base.var_1d * ratio,
                     stressed_es=base.es_1d * ratio, note=f"diversification lost: risk x{ratio:.2f}"))

    table = pd.DataFrame(rows).sort_values("loss", ascending=False).reset_index(drop=True)
    table.insert(0, "rank", np.arange(1, len(table) + 1))
    table["loss_usd"] = table["loss"] * value
    svar, when = historical.worst_window_var(history, conf)
    return StressResults(table, by_stock, replays, beta, svar, when, value)


def by_sector(losses: pd.Series, sectors: pd.Series) -> pd.Series:
    """A scenario's loss added up by sector."""
    return losses.groupby(sectors.reindex(losses.index)).sum().sort_values(ascending=False)
