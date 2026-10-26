# QFI V2 presentation notes

These notes are intentionally detailed and beginner-friendly. They are embedded in the PowerPoint speaker notes and repeated here for easier study.

## 1. Advanced Equity Portfolio Risk Management

I will begin with the practical purpose of this work. This presentation answers three questions. How much could this portfolio lose on an ordinary bad trading day? How do we know whether that estimate is reliable? And what should management do when the measured risk is too high?

When I say “portfolio,” I mean the complete basket of investments considered together. We measure the basket rather than each stock in isolation because gains in one position can offset losses in another. “Risk management” means measuring uncertainty, deciding how much loss the organization is prepared to accept, and agreeing in advance what action follows when a boundary is crossed. It does not mean that we can predict tomorrow perfectly. The word “quant” is simply short for quantitative: the conclusions are based on data, mathematical models, and statistical tests rather than judgment alone.

The portfolio is valued at $10 million, so every dollar-risk figure in the presentation is expressed for that amount. If the same portfolio weights were applied to $20 million, the dollar VaR would be approximately twice as large. The presentation starts with the conclusion, then shows the evidence: the portfolio results, the behavior of returns, the competing risk models, the backtests, the stress results, and finally the proposed management controls.

One warning should remain in mind throughout. Value at Risk, or VaR, is not the maximum possible loss. It is a threshold for a stated time horizon and confidence level. More extreme and prolonged losses are addressed through stress testing. With that distinction clear, I will start with the overall risk assessment and then explain why the evidence supports it.

---

## 2. Executive risk assessment

The main conclusion is that the portfolio appears manageable under the ordinary one-day risk measure, but the stress loss and the concentration of risk require management attention. Under the selected GJR-HS model, the current 99% one-day VaR is about $296,809, while Expected Shortfall is about $338,445.

The phrase “99% one-day VaR” needs to be interpreted carefully. It means the model sets a loss threshold that should be exceeded on roughly one trading day out of one hundred if the model remains appropriate. It does not mean there is 99% certainty that nothing bad will happen, and it says nothing about a full month or an extended crisis. Expected Shortfall, or ES, looks beyond the VaR boundary and asks a more severe question: on the worst one percent of days, what is the average loss? That is why ES is larger than VaR.

The model is supported by the historical validation. GJR-HS produced 34 exceptions, meaning 34 days when the realized loss exceeded the forecast VaR, compared with 31.1 expected. It passes the tests for the number and timing of exceptions at the 5% significance level. A pass does not prove that the model is true; it means the evidence is not strong enough to reject it under the stated test.

The daily result is only one part of the decision. Replaying the 2008 crisis produces a loss of about 44.1%, showing why VaR cannot be treated as a worst-case number. Tesla and Amazon also generate roughly 37% of Expected Shortfall from only about 20% of the capital. My recommendation is therefore to use GJR-HS as the primary model, keep EWMA-HS as an independent challenger, and put explicit limits around stress and concentration. On the slide, green indicates acceptable evidence, gold marks a warning or decision point, and red identifies material tail exposure. I will now show how these conclusions were obtained.

---

## 3. High returns came with equity-like drawdown and market exposure

The portfolio delivered a strong historical result: a 31.6% annualized return. That result, however, came with 21.9% annualized volatility, a maximum drawdown of 34.9%, a Sharpe ratio of 1.27, and a beta of 1.19 to the broad US equity market.

“Annualized return” expresses the compounded historical growth rate as a per-year figure; it is a description of the sample, not a forecast. “Volatility” measures how widely returns move in both directions. A volatility of 21.9% does not mean the portfolio lost 21.9%; it means the daily movements, converted to an annual scale, were substantial. “Maximum drawdown” is the largest fall from a previous peak to a later low. A 34.9% drawdown means an investor who entered at the peak temporarily lost about one-third before the portfolio recovered. The Sharpe ratio compares return above the risk-free rate with volatility. A higher value is generally preferable, but the 1.27 result remains sample-dependent and does not remove crash risk.

