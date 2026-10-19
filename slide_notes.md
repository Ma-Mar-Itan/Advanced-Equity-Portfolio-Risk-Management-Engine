# Slide notes

How this file works: every `### ` line is one slide title, `- ` lines are its bullet
points, `Image:` is a chart from slides_assets/, `Say:` is the speaker note.
Slides with an image hold at most 2 short bullets (the builder warns otherwise).
`python -m tools.build_deck` turns this file into QFI_V2_slides.pptx.

## Module 0: How the platform is built

### One settings form drives the whole platform
- Two separate parts: an engine that does the maths, and a dashboard that only shows the results
- One "settings form" holds every choice: which stocks, how much of each, which dates, how much money ($10M), how sure we want to be (99%)
- Every piece plugs in the same way, so adding a data source or a model is one small file
Say: Before any numbers, a word on how it's built. The maths lives in its own package that knows nothing about screens; the dashboard just asks it questions and draws the answers. Every calculation reads the same settings form, so if you change the stocks or the amount, every number in the platform updates together.

## Module 1: Data collection

### Step 1: we collect 14 years of daily prices
- A price is what one share costs at the end of each trading day; a return is how much it moved that day (from $100 to $102 is a +2% return)
- We use "adjusted" prices, corrected for splits and dividends, so a stock splitting 1-into-4 doesn't look like a 75% crash
- Two sources: Yahoo Finance (any stock in the world, free) and Tiingo (an official backup); every download is saved so we only fetch it once
- Foreign stocks are converted into US dollars; we also collect the whole market (S&P 500), each company's sector and size, and the interest rate on safe government bills
Say: Risk is built from history, so step one is getting clean history. We start in June 2012 because that is when the last of our 10 stocks, Meta, started trading. That gives about 3,600 trading days for each stock. Any stock in the world can be added by name; the platform converts its price into dollars so everything is comparable.

### Same 14 years, very different journeys
- One dollar put into each stock in June 2012 grew to anything from $4 (Exxon) to $782 (Nvidia)
- Stocks move very differently, so the mix we hold changes how much we can lose: that is what the rest of this project measures
Image: slides_assets/m1_growth_of_1_dollar.png
Say: Each line is one dollar invested in one stock in June 2012. The scale is logarithmic: each step up the axis is ten times more money. Nvidia, highlighted, turned one dollar into almost eight hundred; Exxon into four. Big winners also tend to have the wildest swings, and those swings are exactly what risk management is about.

## Module 2: Cleaning and returns

### Step 2: clean the data before trusting it
- Every stock is put on the same trading days; a missing price is filled with the last known one (at most 5 days in a row)
- Prices stuck at the same value for days are flagged as likely glitches, and every change is written to a log
- Prices become daily returns: the % move each day (we use "log" returns, as the brief asks)
- Six automatic checks, all passing: no missing dates, weights add to 100%, returns line up with prices, no impossible values
Say: Bad data gives confident wrong answers, so this step is about trust. Nothing is changed silently: the dashboard shows every option, the effect of each choice, and a log of every fix. For our 10 large US stocks the data was already clean, which is itself a useful result: zero gaps, zero stale prices, all six checks green.

### Clipping extremes would erase the days that matter most
- "Winsorizing" means capping the most extreme days; cutting the top and bottom 1% would change 74 of Apple's days
- They cluster in real crashes (COVID 2020, the April 2025 tariff shock), exactly what risk must see: so clipping is off by default
Image: slides_assets/m2_winsorizing_hides_crashes.png
Say: Each red dot is a day that clipping would have changed. They are not typos; they are the market's worst and best days. Statisticians often clip outliers to make averages stable, but in risk management the outliers are the whole point. We keep the option, and a custom formula box, for experiments, but the default keeps every real day.

## Module 3: Portfolio

### Step 3: combine the stocks into one portfolio
- A portfolio is the basket we actually hold: $10M split across the 10 stocks (10% each by default, or any split we choose)
- Every month we trade back to that split ("rebalancing"); otherwise the winners quietly take over the basket
- Each day we track its value, its profit or loss in dollars, and its "drawdown": how far it is below its best value so far
- Since 2012 it grew 31.6% a year, against 15.2% for the whole market (S&P 500)
Say: Now the ten stocks become one thing we own. The settings form decides how the money is split and how often we tidy it back up. Everything that follows, every risk number, is about this one basket. The dashboard lets you change the split, allow betting against stocks, cap any one stock, set trading costs, and choose whether the $10M is what we hold today or what we started with.

