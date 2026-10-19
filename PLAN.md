# QFI Risk Platform V2: Build Plan

Source of truth: QFI brief "#3 Advanced Equity Portfolio Risk Management" (13 pages).
The old project (`../qfi-risk-platform`) is a reference only; nothing there is modified.

## Ground rules
- `riskkit/` is the maths engine: plain Python, **never imports Streamlit**.
- Every calculation is a small pure function (data in, result out) with a plain-English docstring.
- One `RiskConfig` object (tickers, weights, dates, value, confidence, window, data source) is passed around.
- One interface per family: every **price source** looks the same, every **volatility model** looks the same,
  so the code above them doesn't care which one it gets.
- Streamlit pages are thin (read inputs -> call engine -> draw). Over ~80 lines = logic has leaked.
- Theme copied unchanged from the old project (config.toml, theme.py, style.css, fonts, UI kit).

## Folder layout
```
V2/
  riskkit/                    # the engine (no Streamlit)
    config.py                 # RiskConfig
    data/
      sources/base.py         # PriceSource interface: fetch(ticker, start, end) -> prices
      sources/yahoo.py        # Yahoo Finance (global, default)
      sources/tiingo.py       # Tiingo (second source, free key)
      search.py               # find any ticker worldwide by name
      cache.py                # save downloads locally so we don't re-download
      fx.py                   # convert non-USD stocks into USD
      reference.py            # index, sector, market cap, risk-free rate
      cleaning.py             # align dates, gaps, stale prices, winsorize, cleaning log
      returns.py              # simple and log returns
      validation.py           # the brief's validation checks
    portfolio/                # weights, value & P&L, rebalancing, drawdown, performance
    volatility/               # base.py (VolModel), rolling, ewma, garch (GARCH + GJR)
    var/                      # historical, vol-scaled, horizon (1d/10d), rolling VaR
    backtest/                 # exceptions, kupiec, christoffersen, traffic light, comparison
    stress/                   # scenarios.yaml, historical replay, hypothetical, stressed VaR
    extras/                   # whichever extras we approve (see below)
  app/                        # Streamlit layer: app.py, theme, kit, charts/, pages/
  tests/                      # one test file per engine module
  slide_notes.md              # grows module by module
  slides_assets/              # chart images for the deck
```

## Modules (core = everything the brief asks for)
| # | Module | Brief phase | Main outputs |
|---|--------|-------------|--------------|
| 0 | Setup: folder, RiskConfig, theme port | - | config object, themed empty app |
| 1 | Data collection | Phase 1 | prices (Yahoo + Tiingo), ticker search, FX to USD, index, sector, market cap, risk-free rate, cache |
| 2 | Data cleaning + returns | Phase 2 | clean price & return matrices, cleaning log, validation checks |
| 3 | Portfolio | Phase 3 | equal / custom / market-cap / long-short weights; rebalancing; value, P&L, returns; drawdown; benchmark |
| 4 | Volatility | Phases 2, 5, 6, 7 | rolling, EWMA (lambda input), GARCH(1,1), GJR-GARCH; leverage effect; std. residuals; regimes chart |
| 5 | VaR & ES | Phases 4-7 | HS + EWMA/GARCH/GJR-scaled HS; 250/500/750; 95/99/99.5%; 1d & 10d; rolling VaR |
| 6 | Backtesting + model comparison | Phases 8, 9 | exceptions, Kupiec, Christoffersen (ind. + cc), Basel traffic light, ranking table |
| 7 | Stress testing | Phase 10 | 2008, COVID, 2022 inflation, 2023 banking, tech selloff; market -5/-10/-20%, vol x2, correlation spike, sector shock; stressed VaR/ES; ranking |
| 8+ | Approved extras | beyond brief | see below |
| - | Dashboard | Dashboard reqs | built as we go: **every module gets its own page** the moment it lands (see below) |

Unit tests are written alongside each module (brief deliverable).

## Dashboard: one page per module (decided Oct 18)
Each module ships with its page, with full control over that module's options.
| Page | Module | Controls |
|------|--------|----------|
| 1 Data | 1 | stocks (any ticker, search by name), start date, source, benchmark, offline, re-download |
| 2 Cleaning | 2 | calendar, fill rule + limit, stale threshold + action, log/simple returns, winsorizing (percentiles / k-sigma / cap), custom formula on `r` |
| 3 Portfolio | 3 | weights (equal / custom / market cap / long-short), value, rebalancing |
| 4 Volatility | 4 | rolling window, EWMA lambda, GARCH / GJR outputs |
| 5 VaR & ES | 5 | confidence, window, model, horizon |
| 6 Backtesting | 6 | model, confidence; exceptions, Kupiec, Christoffersen, traffic light, ranking |
| 7 Stress | 7 | scenario picker, custom shocks |
| 8+ Extras | 8+ | risk by stock/sector, what-if, hedge, optimizer |

## Extras from the old project
Chosen (Oct 18): **Where risk comes from** and **Decision tools**. Second data source: **Tiingo**.
Not rebuilt: the other groups below.

- **Where risk comes from:** risk by position and by sector (Euler/component VaR), active risk vs benchmark.
- **Decision tools:** what-if trade, best single hedge, minimum-risk optimizer, liquidity.
- **More VaR models:** normal (parametric), Cornish-Fisher, Monte Carlo, EVT, confidence bands on VaR.
- **Advanced validation/stress:** loss-function scoring + Diebold-Mariano, ES backtest, Basel capital, reverse stress, sensitivity heatmap, backtest power.
- **Advanced volatility:** DCC correlations, hidden-Markov regimes, HAR, range-based vol, model diagnostics.

## Data sources (checked Oct 2026)
- **Yahoo Finance (yfinance 1.7):** global coverage, ticker search, no key. Unofficial; rate-limits bursts -> cache + throttle.
- **Tiingo (free key):** 30+ years adjusted daily prices, 500 symbols/month, 1,000 requests/day. Official API, mostly US.
- Considered and rejected as defaults: Stooq (needs a key since Mar 2026), Alpha Vantage (25 calls/day, adjusted data is premium),
  Massive/Polygon free (under 5 years of history: too short for 2008 replay).

## Status (Oct 18, 2026)
All modules built, each with its dashboard page, unit tests (56 passing) and slides (25 in QFI_V2_slides.pptx):
0 Setup · 1 Data · 2 Cleaning · 3 Portfolio · 4 Volatility · 5 VaR & ES · 6 Backtesting · 7 Stress ·
8A Risk sources · 8B Decisions (what-if, best hedge, optimizer).
Still to do: first live run on Windows (Yahoo download), the written report (brief deliverable).