Beta describes market sensitivity. A beta of 1.19 means the portfolio historically moved by about 1.19% for each 1% market move, on average under the fitted relationship. Its 0.90 correlation with SPY means the portfolio and the market usually moved in the same direction. Correlation measures the strength of co-movement; beta also reflects the relative size of the movements.

The evidence covers ten large US equities, initially weighted equally and rebalanced monthly, with a current net asset value, or NAV, of $10 million. Equal weighting means each stock starts near 10% of capital, while monthly rebalancing resets the holdings toward those targets. The sample runs from 04 June 2012 to 16 October 2026 and contains 3,614 daily return observations. Returns are built from adjusted closing prices, which account for stock splits and distributions. Short missing gaps may be filled using the last known price, but that process is bounded so a long trading suspension is not mistaken for normal activity.

Every historical forecast uses only information available at that date. This “point-in-time” rule avoids look-ahead bias, where later information makes a past model appear unrealistically successful. The dashboard, report, and presentation are generated from the same calculations, which makes the result reproducible. Before selecting a model, however, we must first understand the shape and behavior of the returns.

---

## 4. Returns are fat-tailed; volatility clusters after shocks

The return data do not behave like independent draws from a stable bell curve. Extreme observations occur more often than a simple normal-distribution assumption would suggest, and large movements tend to arrive in groups rather than being evenly spread through time.

Volatility is the typical size of a return movement. “Volatility clustering” means calm days tend to be followed by calm days, while turbulent days tend to be followed by turbulent days. Risk therefore changes over time. Skewness measures asymmetry. Negative skew means unusually large downside moves are more common or more severe than equally large upside moves. Kurtosis measures the thickness of the tails of the return distribution. Under the convention used here, a normal bell curve has kurtosis of three. A higher value indicates that extreme observations occur more frequently than the normal model implies.

The chart gives an intuitive view of this behavior. It groups days by the direction and size of the current market move, then measures the average absolute movement over the next five days. A taller bar after a large negative shock means bad news tends to create more subsequent volatility than equally large good news. That asymmetry matters because a model that treats positive and negative shocks identically may react too slowly after a selloff.

GARCH, short for Generalized Autoregressive Conditional Heteroskedasticity, is a family of models in which today’s volatility depends on recent shocks and recent volatility. GJR-GARCH adds an asymmetry term. Its gamma parameter measures whether negative shocks have a larger effect than positive shocks of the same size. Persistence measures how slowly a volatility shock fades. Here, the estimated half-life is about 20.7 trading days, meaning the model expects half of the shock’s effect to remain after roughly that period. AIC is a comparison score that balances fit against complexity; lower is better when the models use the same data.

These findings support a model that adjusts to the current volatility regime and recognizes downside asymmetry. They also justify comparing several models rather than trusting one unscaled history of past losses.

---

## 5. GJR-HS earns primary-model status; EWMA-HS is the challenger

The model-selection result is to use GJR-HS as the primary risk model, EWMA-HS as the challenger, and plain Historical Simulation as a transparent benchmark. This hierarchy reflects the evidence without pretending that any single model is unquestionably correct.

Historical Simulation, abbreviated HS, takes the last 500 daily portfolio returns, sorts them from best to worst, and reads the loss at the required tail percentile. It is easy to audit and explain, but it gives a return from almost two years ago the same importance as yesterday’s return. EWMA stands for Exponentially Weighted Moving Average. It gives greater weight to recent squared returns so that the volatility estimate responds to changing market conditions. Its memory parameter is lambda, written λ. A value of 0.94 means older shocks fade gradually rather than disappearing immediately.

GARCH-HS goes one step further. It divides each historical shock by the volatility estimated for the day on which it occurred. The remaining scaled shock is called a standardized residual. This makes a shock from a calm period more comparable with a shock from a turbulent period. The model then finds the historical tail of these standardized shocks and rescales it using today’s forecast volatility. GJR-HS uses the same filtered-historical-simulation idea but allows negative returns to increase forecast volatility more than positive returns. It also includes mean reversion, meaning unusually high volatility is expected to move gradually toward a longer-run level rather than remain high forever.

