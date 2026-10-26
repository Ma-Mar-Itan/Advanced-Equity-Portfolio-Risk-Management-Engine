# QFI Risk Platform

A modular Python platform for portfolio construction, market-risk measurement, model validation, and stress testing. The project includes a Streamlit dashboard and a reusable analytics package that has no dependency on the user interface.

## Features

- Cache-first market-data collection from Yahoo Finance, Stooq, Alpha Vantage, and Polygon
- Adjusted-price cleaning, calendar alignment, stale-price detection, missing-value handling, and return transformation
- Equal-weighted, custom, market-cap-weighted, inverse-volatility, and long-short portfolios
- Historical Simulation, EWMA-scaled, GARCH-scaled, and GJR-GARCH-scaled VaR
- Expected Shortfall, rolling forecasts, and multi-day risk horizons
- Kupiec, Christoffersen independence, conditional-coverage, and Basel traffic-light backtests
- Historical and hypothetical stress scenarios
- Stock- and sector-level risk attribution, hedge analysis, and portfolio optimization
- CSV and PNG exports for dashboard data and charts

## Architecture

```text
riskkit/               Analytics package; independent of Streamlit
  data/                Collection, caching, cleaning, and validation
  portfolio/           Weighting, rebalancing, value, returns, and P&L
  volatility/          Rolling, EWMA, GARCH, and GJR-GARCH models
  var/                 Historical and volatility-scaled VaR/ES
  backtest/            Statistical tests and model comparison
  stress/              Historical and hypothetical scenarios
  attribution/         Risk decomposition
  decisions/           What-if, hedging, and optimization tools
app/                   Streamlit application
  views/               Dashboard pages
  charts/              Plotly figure builders
  components/          Reusable interface components and downloads
tests/                 Offline unit and integration tests
tools/                 Data, report, slide, and demonstration utilities
data/snapshot/         Versioned offline data used by the default dashboard
```

`RiskConfig` is the shared immutable configuration object. Dashboard pages call the cached functions in `app/state.py`; those functions delegate all calculations to `riskkit`.

## Quick start

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,reports]"
streamlit run app/app.py
```

On Windows, `Start dashboard.bat` performs the initial setup and starts the application. `Run tests.bat` runs the offline test suite.

## Data sources

The dashboard works without API keys by using Yahoo Finance, Stooq, and the versioned offline snapshot. Optional providers use environment variables:

```text
ALPHAVANTAGE_API_KEY
POLYGON_API_KEY
TIINGO_API_KEY
```

Provider-specific cached files take priority over network requests. If a selected provider is unavailable, the collection pipeline records the actual fallback source rather than relabeling the data. WRDS is displayed only when an adapter and credentials are available.

Do not commit API keys, `.env` files, WRDS credentials, or local agent configuration. The repository `.gitignore` excludes these files.

## Testing

The test suite does not require network access:

```powershell
python -m pytest
```

The tests cover cleaning and alignment, portfolio arithmetic, volatility models, VaR ordering and look-ahead protection, backtesting statistics, stress scenarios, data-source fallbacks, dashboard data exports, and chart metadata.

## Reports and presentations

The repository includes optional tooling for regenerating the report and presentation assets:

```powershell
python -m tools.build_report_assets
python -m tools.build_report
python -m tools.build_deck
```

Generated intermediate files and timestamped deliverables are intentionally excluded from version control.

## Disclaimer

This software is intended for research and educational use. It is not investment advice and should not be used as the sole basis for financial decisions.
