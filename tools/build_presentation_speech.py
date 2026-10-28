from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUTPUT = Path("deliverables/QFI_Presentation_Speech_20_Minutes.docx")


SLIDES = [
    (
        "Slide 1  Advanced Equity Portfolio Risk Management",
        "Good morning. This project asks a practical question: if we hold a ten-stock equity portfolio worth ten million dollars today, how much could we lose on a difficult day, how much confidence should we place in that estimate, and what should we do when the risk becomes too large? The main daily measure is Value at Risk, or VaR. At 99 percent confidence, one-day VaR is a loss threshold that should be exceeded on roughly one trading day out of one hundred. It is not the maximum possible loss. We therefore pair it with Expected Shortfall, which measures the average loss after that threshold is crossed, and with stress tests for crisis conditions. The objective is not simply to produce a number. The objective is to build a transparent process, test whether the number behaves properly, and convert the evidence into monitoring and portfolio decisions.",
    ),
    (
        "Slide 2  Project Scope",
        "The project follows ten connected phases. We begin by collecting reliable market data and cleaning it so that every stock is measured on the same trading dates. We then construct the portfolio and calculate its daily value, return, and profit or loss. Historical Simulation gives us a transparent VaR baseline. EWMA, GARCH, and GJR-GARCH then adjust that history for changing volatility. Backtesting checks the forecasts against losses that occurred later, and model comparison identifies the approach with the strongest evidence. Finally, stress testing asks what could happen in a crisis that ordinary one-day VaR is not designed to capture. Each phase produces an output used by the next one, so the final recommendation can be traced back to the original data.",
    ),
    (
        "Slide 3  Phase 1 Data Collection",
        "The first phase creates the evidence base. We collect adjusted daily closing prices for the ten holdings, SPY as the market benchmark, and a risk-free rate for performance measures such as the Sharpe ratio. Adjusted prices matter because stock splits and dividends otherwise create artificial jumps that look like gains or losses. The pipeline is cache-first: once a valid response is saved, the analysis can be reproduced even if a data provider is unavailable. It also records the provider, the date range, and the latest observation. The portfolio uses Apple, Microsoft, Nvidia, JPMorgan, ExxonMobil, Amazon, Meta, Alphabet, Tesla, and UnitedHealth. These are the assets whose combined risk we will measure.",
    ),
    (
        "Slide 4  Phase 2 Data Cleaning",
        "Raw prices cannot be used safely without controls. The cleaning stage aligns all securities to common trading dates, checks for missing observations, flags prices that remain unchanged for suspiciously long periods, and verifies that returns are calculated in the correct order. If a clear data error creates an extreme return, the system can winsorize it, meaning it limits the error rather than allowing it to dominate the model. We convert the adjusted prices into log returns because they combine consistently through time and work well in volatility models. The important point is that genuine market shocks are preserved; only data problems should be repaired. The output is a clean price matrix, a clean return matrix, and the volatility inputs used by every later phase.",
    ),
    (
        "Slide 5  Phase 3 Portfolio Construction",
        "Portfolio construction turns individual stock histories into the economics of one investable portfolio. The base case starts with ten million dollars, uses equal target weights, and rebalances monthly. Equal weighting is transparent: each company begins with the same capital allocation, while monthly rebalancing prevents market winners from permanently taking over the portfolio. The engine also supports user-defined weights and alternative rules. On each day, it applies the weights to the aligned stock returns, updates the portfolio value, and converts the percentage move into dollar profit or loss. The weights must sum to one hundred percent, and the calculation uses only information available at that time. The outputs are the daily value, return, profit-and-loss series, and the weights behind them.",
    ),
    (
        "Slide 6  Phase 4 Historical Simulation VaR",
        "Historical Simulation is the simplest VaR model in the project. It takes a rolling window of actual portfolio returns, ranks them from worst to best, and selects the loss at the chosen confidence level. At 99 percent confidence with a 500-day window, the cutoff is near the fifth-worst observation. Expected Shortfall then averages the losses beyond that cutoff. This method does not force returns to follow a normal bell curve, so it retains the skewness and large tail events present in the data. Its main assumption is still important: the recent historical window must be relevant to the near future. It also gives every observation equal importance, whether it occurred yesterday or almost two years ago. Because it treats every historical observation equally, this limitation motivates volatility scaling.",
    ),
    (
        "Slide 7  Phase 5 EWMA Volatility Scaling",
        "EWMA stands for Exponentially Weighted Moving Average. It updates volatility by giving the most recent squared returns the greatest weight and allowing older observations to fade gradually. The parameter lambda controls that fading. We use the common daily value of 0.94, which means 94 percent of yesterday's variance estimate is carried forward and 6 percent comes from the latest squared return. A lower lambda would react faster but produce a less stable estimate. To calculate EWMA-scaled Historical VaR, old returns are enlarged or reduced so that they reflect today's volatility. The historical ordering is preserved, but the size of each shock changes. This makes the model more responsive when markets move from a calm period into a turbulent one.",
    ),
    (
        "Slide 8  Phase 6 GARCH Volatility Scaling",
        "GARCH is a statistical model designed for volatility clustering: quiet days tend to follow quiet days, while large moves often arrive in groups. The full name is Generalized Autoregressive Conditional Heteroskedasticity, but its practical idea is straightforward. Tomorrow's variance depends on a long-run level, the size of the latest shock, and yesterday's variance. A GARCH one-one model estimates one shock term and one persistence term, then produces a one-day-ahead volatility forecast. We use that forecast to rescale the historical return distribution before calculating VaR. The model assumes that volatility evolves in a stable recurring process and eventually moves back toward a long-run level. That is more flexible than EWMA, but it also introduces fitted parameters and model risk.",
    ),
    (
        "Slide 9  Phase 7 GJR GARCH Volatility Scaling",
        "GJR-GARCH extends the GARCH model by allowing negative returns to affect future volatility more strongly than positive returns of the same size. This is often observed in equity markets and is sometimes called the leverage effect. Here, leverage refers to an asymmetric volatility response, not to borrowing money. The model adds a parameter that activates after a negative shock. If that parameter is positive, bad news raises the next volatility estimate more than good news. As with GARCH, we estimate conditional volatility, forecast the next day, scale the historical returns, and calculate VaR. The advantage is a closer match to equity behavior. The cost is additional complexity, so the model must earn its role through out-of-sample backtesting rather than fit alone.",
    ),
    (
        "Slide 10  Phase 8 VaR Backtesting",
        "Backtesting asks whether the VaR forecasts would have worked on days that came later. For every test day, the model is estimated using only information already available, which prevents look-ahead bias. An exception occurs when the actual loss is larger than the forecast VaR. At 99 percent confidence, exceptions should be uncommon but not impossible. The Kupiec test checks whether the total number is plausible. The Christoffersen independence test checks whether exceptions cluster together, which can indicate that the model reacts too slowly. Conditional coverage considers the count and timing jointly. We also report the Basel traffic-light zone, but a green zone alone is not enough. A credible model should pass the frequency and clustering tests together.",
    ),
    (
        "Slide 11  Phase 9 Model Comparison",
        "Model comparison is not a contest to find the smallest VaR. A lower number can simply mean that a model is underestimating risk. We compare Historical Simulation, EWMA-scaled Historical Simulation, GARCH-scaled Historical Simulation, and GJR-GARCH-scaled Historical Simulation using exception counts, exception timing, average VaR, VaR stability, Expected Shortfall, and formal test results. We also consider transparency and how quickly each model reacts to market changes. The preferred model is the one that gives a defensible balance of calibration and behavior. A second model remains as a challenger, and plain Historical Simulation remains a transparent benchmark. This model hierarchy reduces dependence on a single set of assumptions.",
    ),
    (
        "Slide 12  Phase 10 Stress Testing",
        "Stress testing answers a different question from VaR. VaR estimates an ordinary one-day tail threshold using a statistical model. Stress testing asks what today's portfolio could lose if a severe historical episode or a hypothetical shock were repeated. The engine includes the 2008 financial crisis, the 2020 COVID crash, the 2022 inflation shock, banking stress, and a technology selloff, together with market, volatility, correlation, and sector shocks. These are conditional what-if estimates, not forecasts and not assigned probabilities. Their purpose is to expose vulnerabilities that a one-day model can miss, especially when correlations rise and diversification weakens. Stress results therefore sit beside VaR rather than replacing it.",
    ),
    (
        "Slide 13  Market Data Coverage",
        "This slide summarizes the actual data used by the engine. The saved run covers 4 June 2012 through 23 October 2026 and contains 3,619 aligned daily observations. It includes the ten portfolio stocks, SPY as the benchmark, and the risk-free input. The chart should be read as coverage, not performance: the purpose is to confirm that all required series extend across the analysis period. The risk-free rate came from a saved Yahoo Finance series with refresh available. Because the provider responses are cached, this run is reproducible. The period is broad enough to include calm markets, the 2020 crash, the 2022 selloff, and more recent shocks, although no historical sample can contain every possible future regime.",
    ),
    (
        "Slide 14  Clean Return Matrix",
        "The cleaning controls passed all six checks in the base run. No missing prices needed to be filled, and no stale prices were detected. That matters because a missing value can shift returns to the wrong day, while a stale price can artificially suppress volatility before creating a false jump later. The matrix aligns every stock to the same trading calendar and then calculates returns, so the portfolio is formed from simultaneous observations. These checks support the accuracy of the later P and L and VaR calculations. They do not prove that vendor data is perfect, but they show that the known structural problems were tested and that no repair was required in this saved run.",
    ),
    (
        "Slide 15  Portfolio Return and Drawdown",
        "This chart shows the ten-stock portfolio under equal weights and monthly rebalancing, expressed on a ten-million-dollar current-value basis. Over the historical sample, the annualized return was 31.6 percent and annualized volatility was 21.9 percent. The Sharpe ratio was about 1.28. The key risk evidence is the drawdown: the portfolio fell 34.9 percent from its previous peak during the 2020 shock. A drawdown of that size means an investor temporarily lost more than one-third of peak capital before recovery. These are historical sample results, not forecasts, and the stock universe uses companies that are prominent today, so selection and survivorship effects should be kept in mind.",
    ),
    (
        "Slide 16  Historical Simulation VaR Results",
        "At 99 percent confidence and a 500-day window, the one-day Historical Simulation VaR is about 337 thousand dollars. This means the model expects roughly 99 days out of 100 to lose less than that amount, while about one day out of 100 may lose more. Expected Shortfall is about 463 thousand dollars, which is higher because it averages only the losses beyond the VaR boundary. The ten-day VaR is about 1.06 million dollars. That longer-horizon figure uses square-root-of-time scaling, which is convenient but assumes risk accumulates smoothly and does not fully capture path dependence or changing correlations. VaR is therefore a threshold, not a worst-case loss.",
    ),
    (
        "Slide 17  EWMA Volatility Scaling Results",
        "The EWMA chart compares today's annualized volatility with the other estimates. EWMA is currently about 11.7 percent, below the longer rolling measure, so it scales the historical shocks downward. The resulting one-day VaR is about 240 thousand dollars and Expected Shortfall is about 277 thousand dollars. This does not mean the portfolio has become permanently safer. It means the most recent returns are calmer than much of the 500-day reference window. EWMA reacts quickly because lambda is 0.94, but that speed can also cause it to fall too rapidly after a shock. We therefore treat it as a responsive challenger and judge it through backtesting rather than accepting the lower number at face value.",
    ),
    (
        "Slide 18  GARCH Volatility Scaling Results",
        "The GARCH model estimates current annualized volatility at about 13.7 percent and produces a one-day scaled VaR of roughly 275 thousand dollars. The fitted persistence is 0.968. A number close to one means volatility shocks fade slowly rather than disappearing the next day. The estimated half-life is about 21 trading days, so half of a shock's influence remains after roughly one month. The chart's important feature is this gradual rise and decay across volatility regimes. GARCH captures clustering more formally than EWMA and allows mean reversion, but it responds symmetrically: a positive and a negative return of the same size have the same direct effect on variance. Because GARCH treats positive and negative shocks symmetrically, the next model relaxes that assumption.",
    ),
    (
        "Slide 19  GJR GARCH Leverage Effect Results",
        "GJR-GARCH estimates current annualized volatility at about 14.7 percent and one-day VaR at about 297 thousand dollars. The leverage parameter is positive at 0.154, which supports the idea that negative equity returns raise later volatility more than equally large positive returns. The model also has a lower AIC than symmetric GARCH: about 11,485 versus 11,581. A lower AIC means a better in-sample balance between fit and complexity, but it does not prove that the model forecasts risk correctly. The higher current volatility and VaR reflect the asymmetric response. We now need the out-of-sample tests to decide whether that added complexity improves real forecasting behavior.",
    ),
    (
        "Slide 20  VaR Backtesting Results",
        "The GJR model produced 34 exceptions during the 99 percent backtest, compared with about 31.2 expected. The Kupiec p-value is 0.618, so the total exception frequency is plausible. The Christoffersen independence p-value is 0.056, just above the 5 percent rejection threshold, so we do not reject independence. The joint conditional-coverage p-value is 0.143, and the Basel result is green. In plain language, the model had about the right number of breaches and their timing was not statistically too clustered at the chosen threshold. This is evidence that the model is adequate for the tested sample, not proof that it will remain correct in every future market regime.",
    ),
    (
        "Slide 21  Model Comparison Results",
        "This comparison explains why GJR-HS ranks first. All four models produced exception counts close enough to the expected 31.2 to pass the frequency test. The difference is timing. Historical Simulation, EWMA-HS, and symmetric GARCH-HS failed the independence test at the 5 percent level, meaning their exceptions were too clustered. GJR-HS recorded 34 exceptions and passed the frequency, independence, and joint tests. EWMA-HS ranks second because it reacts quickly and remains useful as a warning model, while Historical Simulation stays as the easiest benchmark to audit. The decision is therefore based on validation, not on selecting the model with the lowest current VaR.",
    ),
    (
        "Slide 22  Stress Testing Results",
        "The bars rank losses on today's portfolio under severe scenarios. Replaying the 2008 financial crisis produces the largest estimated loss, about 4.40 million dollars, or roughly 44 percent of portfolio value. The COVID crash produces about 3.46 million dollars, and the inflation shock about 2.47 million dollars. Basel-style stressed VaR is about 957 thousand dollars. Compare these figures with the ordinary one-day GJR VaR of about 297 thousand dollars: the crisis replay is almost fifteen times larger. That gap is not a contradiction. Daily VaR and stress testing answer different questions. The stress result is a conditional scenario, not a prediction, but it shows the loss capacity that governance must address.",
    ),
    (
        "Slide 23  Executive Risk Assessment",
        "The central conclusion is that routine daily risk is measurable, but crisis and concentration risk still require action. The selected GJR-HS model gives a 99 percent one-day VaR of about 297 thousand dollars and Expected Shortfall of about 339 thousand dollars. Its backtest produced 34 exceptions against about 31 expected and passed the full test suite. However, the 2008 replay reaches about 44 percent of portfolio value, above the proposed 40 percent escalation level. The recommended operating model is therefore GJR-HS as primary, EWMA-HS as challenger, and Historical Simulation as the transparent benchmark. Management must separately decide whether the stress loss and concentrated tail contributions should be hedged, reduced, or formally accepted.",
    ),
    (
        "Slide 24  Return Drawdown and Market Exposure",
        "This slide places the strong return record in its risk context. The portfolio earned a historical annualized return of 31.6 percent with 21.9 percent volatility, but it also suffered a maximum drawdown of 34.9 percent. Its beta to SPY is 1.19 and its correlation with SPY is 0.90. A beta above one means the portfolio has tended to move more than the market, while the high correlation shows that broad market conditions explain much of its behavior. The 2020 drawdown reached its trough on 23 March and required 52 trading days to recover. The message is not that past performance was poor. The central message is that high historical returns did not remove substantial equity-market and crash exposure.",
    ),
    (
        "Slide 25  Fat Tails and Volatility Clustering",
        "The return distribution is not a stable bell curve. Portfolio skewness is negative at about minus 0.53, and kurtosis is about 12, far above the normal-distribution reference of three. In practical terms, large moves, especially losses, occur more often than a simple normal model would imply. The chart groups days by the size and direction of the initial move and then shows the average absolute movement over the next five days. Large negative days are followed by especially large moves, which supports volatility clustering and asymmetry. The fitted GJR persistence of about 0.967 means the effect fades over weeks, not instantly. This evidence justifies volatility-aware models, while the backtest determines whether they are useful in practice.",
    ),
    (
        "Slide 26  Primary Challenger and Benchmark Models",
        "The model hierarchy has three different jobs. GJR-HS is the primary model for official daily monitoring because it is the only approach that passes the full 99 percent backtesting suite. EWMA-HS is the challenger because it is simple, fast, and highly responsive to recent shocks. If the primary and challenger diverge materially, that is a signal to investigate rather than to choose the more convenient answer. Plain Historical Simulation remains the benchmark because anyone can inspect the underlying ranked losses. Symmetric GARCH provides useful diagnostics, but its exception clustering prevents it from becoming the official model in this sample. Keeping these roles separate makes model risk visible and avoids dependence on one method.",
    ),
    (
        "Slide 27  Current One Day VaR and Expected Shortfall",
        "The bars compare the current 99 percent one-day loss estimates across the four models. The selected GJR-HS result is approximately 297 thousand dollars of VaR and 339 thousand dollars of Expected Shortfall. The Expected Shortfall bar is higher because it describes the average loss after the VaR line has already been crossed. Read the VaR carefully: it does not say the maximum loss is 297 thousand dollars, and it does not say a breach is impossible. It says that under the model and current conditions, losses should exceed that threshold on about one trading day in one hundred. The range across models also reminds us that the estimate depends on methodology.",
    ),
    (
        "Slide 28  Parameter Choice and Model Risk",
        "This grid shows how GJR-HS VaR changes when we alter the confidence level and the historical window. The base setting is 99 percent confidence and 500 days, producing a loss threshold of about 2.97 percent. Across the tested combinations, the estimate ranges from about 1.34 percent to 3.34 percent. Higher confidence generally moves us deeper into the loss tail, while the window determines which market regimes supply the scenarios. A short window reacts quickly but uses fewer tail observations. A long window is more stable but may include outdated conditions. This is why a risk limit must name the model, confidence level, horizon, and window. The word VaR alone is not a complete policy specification.",
    ),
    (
        "Slide 29  Adaptive VaR and Exceptions",
        "The horizontal axis is time, the vertical axis is daily profit or loss in thousands of dollars, and the risk boundary is the negative VaR forecast available before each day. A red point appears when the realized loss falls below that boundary. The VaR line rises in magnitude after large shocks, showing that the model adapts to changing volatility. Occasional red points are expected at 99 percent confidence; a model with no exceptions may simply be too conservative. The validation question is whether the total is plausible and whether breaches cluster. This chart shows the most recent 750 trading days for readability, while the formal tests use the full out-of-sample history of more than three thousand days.",
    ),
    (
        "Slide 30  Full Backtesting Comparison",
        "This slide separates three questions. First, Kupiec coverage asks whether each model has roughly the right number of exceptions. All four pass that test. Second, Christoffersen independence asks whether exceptions arrive separately rather than in clusters. Only GJR-HS passes at the 5 percent decision level, with a p-value of 0.056. Third, conditional coverage combines frequency and independence, and GJR-HS passes that joint test as well. The result is close to the threshold, so it deserves monitoring rather than overconfidence. A p-value above 0.05 does not prove the model true; it means the available sample does not provide enough evidence to reject it under that test.",
    ),
    (
        "Slide 31  Largest VaR Exceptions",
        "This table ranks the largest GJR-HS exceptions by realized loss. The worst listed breach occurred on 11 June 2020: the loss was about 586 thousand dollars against a VaR near 259 thousand dollars. Other large exceptions occurred during the 2022 inflation shock and the April 2025 tariff shock. A count-based test treats a small breach and a very large breach as one exception each, but economically they are not equivalent. Production governance should therefore record the size of every breach, confirm the data, identify the positions and market event that drove it, and document any remediation. Backtesting tells us whether the pattern is acceptable; exception review explains the losses and supports action.",
    ),
    (
        "Slide 32  Crisis Losses Versus Daily VaR",
        "The scenario bars make the limitation of one-day VaR visible. The 2008 replay implies a loss of about 44 percent, the COVID replay about 35 percent, and the technology selloff about 23 percent. A broad 20 percent market fall produces a portfolio loss of roughly 22 percent because the portfolio beta is above one. These results use today's portfolio weights and historical or hypothetical shocks. They are not probabilities and do not claim the exact crisis will repeat. Their value is to show whether the portfolio could survive a severe but intelligible event. Daily VaR controls routine market risk; stress testing frames capital, escalation, and risk-appetite decisions when normal relationships break down.",
    ),
    (
        "Slide 33  Tail Risk Concentration",
        "This chart compares capital weight with contribution to Expected Shortfall. Equal capital weights do not create equal risk contributions because the stocks have different volatility and correlation patterns. In the latest engine output, Tesla and Amazon together represent about 20.6 percent of capital but about 39 percent of tail risk. Tesla alone contributes roughly 20.8 percent of Expected Shortfall, and Amazon about 18.3 percent. The portfolio still receives an estimated diversification benefit of about 38 percent, so diversification is working, but it is uneven. This is the most useful place to investigate changes: reducing or hedging positions whose tail-risk share greatly exceeds their capital weight can lower risk more efficiently than cutting every holding equally.",
    ),
    (
        "Slide 34  Actions Supported by the Analytics",
        "The analysis produces two illustrative actions, not automatic trades. A beta-neutral SPY hedge is estimated to reduce VaR by about 59 percent, from roughly 307 thousand dollars to 127 thousand dollars, but the hedge would be large, around 10.5 million dollars short, and would introduce basis, financing, and execution risk. An in-sample reallocation reduces Expected Shortfall from about 331 thousand dollars to 230 thousand dollars and VaR to about 189 thousand dollars, subject to a 25 percent position cap. Before implementation, either idea needs out-of-sample testing, turnover and transaction-cost estimates, liquidity checks, tax review, and position limits. The models support a decision; they do not authorize a trade.",
    ),
    (
        "Slide 35  Proposed Risk Limits and Governance",
        "A model becomes useful only when its output is tied to ownership and action. The proposed framework assigns daily monitoring and one-day exception review to the risk team. If a threshold is exceeded, the portfolio manager prepares a remediation proposal, while the risk committee decides whether to approve the action or accept the residual risk. The committee should review the limits at least quarterly and after material changes in exposure or market conditions. The policy should state the exact VaR model, confidence, horizon, and window; an Expected Shortfall limit; a stress-loss escalation level; and concentration thresholds. These are proposed controls for approval, not existing policy. Every override and exception should leave an audit trail.",
    ),
    (
        "Slide 36  Final Recommendation",
        "My recommendation is to adopt GJR-HS as the primary model for official 99 percent one-day VaR monitoring, with EWMA-HS as the fast challenger and plain Historical Simulation as the transparent benchmark. This recommendation follows the evidence: GJR-HS captures the asymmetric volatility of equities and is the only model that passes the full backtesting suite in the current sample. It still cannot define the maximum loss, predict a crisis, or remove data, liquidity, and model risk. Expected Shortfall, stress testing, and position-level attribution must therefore remain mandatory. The immediate decision is whether the estimated 44 percent crisis loss and the concentration of tail risk in Tesla and Amazon fit the approved risk appetite. If the crisis loss and concentrated tail risk exceed approved appetite, management should hedge, reduce exposure, or explicitly document risk acceptance.",
    ),
]

