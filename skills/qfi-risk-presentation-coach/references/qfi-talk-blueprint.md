# QFI talk blueprint

Use this reference to draft a full speech. Verify every number against the current engine outputs.

## Recommended flow

### 1. Opening: the decision problem

State the portfolio value, the risk question, and the contrast between ordinary daily risk and severe stress. Do not open with the project phases or a definition of VaR.

Speaker goal: make the audience want an answer to “How much can this portfolio lose, how reliable is that estimate, and what should we do about it?”

### 2. Scope and portfolio

Name the ten holdings, weighting and rebalancing rule, benchmark, date range, and valuation basis. Explain that the analysis measures the combined portfolio because correlations change total risk.

Keep the stock list brief. The decision-relevant facts are portfolio size, diversification, sector exposure, and market sensitivity.

### 3. Data and cleaning

Explain adjusted prices, date alignment, missing and stale-price checks, return definition, and the source of the risk-free rate. State the data end date. Confirm that the process avoids look-ahead where relevant.

Do not narrate the code pipeline. Explain the controls that make the later risk estimates credible.

### 4. Portfolio behavior

Present return, volatility, maximum drawdown, beta, and the worst daily loss. Separate historical performance from a forecast. Acknowledge that strong returns can coexist with severe drawdowns and concentrated tail risk.

### 5. VaR baseline

Introduce Historical Simulation in one plain sentence: it ranks recent portfolio outcomes and takes the relevant loss cutoff. State confidence, horizon, and historical window with the result.

Then explain Expected Shortfall as the average loss after crossing that cutoff.

### 6. Volatility scaling

Explain the progression, not every equation:

- EWMA reacts quickly by weighting recent squared returns more heavily.
- GARCH models persistent volatility and mean reversion.
- GJR-GARCH adds the stronger volatility response that often follows negative equity returns.

If showing parameters, interpret them. A persistence value describes decay. A positive leverage parameter supports asymmetry. A lower AIC supports relative fit but does not prove decision adequacy.

### 7. Backtesting

Define the forecast timing before discussing results: each day’s VaR must use only information available before that day.

Explain three questions:

1. Is the total number of exceptions plausible?
2. Do exceptions arrive independently or cluster?
3. Does the model pass both conditions jointly?

Do not treat the Basel zone as a complete validation result. Discuss Kupiec and Christoffersen evidence together.

### 8. Model comparison

Compare the models on validation and behavior, not on which produces the smallest number. Address:

- exception count and expected count;
- independence and conditional coverage;
- average VaR and variability;
- responsiveness in volatile periods;
- interpretability and governance role.

Name a primary model only when the current evidence supports it. Keep a challenger and a transparent baseline.

### 9. Stress and concentration

Explain that stress testing asks a different question from one-day VaR. State the scenario, portfolio held fixed today, estimated loss, and whether the scenario is historical or hypothetical.

Then show concentration. Equal money weights do not create equal risk contributions. Use the largest Expected Shortfall contributors to explain where management action would have the most effect.

### 10. Decision and close

End with a small number of decisions:

- the primary and challenger models;
- the monitoring frequency and exception review;
- any hedge, reallocation, or concentration limit worth considering;
- the limitations that prevent automatic trading or overconfidence.

Close by restating the risk-management judgment, not by repeating the phase list.

## Timing patterns

Adapt these proportions to the actual time limit:

- Opening and scope: about 10%.
- Data, portfolio, and method: about 30%.
- VaR, volatility models, and backtesting: about 35%.
- Stress, concentration, decision, and limitations: about 25%.

For a short executive briefing, compress method slides and preserve the backtest, stress, and decision sections. For a defense or academic presentation, expand assumptions, no-look-ahead controls, model equations, diagnostics, and robustness.

## Useful transitions

- Data to portfolio: “With the inputs aligned, the next question is what risk the combined portfolio actually produced.”
- Portfolio to VaR: “Drawdown describes the historical path; VaR turns that history into a repeatable daily threshold.”
- HS to scaling: “The baseline is transparent, but it treats an old calm day like yesterday. The filtered models change that volatility clock.”
- Models to backtesting: “A plausible model is not enough. We now test the forecasts against losses that occurred later.”
- Backtesting to stress: “Passing a one-day backtest does not make VaR a crisis-loss ceiling. Stress testing addresses that gap.”
- Stress to action: “The stress result identifies the size of the problem; attribution identifies where an intervention can change it.”

## Speech-note template

```text
Slide [number]: [title]

Purpose
[What this slide must establish.]

Talk track
[Natural spoken explanation with verified numbers.]

Visual cue
[Exact chart feature to indicate.]

Transition
[Why the next slide is needed.]

Likely question
Q: [Challenge]
A: [Direct answer, assumption, and limitation.]
```
