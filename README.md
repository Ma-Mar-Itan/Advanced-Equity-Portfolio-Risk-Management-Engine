# QFI Risk Platform V2

Rebuilt from scratch, one module at a time. See PLAN.md for the full plan and
slide_notes.md / QFI_V2_slides.pptx for the presentation as it grows.

## Run it on Windows: double-click

- **Start dashboard.bat**: opens the dashboard in your browser (the first run sets everything up, a few minutes).
- **Update data, report and slides.bat**: downloads the latest prices and rebuilds the charts, the Word report and the deck.
- **Run tests.bat**: runs the unit tests.

Python 3.11+ must be installed (python.org, tick "Add python.exe to PATH").

## Run it from a terminal (Windows, from this V2 folder)

One-time setup (a few minutes):

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

Then:

    python -m tools.module1_demo      # Module 1: download prices, print summary, save chart
    python -m tools.module2_demo      # Module 2: clean, run the checks, save chart
    python -m tools.module3_demo      # Module 3: build the portfolio, compare weighting schemes, save chart
    python -m tools.module4_demo      # Module 4: fit the four volatility models, save charts
    python -m tools.module5_demo      # Module 5: VaR and ES for the four models, quick breach count, charts
    python -m tools.module6_demo      # Module 6: backtest and rank the four VaR models, save chart
    python -m tools.module7_demo      # Module 7: run every stress scenario, save chart
    python -m tools.module8_demo      # Module 8: risk by stock, what-if, hedges, optimizer, save chart
    python -m tools.build_deck        # rebuild QFI_V2_slides.pptx from slide_notes.md
    python -m tools.build_report_assets  # recompute every number, table and figure for the report
    python -m tools.build_report      # rebuild QFI_V2_report.docx from those results
    python -m pytest tests            # unit tests (no internet needed)
    streamlit run app/app.py          # the dashboard

Optional: put a free Tiingo key (tiingo.com) in a one-line file `tiingo_key.txt`
next to this README, or in the TIINGO_API_KEY environment variable. Without it,
Yahoo is the only source.

## Dashboard pages (one per module)

1 Data · 2 Cleaning · 3 Portfolio · 4 Volatility · 5 VaR & ES · 6 Backtesting · 7 Stress ·
8 Risk sources · 9 Decisions. Every setting lives in one RiskConfig object, so a change on
any page (stocks, weights, model, confidence...) flows through every other page.

## Layout

    riskkit/   the maths engine (never imports Streamlit)
    app/       the Streamlit dashboard (thin: inputs -> engine -> charts)
    tests/     unit tests, one file per module
    tools/     demo scripts and the slide builder