The hierarchy has a governance purpose. The primary model drives official reporting and limit monitoring. The challenger is maintained separately so that it can reveal drift or blind spots in the primary result. The benchmark remains available because a simple answer is often useful when reviewing a more complicated one. We should investigate material disagreement between these models rather than automatically averaging it away. With that structure established, the next slide compares today’s risk estimates.

---

## 6. Current one-day VaR and Expected Shortfall

For the selected GJR-HS model, the current 99% one-day VaR is $296,809, and Expected Shortfall is $338,445.

Value at Risk is a loss threshold. A VaR of roughly $297,000 means the model expects a larger one-day loss on about one trading day in one hundred. It does not mean that $297,000 is the maximum possible loss. Expected Shortfall asks what happens after that line has already been crossed. It is the average loss within the worst one percent of outcomes, so it should be larger than VaR. On the chart, each gold ES bar therefore sits above the corresponding green VaR bar; if it did not, the calculation or the labeling would need to be investigated.

The four models do not produce identical answers because they treat history differently. Plain Historical Simulation is currently higher because its 500-day window includes volatile observations at their original scale. A filtered model first normalizes each historical shock by the volatility at that time and then rescales it to today’s volatility environment. The gap between the model estimates is called model dispersion. It is not nuisance noise to hide; it is direct evidence that the risk number depends on the method chosen.

The percentage results are useful when comparing portfolios of different sizes. The dollar results are more useful for judging limit consumption, liquidity, and management action. Dollar risk scales approximately in proportion to NAV when the portfolio weights remain unchanged. The important conclusion is therefore not only that the selected estimate is about $297,000, but also that the stated model, horizon, confidence level, and portfolio value are inseparable from that number. The next slide shows how much the answer moves when some of those assumptions change.

---

## 7. Parameter choice is a material source of model risk

A VaR number is incomplete unless we state the model, confidence level, time horizon, and historical window. The sensitivity analysis shows why: across the tested specifications, estimated VaR ranges from 1.34% to 3.34% of NAV. That difference is large enough to change whether a portfolio appears comfortably within a limit or close to breaching it.

The confidence level determines how far into the loss tail we look. Moving from 95% to 99% or 99.5% deliberately focuses on rarer and more severe outcomes. A quantile is simply a cutoff in an ordered distribution. For 99% VaR, the relevant cutoff is located in the worst one percent of portfolio outcomes. The estimation window determines how much history is used: 250 trading days is roughly one year, 500 is roughly two years, and 750 is roughly three years.

There is no free choice. A short window reacts quickly to a new market regime but contains fewer observations, which makes a deep-tail estimate less stable. A longer window provides more observations but may combine an old regime with the present one. The highlighted base case uses 99% confidence and a 500-day window, producing a VaR of about 2.97% of NAV. “Sensitivity analysis” means changing one assumption at a time and observing how much the result moves. The wide range on this slide shows that parameter uncertainty is economically important, not merely technical.

This is one form of model risk: the possibility that the selected method, assumptions, data, or implementation produce a misleading decision. Governance should therefore define the risk measure precisely. A policy should say “99% one-day GJR-HS with a 500-day estimation window,” rather than simply referring to “VaR.” Even a precisely defined number must then be tested against outcomes that actually occurred, which is the purpose of the backtest.

---

## 8. The VaR forecast adapts, but exceptional losses still break through

This chart is the core validation picture because it compares the model’s forecast with the loss that occurred on the following trading day. The gray line is realized profit and loss, or P&L: the actual daily gain or loss. The green line is plotted below zero because it represents the negative VaR boundary. Each red point marks a day when the realized loss fell below that boundary. We call such a day a breach or an exception.

