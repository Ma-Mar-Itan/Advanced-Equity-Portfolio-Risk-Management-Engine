"""Create the read-aloud speech aligned with the final 21-slide QFI deck."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables" / "QFI_Presentation_Speech_Final_Rehearsed.docx"


SLIDES = [
    (
        "Slide 1  Advanced Equity Portfolio Risk Management",
        """Hello everyone. Today I am presenting our advanced equity portfolio risk-management engine. The purpose of this project is to take a group of stocks, measure the losses that could occur under normal and severe market conditions, and test whether those risk estimates are dependable enough to support a real decision.

Before discussing the models, I want to define the basic language. A portfolio is simply a collection of investments held together. Each investment is called a holding, and its weight is the percentage of the portfolio invested in it. An equity portfolio is a portfolio made mainly of company shares, which we usually call stocks. This project studies ten large US companies rather than placing all the capital in a single stock.

Combining several stocks creates diversification. Diversification means that the result does not depend entirely on one company. If one business performs badly, gains elsewhere may soften the damage. However, diversification does not eliminate risk. Several companies can be exposed to the same economic forces, and during a broad crisis many stocks may fall together. A portfolio can therefore contain many names and still carry substantial market or sector concentration.

There are also different portfolio structures. A long-only portfolio owns stocks and benefits when they rise. That is the main structure used here. A long-short portfolio combines owned positions with short positions designed to benefit when selected stocks fall. Long-short portfolios can reduce some exposures, but they also introduce borrowing costs, leverage and additional loss possibilities. Our portfolio is also compared with SPY, an exchange-traded fund that follows the S and P 500. SPY acts as the benchmark, meaning the market reference used to judge the portfolio's performance and sensitivity to broad market movements.

Risk management is the process of identifying, measuring, monitoring and controlling possible losses. It does not mean removing every risk. Taking no risk would also remove much of the opportunity to earn a return. The practical goal is to understand the risk, decide whether it is acceptable, and act when it becomes too large.

The main daily measure in this project is Value at Risk, or VaR. VaR is a loss warning line for a stated period and confidence level. The figure on this slide is approximately 297 thousand dollars at 99 percent confidence for one trading day. In plain language, the model expects a ten-million-dollar portfolio to lose less than that amount on about 99 trading days out of 100. On roughly one day out of 100, the loss may be larger.

The most important limitation is that VaR is not the maximum possible loss. It identifies where the worst one percent of daily outcomes begins, but it does not tell us how damaging those outcomes may become. That is why the engine also calculates Expected Shortfall. Expected Shortfall is the average loss after the VaR warning line has already been crossed. VaR tells us where the severe-loss region begins; Expected Shortfall tells us the typical size of a loss within that region.

We also examine volatility and drawdown. Volatility describes how widely returns move from day to day. High volatility means larger and less predictable movements, both positive and negative. Drawdown measures the decline from a previous portfolio peak to a later low. It answers a very human question: how much value could an investor have watched disappear before the portfolio recovered?

Stress testing looks beyond ordinary daily risk. The 2008 crisis replay on this slide produces a loss of about 4.40 million dollars, or roughly 44 percent of the portfolio. This contrast is central to the project. Daily VaR supports routine monitoring, while stress testing asks what could happen in an exceptional crisis.

Finally, the slide shows 34 actual backtest exceptions compared with about 31.2 expected. An exception occurs when the realized loss is larger than the VaR forecast made before that day. Some exceptions are normal for a 99 percent model. The real test is whether their total number is reasonable and whether they are spread through time rather than arriving in dangerous clusters. The rest of the presentation explains how the data was prepared, how the portfolio was built, how four VaR methods were developed and tested, and why GJR-HS became the preferred model for daily monitoring.""",
    ),
    (
        "Slide 2  Project Scope and the Language of Risk",
        """This slide shows the full scope of the project and introduces the main vocabulary that will appear throughout the presentation.

An equity is a share of ownership in a company. A portfolio is a group of investments held together, and a holding is one investment inside that portfolio. A weight is the percentage of the portfolio assigned to a particular holding. A long position benefits when an asset rises, while a short position is designed to benefit when it falls. A benchmark is a market reference used to judge performance; in this project, that reference is SPY, which follows the S and P 500.

A return is the percentage gained or lost over a period. Profit and loss, or P and L, expresses the same movement in dollars. Volatility measures how widely returns move and is used as a measure of uncertainty. A drawdown is the decline from a previous portfolio peak to a later low. Correlation measures how closely two investments move together, while beta measures how sensitive the portfolio is to broad market movements.