### Even a winning portfolio fell by a third, twice
- Despite strong growth, it lost 35% in five weeks of COVID (2020) and 33% over 2022
- Big gains come with big falls: the next modules put a number on that risk before it happens
Image: slides_assets/m3_drawdown.png
Say: This is drawdown: each day, how far the portfolio is below its best value so far. Zero means a new high. In March 2020 it fell 35% in 23 trading days and took another 52 days to recover. In 2022 the fall was slower but lasted a full year. If you only looked at the 31% a year average, you would never guess these episodes. Risk management is about the episodes, not the average.

### Rebalancing cut the worst fall from 60% to 35%
- Never rebalancing: 38.9% a year, but a worst fall of 59.5%, because Nvidia and Tesla grew to dominate the basket
- Monthly rebalancing back to 10% each: 31.6% a year, worst fall 34.9%
- Splitting by company size: 24.9% a year, worst fall 39.7%; splitting by calmness: 26.6% a year, worst fall 33.7%
- Each of these is one switch on the Portfolio page
Say: Same ten stocks, different rules, very different rides. Buy and hold made the most money in hindsight, but only because two stocks happened to soar; it also came closest to losing well over half its value. Monthly rebalancing keeps the basket balanced and nearly halves the worst fall. The choice of rules is itself a risk decision.

## Module 4: Volatility

### Step 4: measure how jumpy the market is right now
- Volatility is the typical size of a day's move: our portfolio's is about 14.6% a year today, roughly 0.9% on a normal day
- Four ways to estimate it, simplest to smartest: a rolling average; EWMA (recent days count more); GARCH (also drifts back to normal); GJR-GARCH (also knows bad days hit harder)
- They disagree today, from 12.1% to 14.6% a year: and over the next 10 days the GARCH models expect it to rise towards its long-run 22%
- All four plug into the same slot, so the risk numbers in the next step can use any of them
Say: An average over 14 years would say our portfolio moves about 22% a year. But risk is about now, and now is calmer than average. The rolling model weighs the last three months equally; EWMA lets old days fade; GARCH adds the idea that calm and storms both pass; GJR adds that falls stir things up more than rises. On the dashboard you can change each model's settings, including the EWMA memory the brief asks for.

### Bad days cluster together
- In early 2020 the portfolio's normal daily range widened about fivefold within weeks, then took months to shrink back
- 66 of the 77 days it lost more than 3% fell in the stormiest third of days
Image: slides_assets/m4_clustering.png
Say: The grey line is the portfolio's daily return; the shaded band is the range the GJR model expected, plus or minus two volatilities. Notice the band is not fixed: it balloons in March 2020 and then slowly deflates. Red dots are days that broke the band. Storms come in clusters, like weather, which is why a risk number based on a fixed long-term average would be badly wrong in a crisis.

### A big fall makes the next days wilder
- After a day below -3%, the next 5 days moved 2.19% on average; after a quiet day, only 0.85%
- Falls stir up more than rises of the same size (2.19% vs 1.83%): this is the "leverage effect" GJR-GARCH captures
Image: slides_assets/m4_leverage.png
Say: This chart uses no model at all, just the data. We group days by how much the portfolio moved, then look at how big the following week's moves were. Big days of either sign are followed by wild weeks, but falls more so than rises. The GJR-GARCH model measures this asymmetry with one number, gamma, which comes out at 0.15 against only 0.02 for ordinary shocks. And once we divide each day by the model's volatility, the extreme-day score (kurtosis) drops from 12.1 to 4.5, close to a normal bell curve's 3: the model explains most of the wildness.

## Module 5: VaR and Expected Shortfall

### Step 5: on a bad day, how much could we lose?
- Value at Risk (VaR): "on 99 days out of 100 we won't lose more than this". Today: $297K tomorrow (3.0% of $10M)
- Expected Shortfall (ES): "on that 1 bad day in 100, we lose this much on average". Today: $338K
- How: replay the last 500 days on today's portfolio, rescaled to today's volatility, and read off the worst ones
- Over 10 days: VaR $939K (the Basel shortcut: 1-day x √10)
Say: VaR turns all our work into one number a manager can act on. We take the last 500 trading days, imagine each one happening again tomorrow to the basket we hold now, and line them up from worst to best. The 5th worst out of 500 is our 99% VaR; the average of the worst five is the Expected Shortfall. Before replaying, each old day is rescaled to today's volatility, so a calm-year day counts for more if today is stormy, and less if today is calm.

### 500 possible tomorrows
- Most replayed days are small gains or losses; only a handful sit beyond the VaR line in the left tail
- VaR marks the edge of the cliff ($297K), Expected Shortfall the average depth of the fall ($338K)
Image: slides_assets/m5_scenarios.png
Say: Each bar counts how many of the 500 replayed days would give a profit or loss of that size tomorrow. The dashed teal line is VaR: only 1% of scenarios fall to its left. The red line is Expected Shortfall: the average of those worst scenarios. Regulators increasingly prefer ES because it looks inside the tail rather than stopping at its edge.