The forecasts are “ex ante,” meaning they were made before the outcome. At every date, the VaR estimate uses only information that would have been available at that time. This avoids look-ahead bias and creates a fair test. The slide displays the most recent 750 trading days so the pattern remains readable, while the formal statistics on the next slide use the full 3,114-day forecast sample.

One red point does not by itself show that a 99% model has failed. At that confidence level, occasional exceptions are expected. What matters is whether the total number is plausible and whether the exceptions arrive independently. If breaches cluster together, the model may be reacting too slowly to a new volatility regime. The visual also shows that the VaR boundary expands during turbulent periods and contracts during calmer periods. That adaptation is what a conditional-volatility model is designed to do.

The chart should therefore be read as a sequence, not as a search for a single dramatic date. We want a risk boundary that moves with conditions, produces roughly the expected number of exceptions, and does not repeatedly miss losses in clusters. The next slide translates those three ideas into formal statistical tests.

---

## 9. GJR-HS is the only model that passes all 99% tests

The backtest result is clear: all four models produce a broadly plausible total number of exceptions, but only GJR-HS also makes their timing statistically acceptable under the stated 5% rule. That is why GJR-HS ranks first.

Backtesting means recreating the exercise at each historical date: estimate tomorrow’s VaR using only the information available today, observe tomorrow’s actual return, and record whether the loss crossed the boundary. With 3,114 forecasts at 99% confidence, the expected number of exceptions is 3,114 multiplied by 1%, or 31.14.

The Kupiec test asks whether the total number of breaches is plausible. This is called unconditional coverage. The Christoffersen independence test asks whether one breach makes another breach unusually likely on the next day; in other words, whether the exceptions cluster. The conditional-coverage test combines the count and timing questions. Each test reports a p-value. A p-value measures how surprising the observed result would be if the tested model property were correct. Under the 5% decision rule, a value below 0.05 leads us to reject that property. It is not the probability that the model itself is true.

GJR-HS records 34 exceptions compared with 31.1 expected. Its independence p-value is 0.056, only slightly above 0.05. That is a pass, but a narrow one, and it should be monitored rather than celebrated. HS, EWMA-HS, and GARCH-HS pass the count test but fail the independence test because their breaches are too clustered.

Rank one therefore means “best under this declared rule and historical sample,” not “perfect.” The usual statistical scorecard also counts a one-dollar exceedance and a very large exceedance in the same way. The next slide addresses that limitation by examining the severity of the exceptions.

---

## 10. The largest exceptions are economically meaningful

The largest GJR-HS exception was economically significant. On 11 June 2020, the portfolio lost about $585,671 against a VaR forecast of about $259,011, so the realized loss exceeded the boundary by approximately $326,659.

The table is ordered by the size of the realized loss rather than by date. “Loss” is the amount the portfolio actually lost. “VaR” is the loss boundary estimated before that trading day. “Excess” is the difference between the two. Severity matters because a standard traffic-light count treats every exception as one event, whether the loss exceeds VaR by one dollar or by more than $300,000.

The major exceptions occur around the COVID selloff, inflation and interest-rate repricing, the 2018 volatility shock, and the April 2025 tariff shock. These labels provide market context; they are not proof that one headline caused the entire portfolio movement. A diversified portfolio can react simultaneously to broad market beta, sector exposure, interest rates, and company-specific news. The careful conclusion is that the largest misses coincide with periods of broad market disruption, not that a single event has been identified as the sole cause.

“Economic significance” means the dollar amount is large enough to affect capital, liquidity, or management decisions even if the statistical count remains acceptable. A production process should therefore review every exception promptly, reconcile the prices, identify the position-level contributors, and determine whether the event reflects market movement, a data error, model lag, or a portfolio change. That process is called root-cause analysis: it explains why the breach occurred rather than merely logging it.

Even a model that passes this one-day backtest is not designed to describe an extended crisis. For that question, we need stress testing.

---

## 11. Crisis losses overwhelm ordinary daily VaR

