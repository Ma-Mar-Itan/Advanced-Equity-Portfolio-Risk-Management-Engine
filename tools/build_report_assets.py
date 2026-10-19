"""Compute every number, table and figure used in the written report.

Writes report_assets/results.json and report_assets/fig*.png. Run from the V2 folder:
    python -m tools.build_report_assets          (online)
    python -m tools.build_report_assets offline  (saved prices only)
The report builder (tools/build_report.py) reads these files, so the report always
matches the latest data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch

from app import theme
from app.charts.backtest import exception_timeline
from app.charts.data import growth_chart, growth_of_one_dollar
from app.charts.extras import share_chart
from app.charts.portfolio import distribution_chart, drawdown_chart
from app.charts.stress import loss_chart
from app.charts.var import rolling_chart, scenario_histogram
from app.charts.volatility import comparison_chart, leverage_chart
from riskkit.attribution.euler import active_risk, attribution_table, diversification
from riskkit.attribution.scenarios import build_scenarios
from riskkit.backtest.compare import comparison_table
from riskkit.backtest.traffic_light import rolling_zone
from riskkit.config import VAR_MODELS, CleaningSpec, PortfolioSpec, RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data
from riskkit.decisions.hedge import best_hedges
from riskkit.decisions.optimize import compare_splits, min_es_weights
from riskkit.portfolio.construction import build_portfolio, simple_asset_returns
from riskkit.portfolio.drawdown import drawdown_episodes, drawdown_series
from riskkit.portfolio.performance import benchmark_comparison, summary_stats
from riskkit.stress.engine import run_stress
from riskkit.var.engine import all_models_today, confidence_window_grid, rolling_var
from riskkit.volatility.analysis import fit_all, leverage_effect, regime_table, volatility_regimes
from riskkit.volatility.base import annualize

OUT = Path(__file__).resolve().parents[1] / "report_assets"
WIDTH, HEIGHT = 1000, 430


SERIF = "Times New Roman, Liberation Serif, serif"


def save(fig: go.Figure, name: str, height: int = HEIGHT, right: int = 30, left: int = 70) -> None:
    """Write one figure as a print-ready PNG: white background, fixed size, Times everywhere."""
    fig.update_layout(width=WIDTH, height=height, paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(family=SERIF, size=15, color="#222222"),
                      legend=dict(font=dict(family=SERIF, size=14)),
                      margin=dict(l=left, r=right, t=40, b=55))
    fig.update_xaxes(tickfont=dict(family=SERIF, size=14), title_font=dict(family=SERIF, size=15))
    fig.update_yaxes(tickfont=dict(family=SERIF, size=14), title_font=dict(family=SERIF, size=15))
    fig.update_annotations(font_family=SERIF)
    try:
        fig.write_image(OUT / name, scale=2)
    except Exception as exc:  # kaleido needs Google Chrome; keep the previous image if it fails
        print(f"Figure {name} not updated ({exc.__class__.__name__}): install Google Chrome and kaleido.")


def records(df: pd.DataFrame) -> list[dict]:
    """A table as JSON-safe rows (dates as text, NaN as None)."""
    clean = df.copy()
    for c in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[c]):
            clean[c] = clean[c].dt.strftime("%d %b %Y")
    return json.loads(clean.to_json(orient="records", double_precision=6))


def data_section(md, cd, cfg) -> dict:
    """Descriptive statistics of each stock's daily log returns."""
    r = cd.returns
    rows = []
    for t in r.columns:
        x = r[t]
        rows.append({"stock": t, "name": md.profiles[t].name, "sector": md.profiles[t].sector,
                     "ann_return": float(np.expm1(x.mean() * 252)), "ann_vol": float(x.std() * np.sqrt(252)),
                     "skew": float(stats.skew(x)), "kurt": float(stats.kurtosis(x, fisher=False)),
                     "min": float(x.min()), "max": float(x.max())})
    return {"start": f"{r.index[0]:%d %B %Y}", "end": f"{r.index[-1]:%d %B %Y}", "days": len(r),
            "filled": cd.count("fill"), "stale": cd.count("stale"), "checks_passed": sum(c.passed for c in cd.checks),
            "checks": len(cd.checks), "stocks": rows}