### Scaled VaR reacted to COVID within days; plain history did not
- Plain history kept VaR near $600K while losses reached $1.4M: 6 breaches in 4 weeks of March 2020
- VaR rescaled by GJR-GARCH jumped to $2.5M at the peak and was breached once
Image: slides_assets/m5_rolling_2020.png
Say: Each line is the VaR we would have published every evening in 2020, computed only with data available at the time. Grey bars are what actually happened the next day. Plain history treats a crisis day and a calm day alike, so its VaR barely moved and was broken again and again. The scaled VaR saw volatility explode and raised its warning straight away. Over the whole 12 years, all four models were exceeded on about 1% of days, as designed; the next module tests whether those exceptions came at the right times.

### Four models, one answer range
- Today's 1-day 99% VaR: plain history $337K, EWMA $247K, GARCH $279K, GJR-GARCH $297K
- Plain history is highest because its 500 days still include the April 2025 tariff crash; the scaled models see a calmer today
- Confidence and window matter too: 95% gives 1.5%, 99% gives 3.0%, 99.5% gives 3.3% of value (500 days)
Say: There is no single true VaR; it depends on the method and its settings. The dashboard lets you change the model, the confidence level and the window, and shows the brief's three-by-three grid of confidence against window. All five of the brief's VaR checks pass: VaR is positive, grows with confidence, the 10-day figure exceeds the 1-day one, ES exceeds VaR, and VaR doubles from calm to stormy periods (2.5% against 5.0%).

## Module 6: Backtesting and model comparison

### Step 6: did the forecasts hold up?
- Backtesting compares the VaR we would have published each evening with the loss that actually followed
- At 99% a good model is beaten on about 1 day in 100 (an "exception"): over 12 years, about 31 days
- Three tests: the right number of exceptions (Kupiec), at random times rather than in clumps (Christoffersen), and both together
- Regulators' traffic light: 0-4 exceptions in the last 250 days is green, 5-9 yellow, 10 or more red
Say: A forecaster who says 10% chance of rain should see rain on about one day in ten. VaR is the same: at 99% we should be surprised on about one day in a hundred. We replay 12 years of evenings, each time using only the data known that evening, and count the surprises. Then we ask two questions: is the number right, and do the surprises come at random, or in clumps? Clumps mean the model was slow to notice that the weather had changed.

### Plain history's misses come in clumps
- All four models were beaten about the right number of times (32 to 36 against 31 expected)
- But plain history's misses bunch up in every storm, so it fails the timing test; GJR-scaled misses are spread out
Image: slides_assets/m6_exception_timeline.png
Say: Each tick is a day the actual loss beat the VaR. The bottom row is plain historical simulation: its ticks come in clumps, in August 2015, early 2018, March 2020 and April 2025, because it takes weeks to notice a storm. The top row is VaR rescaled by GJR-GARCH: the same number of ticks, but spread out. The clustering test gives plain history a p-value of 0.001, a clear fail, and GJR 0.06, a pass. Plain history also sat in the regulators' yellow zone on 980 days, against 262 for GJR.