Value at Risk, or VaR, is a loss warning line for a stated time period and confidence level. Expected Shortfall is the average loss after that warning line has been crossed. A backtesting exception occurs when the actual loss is greater than the VaR forecast made before that day. Stress testing asks what would happen if a severe historical or hypothetical event affected the portfolio.

The work is organized into ten phases, but those phases are not separate exercises. They form one connected process that begins with raw market prices and ends with a risk decision.

The first three phases create the foundation. We collect adjusted market data, clean and align it, and combine the ten stocks into one portfolio with defined weights and a rebalancing rule. If a price is wrong, if dates are mixed, or if the weights are applied incorrectly, every risk number that follows will also be wrong.

The next four phases develop the risk models. Historical Simulation provides a transparent starting point by using actual past portfolio outcomes. EWMA then gives greater importance to recent market movements. GARCH models the way turbulent and calm periods tend to persist. GJR-GARCH adds the idea that negative market shocks may increase future volatility more strongly than equally large positive shocks.

The final three phases ask whether the results are useful. Backtesting compares forecasts with the losses that actually occurred. Model comparison evaluates the competing methods using the same evidence. Stress testing then moves beyond routine daily risk and replays crises or hypothetical shocks against today's portfolio.

The key message is that a credible risk engine is more than a formula. It needs reliable data, correct portfolio construction, a model that responds to changing markets, an honest test using information available at the time, and a clear way to communicate the result. The dashboard brings those stages together so the user can move from data quality to portfolio performance, daily VaR, model validation and severe-loss scenarios in one consistent workflow.""",
    ),
    (
        "Slide 3  Phase 1 Data Collection",
        """Phase 1 is data collection. Before the engine can measure risk, it needs information that describes the investments, their historical price changes and the portfolio's exposure to each one.

The main market input is the daily adjusted closing price. The closing price is the stock's price at the end of a trading day. The word adjusted means the historical series has been corrected for corporate actions such as stock splits and dividends.

A stock split changes the number of shares and the price per share without changing the investor's total ownership value at that moment. In a two-for-one split, one share becomes two shares and the price of each share is roughly halved. Without an adjustment, the price chart could look as if the investor suddenly lost 50 percent, even though the total value did not change.

A dividend is a payment that a company makes to its shareholders, usually from its profits. When a dividend is paid, the share price may fall by roughly the amount of the payment because cash has left the company. The investor has not simply lost that value; part of it has been received as cash. Adjusted prices account for both splits and dividends so these corporate actions do not appear as false investment gains or losses.

Those prices are converted into daily returns. A daily return measures the percentage gained or lost from one trading day to the next. Returns are more useful than raw price changes because they make different stocks comparable. A two-dollar move is enormous for a ten-dollar stock but relatively small for a five-hundred-dollar stock. Expressing both movements as percentages puts them on the same scale.

We also need portfolio weights. A weight is the share of total capital invested in a holding. If one million dollars of a ten-million-dollar portfolio is invested in Apple, Apple's weight is 10 percent. The same stock return can have a very different effect depending on its weight, so prices alone are not enough to calculate portfolio risk.

The analysis also collects a market benchmark, sector classifications and a short-term risk-free rate. SPY is used as the benchmark because it follows the S and P 500. It helps us compare the portfolio with the broad US equity market and later calculate measures such as beta and correlation. Sector information groups companies into areas such as technology, energy, healthcare and financial services. This can reveal hidden concentration and supports sector-specific stress tests. The risk-free rate represents the return available from a very low-risk short-term government investment. It is used as a baseline when measuring risk-adjusted performance.

The data layer can work with public end-of-day sources such as Yahoo Finance and Stooq, and the architecture can accommodate institutional sources when they are available. The important point is consistency: ticker symbols, date formats, currencies and adjustment conventions must be standardized before data from different providers can be compared.

The example universe contains Apple, Microsoft, Nvidia, JPMorgan, ExxonMobil, Amazon, Meta, Alphabet, Tesla and UnitedHealth. The chart shows the growth of one dollar invested separately in each stock over the sample. It is not yet the portfolio result. It lets us compare the paths of the individual holdings on the same starting scale. Nvidia produced the largest standalone growth, followed by Tesla, while the other stocks followed very different paths.