def diagnostics(r: pd.Series) -> dict:
    """Normality and volatility-clustering tests on the portfolio's daily log returns."""
    jb = stats.jarque_bera(r)
    lb = acorr_ljungbox(r, lags=[10], return_df=True)
    lb2 = acorr_ljungbox(r**2, lags=[10], return_df=True)
    arch = het_arch(r, nlags=5)
    return {"mean": float(r.mean()), "sd": float(r.std()), "skew": float(stats.skew(r)),
            "kurt": float(stats.kurtosis(r, fisher=False)), "jb": float(jb.statistic), "jb_p": float(jb.pvalue),
            "lb_r": float(lb["lb_stat"].iloc[0]), "lb_r_p": float(lb["lb_pvalue"].iloc[0]),
            "lb_r2": float(lb2["lb_stat"].iloc[0]), "lb_r2_p": float(lb2["lb_pvalue"].iloc[0]),
            "arch_lm": float(arch[0]), "arch_p": float(arch[1])}


def main() -> None:
    """Compute everything and write it out."""
    OUT.mkdir(exist_ok=True)
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    cd = clean_market_data(md, cfg)
    p = build_portfolio(cd, md, cfg)
    r = p.log_returns
    res: dict = {"value": cfg.portfolio_value, "confidence": cfg.confidence, "window": cfg.window}

    # Data and portfolio
    res["data"] = data_section(md, cd, cfg)
    res["risk_free_source"] = md.origin["risk-free"]
    clipped = clean_market_data(md, cfg.updated(cleaning=CleaningSpec(winsor_method="quantile", winsor_lower=0.01,
                                                                      winsor_upper=0.99)))
    days = clipped.log.loc[clipped.log["step"] == "winsorize", "date"]
    busiest = days.dt.to_period("M").value_counts()
    res["winsor"] = {"total": int(len(days)), "year_2020": int((days.dt.year == 2020).sum()),
                     "busiest_month": busiest.index[0].strftime("%B %Y"), "busiest_count": int(busiest.iloc[0])}
    s, b = summary_stats(p, md.risk_free), benchmark_comparison(p, md.benchmark)
    res["portfolio"] = {**s, **b}
    res["drawdowns"] = records(drawdown_episodes(p.value, 3))
    schemes = {"Equal weight, monthly rebalancing": PortfolioSpec(), "Equal weight, buy and hold": PortfolioSpec(rebalance="none"),
               "Market-cap weight, monthly": PortfolioSpec(scheme="market_cap"),
               "Inverse-volatility weight, monthly": PortfolioSpec(scheme="inverse_vol")}
    rows = []
    for name, spec in schemes.items():
        q = summary_stats(build_portfolio(cd, md, cfg.updated(portfolio=spec)), md.risk_free)
        rows.append({"scheme": name, "ann_return": q["annual return"], "ann_vol": q["annual volatility"],
                     "sharpe": q["sharpe"], "mdd": q["max drawdown"]})
    res["schemes"] = rows
    res["diagnostics"] = diagnostics(r)

    # Volatility
    fits = fit_all(r, cfg.volatility)
    res["vol_today"] = {n: float(annualize(f.next_day)) for n, f in fits.items()}
    res["vol_10d"] = {n: float(annualize(f.forecast[-1])) for n, f in fits.items()}
    res["garch"] = {n: fits[n].params for n in ("GARCH", "GJR-GARCH")}
    z = fits["GJR-GARCH"].std_residuals(r)
    res["resid"] = {"kurt_raw": float(stats.kurtosis(r, fisher=False)), "kurt_z": float(stats.kurtosis(z, fisher=False)),
                    "lb_z2": float(acorr_ljungbox(z**2, lags=[10], return_df=True)["lb_stat"].iloc[0]),
                    "lb_z2_p": float(acorr_ljungbox(z**2, lags=[10], return_df=True)["lb_pvalue"].iloc[0])}
    lev = leverage_effect(r)
    res["leverage"] = records(lev.assign(move=lev["move"].astype(str)))
    res["regimes"] = records(regime_table(r, volatility_regimes(fits["GJR-GARCH"].sigma)))

    # VaR
    today = all_models_today(r, cfg)
    res["var_today"] = [{"model": v.model, "var": v.var_1d, "es": v.es_1d, "var10": v.var_h, "es10": v.es_h} for v in today]
    grid = confidence_window_grid(r, cfg, cfg.var.model)
    res["var_grid"] = {"rows": list(grid.index), "cols": list(grid.columns), "values": grid.to_numpy().tolist()}
    rollings = {m: rolling_var(r, cfg, m) for m in VAR_MODELS}

    # Backtests
    # Robustness: the same backtest started after 750 days of history, as in the brief's example.
    brief_start = r.index[750]
    res["brief_start"] = f"{brief_start:%d %B %Y}"
    for c, key in ((0.99, "bt99"), (0.95, "bt95")):
        roll_c = rollings if c == cfg.confidence else {m: rolling_var(r, cfg, m, c) for m in VAR_MODELS}
        res[key] = records(comparison_table(roll_c, c, cfg.portfolio_value))
        res[key + "_brief"] = records(comparison_table(roll_c, c, cfg.portfolio_value, start=brief_start))
    res["brief_days"] = int((rollings["HS"].index >= brief_start).sum())
    res["bt_days"] = len(rollings["HS"])
    res["bt_start"] = f"{rollings['HS'].index[0]:%d %B %Y}"
    res["yellow_days"] = {m: int((rolling_zone(df["actual"] > df["var"])["zone"] != "green").sum())
                          for m, df in rollings.items()}

    # Stress
    base = next(v for v in today if v.model == cfg.var.model)
    st_res = run_stress(cfg, md, p, base)
    res["stress"] = records(st_res.table[["rank", "scenario", "kind", "loss", "worst_day", "stressed_var", "stressed_es"]])
    res["basel_svar"] = st_res.basel_svar
    res["basel_svar_end"] = f"{st_res.basel_svar_end:%B %Y}"
    res["betas"] = st_res.betas.round(3).to_dict()

    # Attribution and decisions
    sc = build_scenarios(cd, md, p, cfg)
    sectors = pd.Series({t: md.profiles[t].sector for t in sc.weights.index})
    att = attribution_table(sc, sectors)
    res["attribution"] = records(att)
    res["diversification"] = diversification(sc)
    res["active"] = active_risk(sc, p.returns, md.benchmark)
    res["hedges"] = records(best_hedges(sc, cfg.benchmark).head(4))
    new = min_es_weights(sc, 0.25)
    res["optimizer"] = {"weights": new[new > 1e-3].round(4).to_dict(),
                        "compare": records(compare_splits(sc, new, simple_asset_returns(cd, cfg.cleaning.return_type)))}

    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=float))

    # Figures
    prices = md.prices.loc[pd.Timestamp(cfg.start):].dropna()
    save(growth_chart(growth_of_one_dollar(prices)), "fig01_growth.png", 460, right=130)
    save(drawdown_chart(drawdown_series(p.value)), "fig02_drawdown.png", 360)
    save(distribution_chart(p.returns).update_xaxes(range=[-8, 8]), "fig03_distribution.png", 380)
    save(comparison_chart(fits, True), "fig04_vol_models.png", 400)
    save(leverage_chart(lev), "fig05_leverage.png", 380)
    gjr = next(v for v in today if v.model == "GJR-HS")
    save(scenario_histogram(gjr), "fig06_scenarios.png", 380)
    window = {m: rollings[m].loc["2020-01":"2020-12"] for m in ("HS", "GJR-HS")}
    fig = rolling_chart(window, "GJR-HS", cfg.portfolio_value).update_traces(visible=True)
    fig.update_traces(selector=dict(name="Loss beyond VaR"), name="Loss beyond GJR-HS VaR")
    hs = window["HS"]
    beyond = hs["actual"] > hs["var"]
    fig.add_scatter(x=hs.index[beyond], y=-hs["actual"][beyond] * cfg.portfolio_value, mode="markers",
                    name="Loss beyond HS VaR", marker=dict(color="#161616", size=9, symbol="circle-open", line=dict(width=2)))
    save(fig.update_layout(legend=dict(y=1.12)), "fig07_rolling_2020.png", 420)
    save(exception_timeline(rollings, "GJR-HS"), "fig08_exceptions.png", 300, left=110)
    stress_fig = loss_chart(st_res.table)
    stress_fig.update_xaxes(range=[-1.2e6, st_res.table["loss_usd"].max() * 1.18])
    save(stress_fig, "fig09_stress.png", 480, left=200, right=40)
    save(share_chart(att, "ES"), "fig10_risk_share.png", 380)
    print(f"Report assets written to {OUT}")


if __name__ == "__main__":
    main()