### GJR-GARCH scaling is the most reliable model
- Ranking at 99%: 1 GJR-scaled, 2 EWMA-scaled, 3 GARCH-scaled, 4 plain history; from 2014 only GJR passes all three tests
- Robustness: starting in May 2015 (the brief's 750 days), GJR misses the timing test by a hair (p 0.046 vs 0.05), so no model passes everything; plain history still fails clearly
- At 95% the three scaled models all pass; plain history fails the timing test at both levels
- All four end in the green zone today; GJR also has one of the lowest average VaRs ($363K), so it protects without over-reserving
Say: This is the brief's model comparison. We rank models first by whether they pass every test, then by how close their exception count is to the expected one, then by how little money they tie up on average. GJR-GARCH scaling wins: it is the model that both reacts to storms and knows that falls stir up more than rises. One honest caveat: the margin is thin. If we start the test a year later, as in the brief's example, GJR just misses the timing test, so we call it the most reliable model, not the only good one. What never changes is that plain history fails. GJR is our recommended model, and the one the dashboard uses by default.

## Module 7: Stress testing

### Step 7: what if a crisis happened tomorrow?
- VaR describes a normal bad day (1 in 100); a stress test asks about the days VaR is not built for, like a fire drill
- Real crises replayed on the basket we hold today: 2008, COVID 2020, inflation 2022, banking 2023, the tech selloff and the April 2025 tariff shock
- Made-up shocks: the market falls 5, 10 or 20%; volatility doubles; correlations jump so everything falls together; a sector crashes; or our own moves
- Stocks that did not exist in 2008 (Meta, Tesla) get a stand-in: their sensitivity to the market ("beta") times what the market did
Say: Every risk model is built on recent history, so it can be blind to rare disasters. Stress testing deliberately looks at those disasters. We take today's holdings, as they are right now, and ask what each crisis would do to them, day by day. On the dashboard every shock size is a slider, and you can type your own move for each stock.

### Replaying 2008 on today's portfolio would cost $4.4M
- 2008 would cost 44% of the portfolio and COVID 35%; a plain 20% market fall costs 22%, because our stocks move about 1.1 times as much as the market
- Not every crisis hurts: in the 2023 banking scare this tech-heavy basket would have gained 1.6%
Image: slides_assets/m7_scenarios.png
Say: Teal bars are real crises replayed, grey bars are made-up shocks. The worst case is the 2008 financial crisis: holding today's ten stocks from the Lehman collapse to the market bottom would lose $4.4 million out of $10 million. Compare that with VaR: a 99% one-day VaR of about $300K is the right answer to a different question. A crisis is many bad days in a row, and that is what stress tests capture.

### In a crisis year, VaR is three times bigger
- Today's 1-day 99% VaR is 3.0% of value ($297K); measured on the worst year in history (to December 2008) it is 9.6% ($960K)
- Doubling volatility doubles VaR; pushing correlations halfway to 1 raises it by 41%, because diversification stops working
- The most exposed stocks are the most market-sensitive: Tesla (beta 2.3) and Nvidia (1.9); Exxon (0.2) and UnitedHealth (0.3) barely move
Say: Regulators ask banks for a "stressed VaR": the same calculation, but as if the next year looked like the worst year on record. For our portfolio that is about three times today's number. The correlation shock is the subtle one: in normal times our ten stocks partly offset each other, but in a panic they all fall together, and the safety from mixing them disappears.

## Module 8: Where the risk comes from, and decision tools

### Two stocks carry over a third of the risk
- Tesla and Amazon each hold 10% of the money but carry 20% and 17% of the Expected Shortfall; Exxon and UnitedHealth carry under 5% each
- Mixing ten stocks saves $188K of risk (38%) compared with adding up each stock's risk on its own
Image: slides_assets/m8_risk_share.png
Say: VaR is one number for the whole basket; here we split it, like splitting a restaurant bill by what each person ate. Grey bars are each stock's share of the money, teal bars its share of the risk on the worst days. Tesla and Amazon punch well above their weight; Exxon and UnitedHealth, which move little with the rest, punch below. And because the stocks do not all fall at once, the basket's risk is 38% lower than the sum of its parts: that is diversification, measured in dollars.

### Decision tools: check a trade before making it
- What-if: buying $1M more Apple, paid for by trimming the other nine, would cut VaR from $307K to $293K
- Best hedge: shorting about $10M of the S&P 500 tracker cuts VaR by 59%; the best single stock to short is Tesla ($2.5M, 45% less VaR)
- Optimizer (at most 25% per stock): the lowest-risk split cuts Expected Shortfall from $330K to $229K, but past return falls from 29% to 21% a year
- One button applies the optimized split to the whole dashboard
Say: These tools turn risk numbers into decisions. Before a trade, the what-if shows its effect on VaR and ES. The hedge finder tries every possible offsetting position and ranks them by how much they cut VaR. The optimizer searches for the split of money with the lowest Expected Shortfall. The trade-off is visible: less risk means less return, and a split tuned to the last two years is no guarantee for the next crisis. The tool informs the decision; it does not make it.

## Conclusion

### What we learned about managing this portfolio's risk
- On a normal bad day (1 in 100) the $10M portfolio can lose about $300K; in a crisis year that becomes about $960K, and a 2008 replay costs $4.4M
- Risk changes over time and storms cluster, so VaR must follow today's volatility: GJR-GARCH scaling was the most reliable in the backtests, and plain history failed them from every start date
- Plain historical VaR has the right long-run count of misses but fails exactly when it matters, in the first weeks of a crisis
- The risk is concentrated: Tesla and Amazon drive over a third of it, and rebalancing monthly nearly halved the worst fall
Say: To sum up: we built a platform that collects and cleans data for any stock in the world, builds the portfolio, measures volatility four ways, computes VaR and Expected Shortfall four ways, tests those forecasts against twelve years of reality, stress-tests the portfolio against real and imagined crises, and shows where the risk comes from and what to do about it. The headline lesson is that a risk number is only as good as its ability to react: the model that follows today's volatility, and knows that falls stir up more than rises, is the one that held up.
