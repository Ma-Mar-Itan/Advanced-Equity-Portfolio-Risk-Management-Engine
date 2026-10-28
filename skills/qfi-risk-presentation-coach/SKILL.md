---
name: qfi-risk-presentation-coach
description: Plan, script, rehearse, or critique speeches for the QFI equity portfolio risk presentation, including data quality, portfolio construction, VaR, EWMA, GARCH, GJR-GARCH, backtesting, model comparison, stress testing, and technical Q&A. Use for speaker notes, talk tracks, defenses, or presentation coaching about this project; do not use for unrelated finance decks.
---

# QFI Risk Presentation Coach

Create a clear, defensible speech for the portfolio-risk deck. The audience should understand what the numbers mean, why the preferred model earned trust, where it can fail, and what decision follows.

## Start with evidence

Inspect the current deck and engine outputs before writing claims. In the QFI V2 project, prefer:

- the latest requested PowerPoint in `presentation_mockups/`;
- `report_assets/results.json` for headline metrics and tests;
- `report_assets/presentation_backtest.json` for rolling backtest evidence;
- the relevant Python modules when a method or definition is uncertain.

Do not reuse numbers from old notes when the engine output has changed. State the portfolio value, data end date, confidence level, horizon, estimation window, weighting rule, and selected model wherever they affect interpretation.

## Clarify the speaking situation

Infer the audience, time limit, and purpose from the request. If one is missing and the choice would materially change the speech, ask. Otherwise state a reasonable assumption and proceed.

Choose the emphasis by audience:

- **Executive or risk committee:** dollars, limit usage, exceptions, stress losses, concentration, actions, and model limits.
- **Quantitative or academic:** transformations, no-look-ahead design, volatility equations, parameter interpretation, test statistics, and robustness.
- **Mixed audience:** plain-language meaning first, method second, technical detail in backup slides or Q&A.

## Build one argument

Write the central message in one sentence before drafting notes. It must be supported by the current evidence, not by the desired conclusion.

Use this narrative unless the user specifies another:

1. The decision problem and portfolio being measured.
2. Data coverage and cleaning controls.
3. Portfolio return, volatility, drawdown, and market exposure.
4. Historical Simulation as the transparent baseline.
5. EWMA and GARCH as volatility-timing improvements.
6. GJR-GARCH as the asymmetric challenger or preferred model when the tests support it.
7. Backtesting evidence, including exception frequency and clustering.
8. Model comparison based on validation, not on the smallest VaR.
9. Stress losses and concentration that ordinary one-day VaR does not capture.
10. Decision, limitations, monitoring, and next action.

Read [references/qfi-talk-blueprint.md](references/qfi-talk-blueprint.md) when drafting a full speech or slide-by-slide notes.

## Explain risk without distorting it

Preserve these distinctions:

- VaR is a loss threshold at a stated confidence and horizon. It is not the maximum possible loss.
- Expected Shortfall is the average loss beyond the VaR threshold.
- Historical Simulation uses observed outcomes from the selected window; it does not guarantee the future will resemble that window.
- Volatility scaling changes the size of historical shocks, not their rank or economic cause.
- GARCH models conditional volatility; GJR-GARCH adds an asymmetric response to negative shocks.
- A backtest exception occurs when the realized loss exceeds the VaR forecast made before that day.
- Kupiec tests exception frequency. Christoffersen independence tests clustering. Conditional coverage considers both.
- A green Basel traffic-light zone does not by itself prove the model is adequate.
- Stress scenarios are conditional “what if” estimates, not forecasts or assigned probabilities.
- Strong historical performance does not remove drawdown, tail, liquidity, selection, or model risk.

Always separate facts, model estimates, assumptions, and recommendations. Disclose limitations that could change a decision.

## Narrate every chart

Use the five-part chart talk track:

1. **Orient:** name the axes, unit, period, portfolio, and model.
2. **Direct attention:** identify the line, bar, threshold, or period that matters.
3. **Read the evidence:** state one or two exact values or comparisons.
4. **Interpret carefully:** explain what the pattern means for risk or model performance.
5. **Qualify and bridge:** name the relevant limitation, then connect to the next slide.

Do not read every label or describe visible decoration. Never claim causality from a chart that only shows timing or association.

Read [references/chart-and-qa-playbook.md](references/chart-and-qa-playbook.md) for chart-specific language and defense questions.

## Write notes for speech, not prose

For each slide, provide:

- **Purpose:** one sentence describing the job of the slide.
- **Talk track:** natural spoken language, normally 60 to 130 words.
- **Visual cue:** what to point to or reveal.
- **Transition:** one sentence that creates the need for the next slide.
- **Likely question:** the most probable challenge and a short answer.

Use contractions sparingly and natural sentence lengths. Define a technical term the first time it appears. Avoid jargon clusters, inflated claims, canned enthusiasm, and lines such as “as you can see.” Do not read slide text verbatim.

## Opening and close

Open with the decision, exposure, or consequence rather than an agenda. A useful pattern is:

> “For this $X portfolio, the ordinary one-day risk estimate is manageable, but the crisis loss and concentration are much larger. This presentation shows how we measured that gap and tested whether the model deserves trust.”

Use the current numbers in place of placeholders only after verifying them.

Close by answering:

- Which model should monitor routine risk, and why?
- What does the selected model still miss?
- Which stress or concentration deserves action?
- What should management monitor, challenge, or change next?

Do not finish with only “Questions?” Leave the decision or control recommendation visible.

## Rehearse and test

Check the speech aloud, not only on the page.

- Confirm the opening reaches the decision problem within the first minute.
- Time every section and reserve meaningful time for conclusions and questions.
- Verify every number against the current engine output.
- Confirm each acronym is defined once.
- Check that every chart receives an interpretation, not merely a description.
- Remove material that does not support the central message.
- Prepare backup answers for assumptions, data provenance, look-ahead bias, window choice, confidence level, model selection, backtesting, and stress calibration.
- Test the actual presentation computer, fonts, embedded charts, contrast, and room visibility.

For the evidence behind these rules, read [references/research-foundations.md](references/research-foundations.md).

## Deliverables

Match the user’s request. Useful outputs include:

- a complete speech;
- slide-by-slide speaker notes;
- a timed outline;
- an executive and a technical version;
- a rehearsal checklist;
- a Q&A defense sheet;
- a critique of an existing talk track.

When editing a deck, preserve its design and use the presentation-authoring workflow. Keep detailed derivations in notes or backup slides unless the audience needs them on the main slide.