from presentation_speech_natural import NATURAL_SLIDES

SLIDES = NATURAL_SLIDES


def set_cell_margins(cell, top=120, start=120, bottom=120, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_font(run, name="Aptos", size=11.5, bold=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = "PAGE"
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for node in (begin, instruction, separate, text, end):
        run._r.append(node)
    set_font(run, size=9)


def condensed_speech(slide_number, speech):
    """Fit the full narrative to a 20-minute delivery while retaining the conclusion."""
    limits = {
        1: 130, 2: 85, 3: 105, 4: 100, 5: 95, 6: 105,
        7: 100, 8: 85, 9: 90, 10: 105, 11: 95, 12: 80,
        13: 70, 14: 70, 15: 100, 16: 80, 17: 75, 18: 95,
        19: 90, 20: 85, 21: 90, 22: 75, 23: 75, 24: 95,
        25: 95, 26: 90, 27: 70, 28: 90, 29: 70, 30: 95,
        31: 80, 32: 70, 33: 85, 34: 90, 35: 85, 36: 110,
    }
    limit = limits[slide_number]

    sentences = re.split(r"(?<=[.!?])\s+", speech.strip())
    if len(re.findall(r"\b[\w'-]+\b", speech)) <= limit or len(sentences) < 3:
        return speech

    ending = sentences[-1]
    selected = []
    for sentence in sentences[:-1]:
        trial = " ".join(selected + [sentence, ending])
        if len(re.findall(r"\b[\w'-]+\b", trial)) > limit:
            break
        selected.append(sentence)
    if not selected:
        selected = [sentences[0]]
    return " ".join(selected + [ending])


def build_document():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.67)
    section.left_margin = Inches(0.82)
    section.right_margin = Inches(0.82)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(11.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos")
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.08

    title_style = styles["Title"]
    title_style.font.name = "Aptos Display"
    title_style.font.size = Pt(25)
    title_style.font.bold = True
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    title_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos Display")
    title_style.paragraph_format.space_after = Pt(14)
    title_ppr = title_style._element.get_or_add_pPr()
    title_border = title_ppr.find(qn("w:pBdr"))
    if title_border is not None:
        title_ppr.remove(title_border)

    heading = styles["Heading 1"]
    heading.font.name = "Aptos Display"
    heading.font.size = Pt(14)
    heading.font.bold = True
    heading.font.color.rgb = RGBColor(0, 0, 0)
    heading._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos Display")
    heading.paragraph_format.space_before = Pt(10)
    heading.paragraph_format.space_after = Pt(4)
    heading.paragraph_format.keep_with_next = True

    if "Document Note" not in styles:
        note = styles.add_style("Document Note", WD_STYLE_TYPE.PARAGRAPH)
    else:
        note = styles["Document Note"]
    note.font.name = "Aptos"
    note.font.size = Pt(10.5)
    note.font.italic = True
    note.font.color.rgb = RGBColor(70, 70, 70)
    note._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos")
    note.paragraph_format.space_after = Pt(8)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.add_run("Advanced Equity Portfolio Risk Management Presentation Speech")

    subtitle = doc.add_paragraph(style="Document Note")
    subtitle.add_run("Read aloud manuscript for the 36 slide deck")
    timing = doc.add_paragraph(style="Document Note")
    timing.add_run("Target duration approximately 20 minutes at a clear presentation pace")

    intro = doc.add_paragraph()
    r = intro.add_run(
        "This manuscript is written for direct delivery to a mixed, nontechnical audience. "
        "The figures reflect the latest saved engine run through 23 October 2026."
    )
    set_font(r, size=11.5)
    doc.add_page_break()

    delivered_speeches = []
    for index, (slide_title, speech) in enumerate(SLIDES, start=1):
        speech = condensed_speech(index, speech.strip())
        delivered_speeches.append(speech)
        p = doc.add_paragraph(slide_title, style="Heading 1")
        p.paragraph_format.keep_with_next = True
        body = doc.add_paragraph()
        body.paragraph_format.widow_control = True
        body.paragraph_format.keep_together = True
        run = body.add_run(speech)
        set_font(run, size=11.5)
        if index in {2, 12, 22}:
            body.paragraph_format.space_after = Pt(10)

    footer = doc.sections[0].footer.paragraphs[0]
    add_page_number(footer)

    props = doc.core_properties
    props.title = "Advanced Equity Portfolio Risk Management Presentation Speech"
    props.subject = "Twenty minute slide by slide presentation manuscript"
    props.author = ""
    props.keywords = "portfolio risk, VaR, Expected Shortfall, backtesting, stress testing"

    doc.save(OUTPUT)
    speech_text = " ".join(delivered_speeches)
    words = re.findall(r"\b[\w'-]+\b", speech_text)
    print(f"Created: {OUTPUT.resolve()}")
    print(f"Slides: {len(SLIDES)}")
    print(f"Speech words: {len(words)}")
    print(f"Minutes at 145 wpm: {len(words) / 145:.1f}")
    print(f"Minutes at 150 wpm: {len(words) / 150:.1f}")


if __name__ == "__main__":
    build_document()