Daily VaR describes the boundary of ordinary one-day tail risk. Stress testing asks a different question: what would happen to the current portfolio under a specified severe event? The result is more alarming than the daily metric. Replaying the 2008 crisis produces an estimated portfolio loss of about 44.1%, while the COVID replay produces about 34.6%.

A stress scenario is a deliberately harsh market path or shock applied to the portfolio. A historical scenario replays price behavior from a known period, such as the global financial crisis or the COVID crash. A hypothetical scenario applies designed shocks, such as a sharp market fall, a sector decline, higher volatility, or stronger correlations. Correlation measures the degree to which assets move together. In a crisis, correlations often rise, so positions that appeared diversified in normal conditions can fall together when protection is most needed.

The stress losses are much larger than the roughly 3% one-day VaR because they answer different questions. Daily VaR covers one trading day at a specified confidence level. The historical stress replays an extended crisis path. Stressed VaR, shown separately, recalculates the one-day risk measure using a turbulent historical window and is about 9.6%; it remains a model estimate and should not be confused with the full scenario loss.

No scenario is a prediction. It is a controlled “what if” question. The longer red bars on the chart represent larger losses, but the appropriate comparison is not simply with daily VaR. Management must compare the scenario loss with risk appetite, available capital, and the ability to raise cash without forced selling. The 44.1% result is therefore a decision point: either accept that exposure explicitly, reduce it, or hedge it and rerun the scenario. To decide where an adjustment would be most effective, we next identify which positions create the risk.

---

## 12. Risk is more concentrated than capital

The concentration result is that equal money weights do not create equal risk contributions. Tesla and Amazon each hold about 10% of the capital, but Tesla contributes about 20% of Expected Shortfall and Amazon about 17%. Together, they create roughly 37% of the portfolio’s tail risk from only about 20% of the money.

A portfolio weight is the fraction of capital invested in a position. An Expected Shortfall contribution is the portion of total ES attributed to that position after accounting for both its own volatility and how it moves with the rest of the portfolio. This is why risk weight and capital weight can differ. A stock can have an ordinary capital allocation yet still be a concentration if it is unusually volatile or strongly correlated with the other holdings.

The calculation uses the idea of marginal risk: the approximate change in total portfolio risk caused by adding a small amount to a position. Euler attribution is the mathematical method that converts those marginal effects into components that add back to total portfolio risk. The details of the formula are less important for this audience than its accounting property: the contributions can be read as a complete decomposition of Expected Shortfall rather than as unrelated scores.

The chart compares the green capital bar with the gold ES-contribution bar for each stock. When the gold bar is much taller, the stock is producing more tail risk than its money allocation suggests. The portfolio also receives an estimated 38% diversification benefit, meaning the combined risk is materially lower than the sum of the positions considered alone. That benefit is valuable but not guaranteed; it can shrink when correlations rise during a crisis.

The implication is not that Tesla or Amazon must automatically be sold. It is that any hedge, position limit, or reallocation should focus on the sources of risk rather than only on nominal weights. The next slide shows the approximate effect of two possible responses.

---

## 13. The analytics translate into concrete actions

The analytics translate into concrete management options. The first is a broad-market hedge; the second is a constrained reallocation of the portfolio. In the model results, a beta-neutral SPY hedge reduces current VaR by about 59%, while the optimized allocation reduces Expected Shortfall from roughly $330,000 to $229,000.

A hedge is a position intended to offset losses elsewhere. An index hedge uses a broad market instrument such as SPY rather than selling each stock separately. Beta measures sensitivity to broad market movements. A beta near 1.2 means the portfolio has historically moved by about 1.2% for each 1% market move, on average under the fitted relationship. “Beta-neutral” means choosing a hedge size intended to bring the portfolio’s net market beta close to zero.

That description also states the limitation. A beta-neutral hedge reduces estimated market-direction exposure, but it does not remove company-specific risk, nonlinear behavior, overnight gaps, or basis risk. Basis risk is the possibility that the hedge and the portfolio do not move together as expected. A 59% estimated reduction is therefore a modeled result, not a guarantee.

