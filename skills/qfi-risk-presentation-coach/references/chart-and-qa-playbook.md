# Chart and Q&A playbook

Use this reference when writing chart narration, rehearsing a defense, or preparing backup slides.

## Chart talk tracks

### Growth or portfolio value

- Orient: starting value, ending date, rebalance rule, and whether the chart shows securities or the portfolio.
- Read: identify the broad trend and one major interruption.
- Interpret: distinguish historical compounding from a forecast.
- Qualify: mention selection or survivorship bias when the universe uses today’s large stocks historically.

### Drawdown

- Orient: zero is the previous peak; negative values show the decline from that peak.
- Read: state the maximum drawdown and the period in which it occurred.
- Interpret: explain the temporary capital loss an investor would have experienced.
- Qualify: drawdown depends on the observed path and does not bound the next crisis.

### Return distribution

- Orient: horizontal axis is daily return or P&L; vertical axis is frequency or density.
- Read: compare the empirical tails with the reference distribution.
- Interpret: explain why fat tails and skew weaken a simple Gaussian assumption.
- Qualify: the observed sample remains finite and regime-dependent.

### Volatility series

- Orient: identify annualized or daily units and the competing models.
- Read: point to a calm regime, a spike, and the speed of decay.
- Interpret: explain responsiveness, persistence, and asymmetry.
- Qualify: a higher forecast is not automatically better; backtesting determines whether timing improves calibration.

### VaR and Expected Shortfall

- Orient: state model, confidence, horizon, window, and portfolio value.
- Read: give the VaR threshold and ES tail average.
- Interpret: explain why ES exceeds VaR.
- Qualify: VaR is not the worst loss and does not cover liquidity or every regime change.

### Backtest exceptions

- Orient: actual P&L and the forecast available before each day.
- Read: state actual versus expected exceptions and identify clusters.
- Interpret: separate coverage from independence.
- Qualify: p-values do not prove a model true, and tail samples remain small.

### Stress scenarios

- Orient: today’s weights, scenario type, shock window, and loss units.
- Read: name the worst scenario and compare it with current daily VaR.
- Interpret: explain which exposure or correlation pattern drives severity when supported by attribution.
- Qualify: the scenario is conditional and not a forecast or assigned probability.

### Risk contribution

- Orient: compare capital weight with VaR or ES contribution.
- Read: identify positions whose risk share materially exceeds their money weight.
- Interpret: explain the role of volatility and correlation.
- Qualify: contribution estimates depend on the selected model and current dependence structure.

## Core defense questions

### Portfolio and data

- Why these ten stocks? Address project scope and selection bias separately.
- Why equal weights? Explain the baseline’s transparency and the effect of alternative weighting schemes.
- Are prices adjusted for splits and dividends? Point to the adjusted-close pipeline.
- How were trading dates, missing observations, and stale prices handled?
- What is the data end date and source? Was the run online or from a saved snapshot?
- Does any feature use future information? Explain point-in-time fitting and rolling forecast construction.

### VaR design

- Why 99% confidence and a 500-day window?
- Why use log returns for modeling but simple returns for portfolio aggregation where applicable?
- Why does 10-day VaR use square-root scaling? What path dependence does that miss?
- Why not rely on Historical Simulation alone?
- Why is Expected Shortfall necessary if VaR is already reported?

### Volatility models

- What does lambda 0.94 mean in EWMA?
- What do alpha, beta, persistence, and half-life mean in GARCH?
- What does the GJR leverage parameter mean?
- Why does a lower AIC not settle model selection?
- How often are the GARCH models refitted, and why?

### Backtesting

- What counts as an exception?
- Why can a model pass Kupiec and fail Christoffersen?
- Why can a green traffic-light result coexist with a failed independence test?
- How many tail observations support the p-values?
- Were test thresholds chosen before seeing the result?

### Stress and decisions

- Why were these historical periods selected?
- How are missing histories handled for securities that did not trade during an old crisis?
- Are hypothetical market, volatility, correlation, and sector shocks internally consistent?
- Why does the stress loss exceed one-day VaR by so much?
- What does a proposed hedge fail to protect?
- Would rebalancing or optimization create turnover, liquidity, tax, or estimation risk?

## Answer pattern

Use four parts for difficult questions:

1. Answer directly.
2. Name the evidence or method.
3. State the assumption or limitation.
4. Explain the control, sensitivity, or next test.

Example:

> “The selected model passes the current frequency and independence tests. That supports its use for daily monitoring, but it does not prove the model is correct in every regime. We therefore retain a challenger, review every exception, and use stress testing for losses outside the one-day VaR question.”

If the evidence is unavailable, say so. Do not improvise a statistic or imply that a missing test passed.