The final sample runs from 4 June 2012 through 23 October 2026 and contains 3,619 shared trading days. Shared means that every holding has a valid return for the same date. A portfolio return for Monday must combine Monday's return for every stock; it must never mix Apple's Monday result with Microsoft's Tuesday result. The period includes calm markets, the COVID crash, the 2022 decline and more recent shocks, giving the models several different market conditions to study. By the end of Phase 1, the engine has the adjusted price histories, daily returns, weights and reference inputs required for cleaning, portfolio construction and later risk analysis.""",
    ),
    (
        "Slide 4  Phase 2 Data Cleaning",
        """After collecting the data, we cannot place it directly into a risk model. Different sources may contain missing dates, stale observations, inconsistent formats or artificial price movements. Phase 2 turns the raw information into a consistent and auditable dataset.

The first task is confirming that prices are adjusted for splits and dividends. We then align the trading dates across all stocks. Date alignment means creating one shared calendar in which every row refers to the same trading day for every holding. If Apple has a Monday return but Microsoft's Monday observation is missing, we cannot silently combine Apple's Monday movement with Microsoft's Tuesday movement. That would create a portfolio result that never actually occurred.

Missing values require judgment. A gap may come from a provider problem, a trading suspension, a holiday or a stock that did not yet trade during part of the requested period. Carrying the previous price forward can sometimes solve a very short technical gap, but doing it too freely creates artificial zero returns and makes the asset look safer than it is. The treatment must therefore be explicit and recorded rather than hidden.

We also check for stale prices. A stale price is a value that remains exactly unchanged for an unusually long time because the feed may have stopped updating. Several stale observations can understate volatility, followed by an artificial jump when the price finally changes. Detecting this pattern protects both the return calculation and the later volatility estimates.

Another possible cleaning method is winsorization. Winsorization limits an extreme observation to a chosen boundary instead of deleting the entire row. It can be useful when there is clear evidence of a data error, such as a misplaced decimal point that creates a false 99 percent fall and recovery. However, it must be used carefully. A genuine market crash is also extreme, and those real losses are exactly what a risk model needs to retain. In this project, an unusual return is not altered merely because it is large.

After the prices are cleaned, they are converted into log returns. A log return is the natural logarithm of today's adjusted price divided by yesterday's adjusted price. The name sounds technical, but the practical benefit is simple: log returns measure proportional change consistently and can be added across consecutive periods, which is useful for statistical volatility models. For normal daily movements, they are very close to ordinary percentage returns. The dashboard can therefore use log returns in the engine while still displaying intuitive percentages and dollar profit and loss.

The first chart on this slide shows Apple's cleaned daily returns. Most observations remain close to zero, while a smaller group contains large positive or negative moves. The cluster around 2020 reflects genuine market turbulence, not a data mistake, so it remains in the sample.

The second chart shows rolling annualized volatility. Rolling means that we select a fixed window of recent trading days, calculate volatility, move the window forward by one day and calculate it again. This creates a changing risk series instead of one volatility number for the entire sample. Annualized means that daily volatility is converted to an equivalent yearly scale, normally by multiplying it by the square root of approximately 252 trading days. This does not predict the annual return; it simply expresses recent daily variability on a familiar yearly scale.

Apple is highlighted in teal and the other holdings are shown in grey. Volatility rises as recent movements become larger and falls as markets stabilize. The COVID spike demonstrates why the later models cannot assume that risk stays constant through time.

The final outputs are a clean price matrix, a clean return matrix, a weighted portfolio return series and a rolling volatility series. A matrix is simply a table in which dates form the rows and stocks form the columns. These outputs give every later model the same consistent information while preserving the severe market events that risk management is supposed to study.""",
    ),
    (
        "Slide 5  Phase 3 Portfolio Construction",
        """Phase 3 turns the cleaned stock returns into one investable portfolio. The main inputs are the ticker list, target weights, initial portfolio value and rebalancing frequency. Tickers identify the companies. Weights determine how much capital each company receives. The initial value converts percentage returns into dollar gains and losses, and the rebalancing rule determines how the allocation changes through time.

The engine supports several portfolio choices. An equal-weighted portfolio assigns the same capital weight to every stock. With ten holdings, each begins at approximately 10 percent. This is simple and transparent, but equal capital does not mean equal risk because some stocks are much more volatile than others. User-defined weights allow an investor to choose the allocation directly. Market-cap weights give larger companies larger allocations based on their market value. Inverse-volatility weights give smaller allocations to historically more volatile stocks. An optional long-short portfolio can include negative weights, but that introduces leverage, borrowing and short-selling risks.

The main presentation uses equal starting weights and monthly rebalancing. This means the engine lets the weights move naturally during the month, then checks them once each month against the 10 percent targets. A holding that has become too large is trimmed, while capital is added to holdings that have become too small. For example, if Nvidia rises much faster than the other stocks, its weight increases during the month. On the next rebalancing date, the engine sells part of that position and redistributes the proceeds across the underweight holdings. This keeps the strategy aligned with its intended allocation and prevents one winner from gradually taking over the portfolio. In a live account, the benefit would still have to be compared with trading costs, taxes and market impact.

Each day's portfolio return is calculated by multiplying every stock's return by its weight and adding the results. For a simple example, imagine half the portfolio gains 2 percent and the other half loses 1 percent. The combined return is approximately positive 0.5 percent. The same weighted arithmetic applies across all ten holdings.

The engine produces three related outputs. Daily return expresses the portfolio's movement as a percentage. Daily profit and loss, or P and L, expresses that same movement in dollars. A negative 1.5 percent return on a ten-million-dollar portfolio is approximately a 150-thousand-dollar loss. Portfolio value then compounds those daily results through time, so today's ending value becomes the starting point for tomorrow.

The large chart compares the portfolio's value with SPY, the broad-market benchmark. The two smaller charts display daily P and L and daily return together so the audience can connect percentage movements with their dollar impact. By the end of this phase, we have a complete daily portfolio value series, return series and P and L series. Those are the direct inputs used by every VaR, volatility, backtesting and stress-testing stage that follows.""",
    ),
    (
        "Slide 6  Phase 4 Historical Simulation VaR",
        """Phase 4 introduces Historical Simulation Value at Risk. This is the first VaR method in the project and the most transparent one. It uses actual past portfolio returns as examples of what could happen next. It takes a recent window of returns, arranges them from the worst result to the best and identifies the point where the most severe losses begin. It does not assume that returns follow a perfect bell-shaped curve.

The historical window is the number of previous trading days used in the calculation. The engine allows 250, 500 or 750 days. A 250-day window is approximately one trading year. It reacts relatively quickly to new conditions, but it contains fewer observations. A 500-day window is approximately two trading years and provides a balance between responsiveness and stability. A 750-day window is approximately three trading years. It contains more data, but some older market conditions may be less relevant today.

We must also choose a confidence level. Confidence describes how often the model expects the loss to remain below the VaR threshold. At 95 percent confidence, the threshold is expected to contain about 95 days out of 100, so losses may exceed it on about five days out of 100. At 99 percent confidence, the threshold is expected to contain about 99 days out of 100, leaving roughly one day out of 100 beyond it. At 99.5 percent confidence, only about one day out of 200 is expected to exceed the threshold. A higher confidence level moves further into the severe-loss region and normally produces a larger VaR.

The chart shows the distribution of historical portfolio returns. A distribution describes how frequently different outcomes occurred. Most returns are near the center, while the severe negative returns appear in the left tail. Using a 500-day window and 99 percent confidence, the one-day Historical Simulation VaR is about 337 thousand dollars. In plain language, the model expects the ten-million-dollar portfolio to lose less than this amount on approximately 99 trading days out of 100. On roughly one day out of 100, the loss may be greater. VaR is a warning line, not the maximum possible loss.

Expected Shortfall, often shortened to ES, explains what happens after the VaR line has been crossed. It takes all losses worse than the VaR threshold and calculates their average. On this slide, Expected Shortfall is about 463 thousand dollars. It is larger than VaR because it measures the typical loss inside the severe tail rather than only marking where that tail begins.

The ten-day VaR is about 1.06 million dollars. The longer horizon creates more exposure to unfavorable movements and is useful when positions cannot be sold immediately. The engine also produces rolling VaR by recalculating the measure each day with an updated historical window. This creates a time series that shows how the estimated loss threshold rises and falls as market conditions change.

The advantage of Historical Simulation is that every result can be traced to actual historical portfolio outcomes. Its main limitation is that every observation inside the window receives equal importance. A turbulent day from two years ago counts as much as a calm day from last week. The next phase addresses this by scaling historical returns according to changing volatility.""",
    ),
    (
        "Slide 7  Phase 5 EWMA Volatility Scaling",
        """Phase 5 introduces EWMA volatility scaling. EWMA stands for Exponentially Weighted Moving Average. The idea is to keep the historical return scenarios but make them more responsive to the market conditions we are facing today.

Basic Historical Simulation treats every day inside the selected window equally. A calm return from two years ago has the same influence as a large movement from last week. EWMA changes that by giving greater influence to recent movements and gradually reducing the influence of older ones.

The model is controlled by a number called lambda. Lambda tells us how quickly old information fades. It must lie between zero and one. A value close to one produces a smoother volatility estimate because most of yesterday's estimate is carried forward. A lower value gives more influence to the newest return, so the model reacts faster but also moves around more sharply.

Here lambda is 0.94, a common setting for daily financial returns. In practical terms, today's variance estimate keeps 94 percent of yesterday's estimate and adds 6 percent from the newest squared return. Yesterday's estimate already contains earlier observations, so their influence remains but decays gradually. This is why lambda is also called the decay factor.

Variance measures how widely returns are spread by using squared movements. Volatility is the square root of variance and is easier to interpret because it is expressed on the same general scale as returns. Once EWMA estimates volatility for every day, the engine rescales each old return by comparing today's volatility with the volatility on the day that return originally occurred.

If an old loss occurred during a market that was twice as volatile as today, the engine scales that loss down. If today's market is more volatile than it was on the historical day, the return is scaled up. We are not changing history. We are asking what the same historical shock might look like under today's level of market risk.

The chart shows EWMA volatility rising quickly during turbulent periods and falling gradually as conditions calm. Current annualized EWMA volatility is about 11.7 percent, producing a 99 percent one-day VaR of about 240 thousand dollars. This is lower than the unscaled Historical Simulation estimate because recent conditions are calmer than much of the selected historical window. A smaller VaR is not automatically a better VaR, so the model still has to be judged by the losses that occur afterward. The next phase replaces the fixed decay rule with a volatility model estimated directly from the portfolio data.""",
    ),
    (
        "Slide 8  Phase 6 GARCH Volatility Scaling",
        """Phase 6 introduces GARCH volatility scaling. GARCH stands for Generalized Autoregressive Conditional Heteroskedasticity. The name is complicated, but the idea is familiar: large market movements tend to be followed by more large movements, while calm periods also tend to continue. This pattern is called volatility clustering.

Unlike EWMA, which uses a fixed lambda, GARCH estimates its own response from the portfolio data. The GARCH 1,1 model uses one recent squared return to represent the newest shock and one previous variance estimate to represent the volatility already in the market. It combines those pieces to estimate conditional volatility, meaning the level of volatility expected given the information available at that time.

The model produces a volatility estimate for each historical day and a one-day-ahead forecast. That forecast is then used to scale the historical returns in the same spirit as EWMA: old returns are resized so they reflect the volatility expected for the next day.

The chart compares the volatility paths from the rolling measure, EWMA, GARCH and GJR-GARCH. The current GARCH volatility estimate is about 13.7 percent, producing a 99 percent one-day scaled VaR of about 275 thousand dollars.

GARCH persistence is about 0.968. Persistence tells us how slowly the effect of a volatility shock fades. A value close to one means the shock remains influential for some time. The estimated half-life is approximately 21 trading days, meaning that after about one trading month, roughly half of the shock's effect is still present.

Standard GARCH improves the timing of volatility, but it treats a positive and a negative return of the same size as equally important. Equity markets often react more strongly to bad news, so the next phase adds that asymmetry.""",
    ),
    (
        "Slide 9  Phase 7 GJR GARCH Volatility Scaling",
        """Phase 7 extends the previous model with GJR-GARCH. The important difference is that GJR-GARCH allows negative returns to increase future volatility more than equally large positive returns.

This is known as an asymmetric response, or the leverage effect. For an equity portfolio, the intuition is straightforward. A strong positive day may improve confidence, but a negative shock can create fear, forced selling and uncertainty, causing risk to rise more sharply afterward.

The leverage parameter measures this extra response to negative returns. In our results, it is positive at approximately 0.154. This supports the presence of downside asymmetry in the sample: negative shocks were followed by a stronger volatility response than positive shocks of the same size.

The chart compares standard GARCH with GJR-GARCH through time. The current GJR-GARCH volatility estimate is about 14.7 percent, and the corresponding 99 percent one-day VaR is about 297 thousand dollars.

The model also has a lower AIC than standard GARCH. AIC is a comparison score that rewards a model for fitting the data but penalizes it for unnecessary complexity. When two models use the same dataset, a lower AIC suggests the better balance between fit and complexity.

That result is encouraging, but it is not enough to select the model. A model can fit historical data very well and still forecast poorly. The next phase therefore stops asking how well the models describe the past and asks how their forecasts performed on days they had not yet seen.""",
    ),
    (
        "Slide 10  Phase 8 VaR Backtesting",
        """Phase 8 is VaR backtesting. Until this point, the models have produced reasonable-looking risk estimates. Backtesting asks whether those forecasts actually behaved as a 99 percent VaR model should.

The test is rolling and out of sample. Each day, the model uses only information that was available before that day, produces a VaR forecast, and then compares the forecast with the loss that occurred afterward. This timing is essential because using future information would create look-ahead bias and make the model appear better than it really was.

An exception occurs when the actual loss is greater than the VaR threshold forecast for that day. At 99 percent confidence, some exceptions are expected. If there were none, the model might be far too conservative. If there were too many, it might be underestimating risk.

The chart compares actual daily profit and loss with the GJR-HS VaR forecast. GJR-HS produced 34 exceptions, compared with about 31.2 expected over the backtesting period. The totals are close, but the number alone does not tell us whether those exceptions arrived in a healthy pattern.

The Kupiec test checks the frequency: is the total number of exceptions plausible for a 99 percent model? Its p-value is about 0.618. The Christoffersen independence test checks timing: are exceptions reasonably spread out, or do they cluster together? Its p-value is about 0.056. The conditional-coverage test combines both questions.

A p-value is evidence against rejecting the model. Using a 5 percent decision rule, a p-value below 0.05 would lead us to reject the model on that test. The GJR-HS p-values remain above that cutoff, so it passes frequency, independence and conditional coverage in this sample.

The Basel traffic light is also green, but that result is only a supporting indicator because it focuses mainly on the exception count. The statistical tests are what show whether the frequency and timing are both acceptable. We can now compare all four models using the same standards.""",
    ),
    (
        "Slide 11  Phase 9 Model Comparison",
        """Phase 9 compares the four VaR approaches: unscaled Historical Simulation, EWMA-scaled Historical Simulation, GARCH-scaled Historical Simulation and GJR-GARCH-scaled Historical Simulation.

The goal is not to choose the model with the smallest VaR. A smaller number may look attractive, but it may simply mean the model is underestimating risk. A useful model should produce a reasonable exception count, avoid heavy clustering and respond sensibly when volatility changes.

All four models produced total exception counts close enough to the expected count to pass the Kupiec frequency test. The important difference appears in the timing. Historical Simulation, EWMA-HS and standard GARCH-HS failed the independence test at the 5 percent level because their exceptions were too clustered. In other words, their failures tended to arrive together during difficult periods.

GJR-HS passed the frequency, independence and conditional-coverage tests. That makes it the strongest primary model for daily monitoring in this sample. EWMA-HS remains useful as a fast-moving challenger that gives a second opinion, while unscaled Historical Simulation remains the transparent benchmark because its result can be traced directly to ranked historical losses.

This is a model-ranking decision, not proof that GJR-HS will always work. The next phase addresses the losses that an ordinary one-day backtest cannot fully represent: severe crisis scenarios.""",
    ),
    (
        "Slide 12  Phase 10 Stress Testing",
        """Phase 10 is stress testing. Stress testing answers a different question from VaR. VaR estimates a routine daily loss threshold under a chosen model, confidence level and historical window. Stress testing asks what would happen to the portfolio we hold today if a severe event occurred.

The chart ranks both historical and hypothetical scenarios. A historical replay takes the pattern of an earlier crisis and applies it to today's holdings. A hypothetical scenario applies a deliberately designed shock, such as a broad market fall, doubled volatility, a spike in correlations or a severe decline in one sector.

The 2008 financial-crisis replay is the worst tested case, producing an estimated loss of about 4.40 million dollars, or roughly 44 percent of the ten-million-dollar portfolio. The COVID replay produces about 3.46 million dollars, while the 2022 inflation shock produces approximately 2.47 million dollars.

These scenarios are not forecasts, and they are not assigned probabilities. They are conditional statements: if this event occurred and today's portfolio were exposed to that pattern, this is the estimated effect.

That distinction matters because passing a one-day VaR backtest does not make VaR a crisis-loss ceiling. The stress results show that a severe event can create a loss many times larger than the normal daily threshold. The remaining slides bring the results together and turn them into a risk-management recommendation.""",
    ),
    (
        "Slide 13  Strong Returns Came with a 34.9 Percent Drawdown",
        """The next slides move from the methods to what the results mean. Historically, the portfolio produced an annualized return of about 31.6 percent. Annualized means the full historical growth rate has been converted into an average yearly rate so it can be compared across investments and periods.

Annualized volatility was about 21.9 percent, and the Sharpe ratio was approximately 1.28. The Sharpe ratio compares the return earned above the risk-free rate with the volatility taken to earn it. A higher value generally indicates more excess return for each unit of volatility.

The strong return did not come without risk. The portfolio's maximum drawdown was 34.9 percent, meaning that at its worst point it had fallen by more than one-third from a previous peak. Its beta to SPY was about 1.19, so it tended to move more than the broad market, and its correlation with SPY was about 0.90, showing that the two moved closely together.

The conclusion is not simply that the portfolio performed well. It is that strong historical growth existed alongside a severe drawdown and substantial market exposure. Historical performance is evidence about the past, not a promise about the future.""",
    ),
    (
        "Slide 14  Current Model Choice Moves One Day VaR from 240 to 337 Thousand Dollars",
        """This slide places today's four one-day VaR estimates beside each other using the same 99 percent confidence level. EWMA-HS produces the lowest estimate at about 240 thousand dollars. GARCH-HS produces about 275 thousand, GJR-HS about 297 thousand, and unscaled Historical Simulation about 337 thousand.

That range matters. The portfolio has not changed, but the estimate changes because each model treats volatility differently. This is model risk: uncertainty created by the method used to measure the underlying financial risk.

A VaR number should therefore never be reported on its own. It should always state the model, confidence level, time horizon and historical window. Expected Shortfall also remains above VaR for every method because it measures the average loss after the threshold has been crossed rather than only locating the threshold.""",
    ),
    (
        "Slide 15  Volatility Changes Regime and Downside Shocks Matter More",
        """The volatility chart shows why one fixed risk level is not enough. Calm periods are interrupted by sudden spikes, and those spikes fade gradually rather than disappearing immediately.

GJR-GARCH persistence is about 0.967, with a half-life of roughly 21 trading days. This means shocks decay slowly. The positive leverage parameter also captures the stronger increase in volatility that follows negative returns.

After we divide returns by the volatility estimated for each day, residual kurtosis falls from about 12.0 to about 4.5. Kurtosis measures how often extreme observations appear relative to a normal bell curve. The reduction shows that the model explains much of the volatility clustering. However, the remaining value is still above three, so extreme tails have not disappeared. Volatility modelling improves the risk description; it does not make extreme losses normal or harmless.""",
    ),
    (
        "Slide 16  GJR HS Is the Only Model That Passes All 99 Percent Backtests",
        """This slide brings the backtesting evidence together. GJR-HS produced 34 exceptions compared with approximately 31.2 expected. Its Kupiec, independence and conditional-coverage p-values all remain above the 5 percent rejection level.

That makes GJR-HS the only model in this comparison to pass all three 99 percent backtests. The evidence supports using it as the primary model for daily monitoring.

It does not prove that the model will always work. A liquidity shock, a new market structure or a crisis unlike anything in the sample can still cause failure. The careful conclusion is that GJR-HS performed best in this particular backtest. It should still be challenged by EWMA-HS and checked against transparent Historical Simulation rather than trusted without question.""",
    ),
    (
        "Slide 17  Crisis Loss and Tail Concentration Are Larger Than Daily VaR",
        """The stress and attribution results identify the risks that remain after model selection. The 2008 replay removes about 44 percent of portfolio value, far more than the ordinary one-day VaR estimate.

The loss-by-stock chart also shows that equal money weights do not create equal risk contributions. Tesla and Amazon together represent about 21 percent of capital but contribute roughly 39 percent of Expected Shortfall. Their volatility and their behaviour during bad portfolio days make their tail-risk contribution much larger than their capital weight.

The portfolio still receives a diversification benefit of about 38 percent relative to adding the standalone risks of every stock. However, severe losses remain concentrated in a small number of holdings. Those positions deserve the most attention if management wants to reduce tail risk.""",
    ),
    (
        "Slide 18  The Analytics Support Hedging or Reallocation Not Automatic Trading",
        """The engine is designed to support a decision, not to trade automatically. This slide shows two possible responses to the measured risk.

The first illustration adds a broad SPY hedge and reduces modelled VaR by about 59 percent. A hedge is a position intended to offset losses elsewhere in the portfolio. The reduction is meaningful, but it requires a large short position and introduces financing cost, basis risk and execution risk. Basis risk means the hedge may not move exactly opposite to the portfolio.

The second illustration changes the stock weights. In the historical optimization, Expected Shortfall falls from about 331 thousand dollars to about 230 thousand. That improvement comes with different holdings, lower historical return and greater concentration in some remaining positions.

Neither result is an automatic recommendation. A real decision would require testing on new data, checking liquidity, estimating transaction costs and taxes, and obtaining the appropriate approval.""",
    ),
    (
        "Slide 19  Risk Limits Turn Model Output into a Repeatable Control Process",
        """A risk number becomes useful only when it leads to a consistent process. The proposed control framework has five steps.

First, calculate the primary, challenger and benchmark measures each day. Second, investigate every exception, data problem or unexplained difference between models. Third, escalate breaches of VaR, stress or concentration limits. Fourth, decide whether to reduce, hedge or consciously accept the risk. Finally, record the evidence, the decision, the responsible owner and the follow-up date.

These are proposed controls for approval, not policies that are already in force. Their purpose is to make sure the same type of risk event receives the same type of review, rather than depending on an improvised reaction.""",
    ),
    (
        "Slide 20  Recommendation",
        """My recommendation is to use GJR-HS as the primary daily VaR model. It captures the stronger volatility response after negative returns and is the only model in this comparison to pass the frequency, independence and conditional-coverage tests at 99 percent.

EWMA-HS should remain the fast-moving challenger, while unscaled Historical Simulation should remain the transparent benchmark. Using all three roles reduces the danger of depending on a single model view.

Daily VaR should always be reported beside Expected Shortfall, stress testing and risk attribution. If a possible 44 percent crisis loss or the concentration of tail risk in Tesla and Amazon is outside the portfolio's risk appetite, management should reduce the exposure, hedge it or explicitly accept it.

The engine provides evidence for that decision. It does not replace judgment, governance or accountability.""",
    ),
    (
        "Slide 21  What the Historical Simulation Produced from a 10 Million Dollar Start",
        """I will finish with the simulated investment outcome. The earlier risk slides value the portfolio at ten million dollars today. This final slide asks a different historical question: what would have happened if ten million dollars had been invested at the beginning of the sample using the same equal-weighted strategy and resetting the weights once each month?

Under that historical path, the portfolio grows to approximately 513.4 million dollars, creating about 503.4 million dollars of cumulative simulated profit. The annualized return is 31.6 percent, and annualized volatility is 21.9 percent. Nvidia is the largest profit contributor, followed by Tesla and Alphabet.

Monthly rebalancing matters to that result. As the strongest performers became larger, the engine trimmed them back toward their target weights and redistributed part of the gains across the other holdings. The final outcome therefore reflects the portfolio strategy, not simply buying Nvidia at the start and leaving every position untouched.

The drawdown chart shows the cost of that growth. The worst period ran from 19 February to 23 March 2020, when the portfolio fell 34.9 percent from its previous peak. It recovered by 5 June 2020.

These figures are a historical simulation before transaction costs and taxes. They are not a forecast that ten million dollars invested today will produce the same result. The final lesson is that the strategy generated exceptional historical growth, but it required accepting substantial drawdown, market exposure and concentrated tail risk. Performance and risk must therefore be presented together.""",
    ),
]