Optimization means choosing weights to minimize or maximize a stated objective subject to constraints. Here the objective is lower Expected Shortfall. The result is in-sample, meaning the same historical data were used to estimate and evaluate the solution. That can make the improvement look better than it will be in the future. Reallocation also creates turnover, meaning trading from the old weights to the new ones, and turnover creates transaction costs and potential market impact. Liquidity matters because even a mathematically attractive trade can be impractical if it cannot be executed without moving the price.

These figures are decision aids, not trade instructions. Before implementation, the proposal should include position limits, transaction costs, liquidity and shorting constraints, out-of-sample testing, and independent approval. The final control step is to convert the analysis into named limits, owners, and escalation actions.

---

## 14. Proposed limits turn analytics into governance

The thresholds on this slide are proposed controls for discussion; they are not presented as already approved policy. Their purpose is to turn risk information into a repeatable response.

A risk limit is a measurable boundary that triggers a defined action. A complete limit names the metric, model, threshold, owner, monitoring frequency, and escalation procedure. An early-warning level is the amber boundary that prompts investigation before the hard limit is crossed. Escalation means notifying a named decision-maker and taking a predefined action rather than relying on informal judgment after the fact.

For daily market risk, the proposed measure is 99% one-day GJR-HS with a 500-day window. The warning level is 3.0% of NAV and the escalation level is 3.5%. The current reading is 2.97%, so it remains green but sits close to the warning boundary. For stress risk, the warning level is 35% and escalation begins at 40%. The current worst scenario is 44.1%, so this control is red and requires an explicit decision to accept, hedge, or reduce the exposure.

For concentration, review begins when one position contributes more than 18% of Expected Shortfall, with escalation above 20%. Tesla contributes approximately 19.9%, placing it in amber and very close to escalation. For model health, a formal p-value below 0.05 triggers escalation, while a value below 0.10 deserves attention. The GJR-HS independence p-value is approximately 0.056, so the model passes the formal 5% rule but remains amber under the proposed warning rule.

These controls do not remove the limitations of the analysis. The historical sample may contain survivorship or selection bias; the results remain sensitive to the sample and parameters; square-root-of-time scaling can be misleading over longer horizons; and historical scenarios cannot represent every future crisis. Prices and corporate actions should also be reconciled independently. With those boundaries stated, I will close with the operating model and the decisions requested from the committee.

---

## 15. Recommendation: adopt a primary–challenger model

The recommendation is to adopt GJR-HS as the primary monitoring model, retain EWMA-HS as the challenger, and require stress testing and risk attribution as mandatory complements. The central message is not that one number is perfect. It is that a controlled system is stronger than any single estimate.

The primary model is the official method used for routine reporting and limit monitoring. The challenger is a separately specified model used to question the primary result. A material gap between the two should be investigated rather than automatically averaged away. The proposed operating cycle is daily risk measurement, a documented review after every exception, a monthly comparison of primary and challenger models, and a quarterly risk-committee review. A material portfolio change should trigger an immediate review rather than waiting for the next scheduled meeting.

Four decisions follow from the results. First, management must decide whether the 44.1% crisis loss is consistent with its risk appetite. If not, the exposure should be reduced or hedged and the scenario rerun. Second, Tesla’s approximately 19.9% share of Expected Shortfall should be reviewed, with a deliberate choice to reduce, hedge, or accept the concentration. Third, the committee should approve the exact limits, owners, and escalation deadlines. A number without an owner and an action is only a report, not a control. Fourth, every future exception should be independently reconciled and preserved in an audit trail containing the data, model version, forecast, realized loss, identified cause, and management decision.

This framework does not predict the future and it should not be presented as doing so. Its value is that it measures ordinary risk consistently, tests whether the model behaved credibly, examines severe but plausible losses, identifies where the risk comes from, and connects the evidence to a decision. The final recommendation is therefore a governed process: one primary model, one challenger, explicit stress and concentration controls, and a clear escalation path when the evidence moves outside the agreed boundaries.

---