def set_cell_borderless(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is not None:
        p_pr.remove(p_bdr)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char_1 = OxmlElement("w:fldChar")
    fld_char_1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char_2 = OxmlElement("w:fldChar")
    fld_char_2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char_1, instr_text, fld_char_2])


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.68)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.3)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.04

    title_style = styles["Title"]
    title_style.font.name = "Aptos Display"
    title_style.font.size = Pt(25)
    title_style.font.bold = True
    title_style.font.color.rgb = RGBColor(0, 0, 0)

    heading = styles["Heading 1"]
    heading.font.name = "Aptos Display"
    heading.font.size = Pt(17)
    heading.font.bold = True
    heading.font.color.rgb = RGBColor(0, 0, 0)
    heading.paragraph_format.space_before = Pt(0)
    heading.paragraph_format.space_after = Pt(10)
    heading.paragraph_format.keep_with_next = True

    p = doc.add_paragraph(style="Title")
    p.add_run("Advanced Equity Portfolio Risk Management Presentation Speech")
    set_cell_borderless(p)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = subtitle.add_run("Read aloud manuscript aligned with the final 21 slide presentation")
    r.bold = True
    r.font.size = Pt(12)
    intro = doc.add_paragraph(
        "This version follows the final PowerPoint in order. Slides 1 through 12 explain the concepts and methods. "
        "Slides 13 through 21 interpret the results without repeating definitions already established earlier."
    )
    intro.paragraph_format.space_after = Pt(16)

    for index, (slide_title, text) in enumerate(SLIDES):
        if index > 0:
            doc.add_page_break()
        h = doc.add_paragraph(style="Heading 1")
        h.add_run(slide_title)
        set_cell_borderless(h)
        for block in text.split("\n\n"):
            paragraph = doc.add_paragraph(block.strip())
            paragraph.paragraph_format.keep_together = False

    footer = section.footer
    footer_p = footer.paragraphs[0]
    add_page_number(footer_p)
    for run in footer_p.runs:
        run.font.name = "Aptos"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(100, 100, 100)

    doc.core_properties.title = "Advanced Equity Portfolio Risk Management Presentation Speech"
    doc.core_properties.subject = "Read aloud manuscript aligned with the final 21 slide QFI presentation"
    doc.core_properties.author = "Marwan Itani"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
