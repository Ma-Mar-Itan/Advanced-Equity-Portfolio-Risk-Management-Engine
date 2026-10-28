import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = "C:/Users/malek/Desktop/HomeBase/Job/QFI/QFI Deliverables/V2";
const RUNTIME_ROOT = "C:/Users/malek/.cache/codex-runtimes/codex-primary-runtime/dependencies";
const SKILL_DIR = "C:/Users/malek/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11618/skills/presentations";
const BUILD = path.join(ROOT, ".comprehensive-deck-build");
const OUTPUT = path.join(ROOT, "presentation_mockups", "QFI_Advanced_Risk_Management_Comprehensive_Swiss_v4.pptx");

process.env.RUNTIME_NODE_MODULES = path.join(RUNTIME_ROOT, "node", "node_modules");
process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES = process.env.RUNTIME_NODE_MODULES;

const artifactPath = path.join(RUNTIME_ROOT, "node", "node_modules", "@oai", "artifact-tool", "dist", "artifact_tool.mjs");
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactPath).href);
const { finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR, "container_tools", "artifact_tool_utils.mjs")).href);

const R = JSON.parse(await fs.readFile(path.join(ROOT, "report_assets", "results.json"), "utf8"));
const PERF = JSON.parse(await fs.readFile(path.join(ROOT, "slides_assets", "performance", "performance_data.json"), "utf8"));
const CHART_DIR = path.join(ROOT, "slides_assets", "dashboard_charts");
const imageNames = {
  data: "data_01_same_years_very_different_journeys.png",
  cleanReturns: "cleaning_02_aapl_every_daily_return.png",
  cleanVol: "cleaning_03_rolling_volatility.png",
  portfolioValue: "portfolio_01_portfolio_value_against_the_market.png",
  pnl: "portfolio_03_daily_profit_and_loss.png",
  returns: "portfolio_04_daily_returns.png",
  hs: "var_01_historical_portfolio_return_p_l_distribution.png",
  volModels: "volatility_01_portfolio_four_estimates_of_the_same_volatility.png",
  garchForecast: "volatility_05_forecast_for_the_next_10_days.png",
  gjr: "volatility_04_leverage_effect_in_the_models.png",
  backtest: "backtesting_01_actual_p_l_against_var.png",
  exceptions: "backtesting_03_exceptions_by_model.png",
  stress: "stress_01_scenario_ranking_loss_on_today_s_portfolio.png",
  decisions: "decisions_01_the_split_before_and_after.png",
  drawdown: "portfolio_02_drawdown_distance_below_the_previous_peak.png",
  regimes: "volatility_07_volatility_regimes_compared.png",
  stressVar: "stress_02_stressed_var_against_today_s_var.png",
  stressStock: "stress_03_2008_financial_crisis_loss_by_stock.png",
};
const chartTitles = {
  data: "Growth of $1 invested in each stock",
  cleanReturns: "Apple daily returns",
  cleanVol: "Rolling annualized volatility: Apple vs other holdings",
  portfolioValue: "Portfolio value vs SPY benchmark",
  pnl: "Daily portfolio P&L",
  returns: "Daily portfolio returns",
  hs: "Historical portfolio return and P&L distribution",
  volModels: "Annualized volatility by model",
  garchForecast: "10-day volatility forecast by model",
  gjr: "GARCH vs GJR-GARCH leverage response",
  backtest: "Actual daily P&L vs GJR-HS VaR",
  exceptions: "Actual vs expected exceptions by model",
  stress: "Stress scenario loss ranking",
  decisions: "Portfolio weights before and after optimization",
  drawdown: "Portfolio drawdown from the previous peak",
  regimes: "Volatility regimes",
  stressVar: "Stressed VaR vs current VaR",
  stressStock: "2008 crisis replay loss by stock",
};
const images = {};
for (const [key, name] of Object.entries(imageNames)) images[key] = new Uint8Array(await fs.readFile(path.join(CHART_DIR, name)));

const C = {
  white: "#FFFFFF", paper: "#F5F5F2", ink: "#111111", dark: "#353535",
  mid: "#707070", light: "#D8D8D4", pale: "#EEEEEA", red: "#B42318",
  teal: "#155E63", softTeal: "#DDE8E7", softRed: "#F3DEDA", green: "#1B6B50",
};
const FONT = "Aptos";
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
presentation.theme.defaultFont = FONT;
presentation.theme.colorScheme = {
  name: "QFI Swiss Monochrome",
  themeColors: { bg1: C.white, bg2: C.paper, tx1: C.ink, tx2: C.mid, dk1: C.ink, lt1: C.white,
    dk2: C.dark, lt2: C.paper, accent1: C.teal, accent2: C.red, accent3: C.green,
    accent4: "#8C8C8C", accent5: "#B0B0B0", accent6: "#D0D0D0", hlink: C.teal, folHlink: C.red },
};

function addRect(slide, left, top, width, height, fill, lineFill = fill, lineWidth = 0) {
  return slide.shapes.add({ geometry: "rect", position: { left, top, width, height }, fill,
    line: { style: "solid", fill: lineFill, width: lineWidth } });
}
function addText(slide, text, left, top, width, height, opts = {}) {
  const shape = slide.shapes.add({ geometry: "textbox", position: { left, top, width, height }, fill: "none",
    line: { style: "solid", fill: "none", width: 0 } });
  shape.text = String(text);
  shape.text.style = { fontFamily: FONT, fontSize: opts.fontSize ?? 18, bold: opts.bold ?? false,
    color: opts.color ?? C.ink, alignment: opts.alignment ?? "left", verticalAlignment: opts.verticalAlignment ?? "top" };
  return shape;
}
function addImage(slide, key, left, top, width, height, alt) {
  addRect(slide, left - 1, top - 1, width + 2, height + 2, C.white, C.light, 1);
  addText(slide, chartTitles[key] ?? alt, left + 12, top + 7, width - 24, 20, { fontSize: 12, bold: true, color: C.dark });
  slide.images.add({ blob: images[key], contentType: "image/png", alt, fit: "contain", position: { left, top: top + 29, width, height: height - 31 } });
}
function pct(value, digits = 1) { return `${(value * 100).toFixed(digits)}%`; }
function money(value, digits = 0) {
  const abs = Math.abs(value); const sign = value < 0 ? "−" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(digits || 2)}M`;
  return `${sign}$${(abs / 1000).toFixed(digits)}K`;
}
function baseSlide(title, section, subtitle = "") {
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addText(slide, section.toUpperCase(), 54, 28, 470, 22, { fontSize: 10, bold: true, color: C.red });
  addText(slide, title, 54, 64, 1110, 54, { fontSize: 34, bold: true });
  if (subtitle) addText(slide, subtitle, 54, 120, 1130, 30, { fontSize: 15, color: C.dark });
  addRect(slide, 54, 157, 1172, 3, C.ink);
  return slide;
}
function finish(slide, number, note) {
  addRect(slide, 54, 674, 1172, 1, C.light);
  addText(slide, `QFI risk engine  |  saved data through ${R.data.end}`, 54, 682, 900, 18, { fontSize: 8, color: C.mid });
  addText(slide, String(number).padStart(2, "0"), 1162, 680, 64, 18, { fontSize: 9, bold: true, alignment: "right" });
  slide.speakerNotes.text = note;
  slide.speakerNotes.setVisible(true);
}
function metric(slide, value, label, left, top, width, color = C.ink) {
  addText(slide, value, left, top, width, 42, { fontSize: 28, bold: true, color });
  addText(slide, label, left, top + 42, width, 34, { fontSize: 12, color: C.mid });
}
function bullet(slide, title, body, left, top, width, accent = C.red) {
  addRect(slide, left, top + 4, 4, 48, accent);
  addText(slide, title, left + 16, top, width - 16, 24, { fontSize: 15, bold: true });
  addText(slide, body, left + 16, top + 25, width - 16, 42, { fontSize: 12, color: C.dark });
}
function phaseNumber(slide, n) {
  addText(slide, String(n).padStart(2, "0"), 1102, 174, 112, 62, { fontSize: 52, bold: true, color: C.ink, alignment: "right" });
}
function callout(slide, text, left, top, width, height, fill = C.paper, accent = C.ink) {
  addRect(slide, left, top, width, height, fill);
  addRect(slide, left, top, 5, height, accent);
  addText(slide, text, left + 18, top + 5, width - 30, height - 10, { fontSize: 14, bold: true, color: C.dark, verticalAlignment: "middle" });
}

const hs = R.var_today.find((x) => x.model === "HS");
const ewma = R.var_today.find((x) => x.model === "EWMA-HS");
const garch = R.var_today.find((x) => x.model === "GARCH-HS");
const gjr = R.var_today.find((x) => x.model === "GJR-HS");
const gjrBt = R.bt99.find((x) => x.model === "GJR-HS");

// 1. Cover
{
  const s = presentation.slides.add(); s.background.fill = C.white;
  addText(s, "QFI INTERNSHIP PROJECT", 58, 38, 420, 24, { fontSize: 11, bold: true, color: C.red });
  addText(s, "Advanced Equity Portfolio\nRisk Management", 58, 126, 840, 124, { fontSize: 48, bold: true });
  addRect(s, 58, 280, 1160, 5, C.ink);
  addText(s, "VaR, Expected Shortfall, volatility scaling, backtesting and stress testing", 58, 308, 970, 52, { fontSize: 21, color: C.dark });
  addText(s, money(gjr.var * R.value), 58, 455, 220, 58, { fontSize: 42, bold: true, color: C.teal });
  addText(s, "99% one-day GJR-HS VaR", 58, 510, 260, 24, { fontSize: 13, color: C.mid });
  addText(s, money(R.stress[0].loss * R.value), 390, 455, 250, 58, { fontSize: 42, bold: true, color: C.red });
  addText(s, "2008 crisis replay loss", 390, 510, 260, 24, { fontSize: 13, color: C.mid });
  addText(s, `${gjrBt.exceptions} / ${gjrBt.expected.toFixed(1)}`, 728, 455, 260, 58, { fontSize: 42, bold: true });
  addText(s, "actual / expected exceptions", 728, 510, 290, 24, { fontSize: 13, color: C.mid });
  addText(s, "How much can the portfolio lose, how reliable is that estimate, and what should we do about it?", 58, 590, 1020, 54, { fontSize: 19, bold: true, color: C.dark });
  finish(s, 1, "Hello everyone. Today I will present a risk engine built for a ten-stock equity portfolio. The central question is simple: how much can the portfolio lose, how reliable is that estimate, and what should a risk manager do with the result?");
}

// 2. Scope and vocabulary
{
  const s = baseSlide("Project scope and the language of risk", "OVERVIEW", "A portfolio combines investments; risk management measures and controls the losses that can follow");
  const terms = [
    ["Portfolio", "A group of investments held together; each holding has a weight."],
    ["Equity portfolio", "A portfolio made mainly of listed company shares."],
    ["VaR", "A loss threshold for a stated horizon and confidence level, not a maximum loss."],
    ["Expected Shortfall", "The average loss after the VaR threshold has been crossed."],
    ["Volatility", "How widely returns move from day to day."],
    ["Drawdown", "The fall from a previous portfolio peak to a later low."],
  ];
  terms.forEach((t, i) => bullet(s, t[0], t[1], 58 + (i % 2) * 570, 184 + Math.floor(i / 2) * 112, 510, i < 2 ? C.teal : C.red));
  addRect(s, 58, 522, 1138, 1, C.light);
  const phases = ["Collect", "Clean", "Build", "Measure", "Scale", "Forecast", "Test", "Compare", "Stress", "Decide"];
  phases.forEach((p, i) => {
    const left = 58 + i * 113;
    addText(s, String(i + 1).padStart(2, "0"), left, 550, 82, 24, { fontSize: 11, bold: true, color: C.red });
    addText(s, p, left, 578, 92, 28, { fontSize: 14, bold: true });
  });
  finish(s, 2, "A portfolio is a collection of investments. Risk management does not remove all risk; it measures possible losses, checks whether they are acceptable, and defines what to do when they become too large. VaR marks a warning line, while Expected Shortfall describes the average loss beyond that line.");
}

// 3. Phase 1
{
  const s = baseSlide("Phase 1  Data collection", "PHASE 01", "Adjusted prices, benchmark data, sectors, weights and the risk-free rate create the raw input"); phaseNumber(s, 1);
  addImage(s, "data", 54, 182, 780, 294, "Growth of one dollar for the ten portfolio stocks from the live dashboard");
  metric(s, R.data.days.toLocaleString(), "shared trading days", 872, 262, 290, C.teal);
  addText(s, "same dates across every holding", 872, 326, 290, 22, { fontSize: 11, color: C.mid });
  metric(s, "10 + SPY", "stocks and benchmark", 872, 360, 290);
  bullet(s, "Adjusted close", "Corrects splits and dividends so corporate actions do not create false returns.", 54, 502, 350, C.teal);
  bullet(s, "Returns and weights", "Returns make different stock prices comparable; weights translate each move into portfolio impact.", 432, 502, 350, C.teal);
  bullet(s, "Reference inputs", "SPY, the short-term risk-free rate and sector classifications support comparison and stress testing.", 810, 502, 382, C.teal);
  callout(s, "Adjusted prices are aligned across all holdings before portfolio returns are calculated", 54, 614, 1138, 42, C.softTeal, C.teal);
  finish(s, 3, "Phase 1 collects adjusted daily prices for Apple, Microsoft, Nvidia, JPMorgan, ExxonMobil, Amazon, Meta, Alphabet, Tesla and UnitedHealth, plus SPY and the risk-free rate. Adjusted prices prevent splits and dividends from becoming false losses. The local cache keeps the process reproducible when a provider is unavailable.");
}

// 4. Phase 2
{
  const s = baseSlide("Phase 2  Data cleaning", "PHASE 02", "The portfolio is only credible when every stock return refers to the same trading day"); phaseNumber(s, 2);
  addImage(s, "cleanReturns", 54, 182, 610, 178, "Daily cleaned returns from the dashboard");
  addImage(s, "cleanVol", 54, 374, 610, 184, "Rolling volatility after cleaning from the dashboard");
  addText(s, "WHY THIS MATTERS", 714, 190, 300, 20, { fontSize: 10, bold: true, color: C.red });
  bullet(s, "Comparable prices", "Split and dividend adjustments prevent corporate actions from creating false returns.", 714, 224, 462, C.teal);
  bullet(s, "One shared calendar", "Every stock movement refers to the same trading date before the portfolio is combined.", 714, 318, 462, C.teal);
  bullet(s, "Real shocks preserved", "Genuine crashes remain in the sample because they contain the tail-risk information we need.", 714, 412, 462, C.red);
  bullet(s, "Model-ready output", "Clean stock returns feed the portfolio return series and the rolling risk models.", 714, 506, 462, C.teal);
  callout(s, "Output: clean prices, clean returns, portfolio returns and rolling volatility", 714, 602, 462, 48, C.paper, C.ink);
  finish(s, 4, "Phase 2 aligns the trading calendar, checks missing and stale prices, and converts prices into log returns. Winsorization is reserved for verified errors because genuine market crashes belong in the risk sample. The output is a clean price matrix, return matrix, portfolio return series and rolling volatility series.");
}

// 5. Phase 3
{
  const s = baseSlide("Phase 3  Portfolio construction", "PHASE 03", "Weights, initial value and rebalancing turn ten stock returns into one investable portfolio"); phaseNumber(s, 3);
  addImage(s, "portfolioValue", 54, 182, 720, 260, "Portfolio value versus SPY from the live dashboard");
  addImage(s, "pnl", 54, 468, 354, 174, "Daily portfolio profit and loss");
  addImage(s, "returns", 420, 468, 354, 174, "Daily portfolio returns");
  metric(s, "$10M", "initial reporting value", 828, 214, 330, C.teal);
  metric(s, "10%", "starting weight per stock", 828, 308, 330);
  bullet(s, "Equal weight", "Every stock starts near the same money weight.", 828, 410, 330, C.teal);
  bullet(s, "User or market-cap weight", "The engine also accepts custom allocations or weights based on company size.", 828, 482, 330, C.teal);
  bullet(s, "Monthly rebalance", "Reset drift toward the target allocation; more frequent trading would add costs.", 828, 570, 330, C.teal);
  finish(s, 5, "Phase 3 combines the cleaned returns into one portfolio. The engine supports equal, user-defined, market-cap and optional long-short weights. Daily return is the percentage movement, daily value compounds that movement, and daily P&L expresses it in dollars. The two lower charts show P&L and returns at the same time.");
}

// 6. Phase 4
{
  const s = baseSlide("Phase 4  Historical Simulation VaR", "PHASE 04", "Rank the recent portfolio outcomes and read the loss cutoff directly from history"); phaseNumber(s, 4);
  addImage(s, "hs", 54, 182, 742, 304, "Historical portfolio return and profit-and-loss distribution with VaR thresholds");
  metric(s, money(hs.var * R.value), "99% one-day VaR", 838, 222, 330, C.teal);
  metric(s, money(hs.es * R.value), "Expected Shortfall", 838, 318, 330, C.red);
  metric(s, money(hs.var10 * R.value), "99% ten-day VaR", 838, 414, 330);
  const windows = [["250", "about 1 year"], ["500", "about 2 years"], ["750", "about 3 years"]];
  windows.forEach((w, i) => { const left = 54 + i * 250; addText(s, w[0], left, 526, 100, 34, { fontSize: 23, bold: true }); addText(s, `days\n${w[1]}`, left + 88, 528, 134, 44, { fontSize: 12, color: C.mid }); });
  callout(s, "Confidence choices: 95%, 99% and 99.5%. Higher confidence moves deeper into the loss tail.", 54, 600, 1114, 48, C.softRed, C.red);
  finish(s, 6, "Historical Simulation uses actual past portfolio outcomes. A 99 percent one-day VaR of about 337 thousand dollars marks the start of the worst one percent of days in the selected 500-day window. Expected Shortfall is larger because it averages the losses beyond that threshold. VaR is not a maximum possible loss.");
}

// 7. Phase 5
{
  const s = baseSlide("Phase 5  EWMA volatility scaling", "PHASE 05", "Recent shocks receive more weight, so old returns are resized to today's volatility"); phaseNumber(s, 5);
  addImage(s, "volModels", 54, 182, 756, 300, "Rolling, EWMA, GARCH and GJR-GARCH volatility estimates");
  metric(s, "0.94", "daily decay factor, lambda", 852, 214, 320, C.teal);
  metric(s, pct(R.vol_today.EWMA), "current annualized EWMA volatility", 852, 314, 320);
  metric(s, money(ewma.var * R.value), "EWMA-scaled 99% VaR", 852, 414, 320, C.red);
  bullet(s, "What lambda means", "Each day keeps 94% of yesterday's variance estimate and adds 6% from the newest squared return.", 54, 520, 526, C.teal);
  bullet(s, "Why scale", "A historical shock from a calm period should become larger when today's market is more volatile, and smaller when it is calmer.", 618, 520, 550, C.teal);
  callout(s, "EWMA reacts quickly, but a lower current estimate still has to earn trust in backtesting", 54, 618, 1114, 38, C.softTeal, C.teal);
  finish(s, 7, "EWMA stands for Exponentially Weighted Moving Average. Lambda equals 0.94 for daily data, so the model remembers most of yesterday's variance while giving the newest observation meaningful weight. The model standardizes old returns by their historical volatility and rescales them by today's volatility.");
}

// 8. Phase 6
{
  const s = baseSlide("Phase 6  GARCH volatility scaling", "PHASE 06", "Volatility clusters and then decays gradually instead of resetting each day"); phaseNumber(s, 6);
  addImage(s, "garchForecast", 54, 182, 756, 274, "Ten-day volatility forecast from rolling, EWMA, GARCH and GJR-GARCH models");
  metric(s, pct(R.vol_today.GARCH), "current GARCH volatility", 850, 214, 322, C.teal);
  metric(s, money(garch.var * R.value), "GARCH-scaled 99% VaR", 850, 310, 322, C.red);
  metric(s, `${R.garch.GARCH["half-life (days)"].toFixed(1)} days`, "estimated shock half-life", 850, 406, 322);
  bullet(s, "GARCH(1,1)", "Today's variance depends on one recent squared shock and one previous variance estimate.", 54, 500, 350, C.teal);
  bullet(s, "Conditional volatility", "The risk estimate changes with information available at that point in time.", 432, 500, 350, C.teal);
  bullet(s, "One-day forecast", "The model projects tomorrow's volatility, then scales the historical returns and tail loss.", 810, 500, 362, C.teal);
  callout(s, `Persistence ${R.garch.GARCH.persistence.toFixed(3)} means volatility shocks fade slowly rather than disappearing immediately`, 54, 616, 1118, 40, C.softTeal, C.teal);
  finish(s, 8, "GARCH models volatility clustering: large moves tend to be followed by large moves. The model estimates conditional volatility for each day and a one-day forecast for tomorrow. Persistence close to one means a shock fades gradually, and the estimated half-life is about one trading month.");
}

// 9. Phase 7
{
  const s = baseSlide("Phase 7  GJR-GARCH volatility scaling", "PHASE 07", "Negative equity shocks can raise future volatility more than positive shocks of the same size"); phaseNumber(s, 7);
  addImage(s, "gjr", 54, 182, 650, 310, "GARCH versus GJR-GARCH leverage effect from the live dashboard");
  metric(s, pct(R.vol_today["GJR-GARCH"]), "current GJR volatility", 760, 200, 390, C.teal);
  metric(s, R.garch["GJR-GARCH"].gamma.toFixed(3), "leverage-effect parameter", 760, 292, 390, C.red);
  metric(s, money(gjr.var * R.value), "GJR-scaled 99% VaR", 760, 384, 390);
  bullet(s, "Asymmetry", "The extra leverage term activates after a negative return.", 54, 526, 332, C.red);
  bullet(s, "Equity relevance", "Bad news often produces more fear and volatility than equally large good news.", 414, 526, 350, C.red);
  bullet(s, "Fit check", `GJR AIC ${Math.round(R.garch["GJR-GARCH"].AIC).toLocaleString()} versus GARCH ${Math.round(R.garch.GARCH.AIC).toLocaleString()}; lower is better on the same sample.`, 792, 526, 376, C.red);
  finish(s, 9, "GJR-GARCH extends GARCH with an asymmetric response. The positive leverage parameter indicates that negative returns increased later volatility more strongly in this sample. A lower AIC supports the relative fit, but the model only becomes useful if its forecasts also perform well out of sample.");
}

// 10. Phase 8
{
  const s = baseSlide("Phase 8  VaR backtesting", "PHASE 08", "Every forecast uses information available before the day whose loss it is tested against"); phaseNumber(s, 8);
  addImage(s, "backtest", 54, 182, 790, 330, "Actual portfolio profit and loss against forecast VaR");
  metric(s, String(gjrBt.exceptions), `exceptions versus ${gjrBt.expected.toFixed(1)} expected`, 884, 204, 298, C.teal);
  metric(s, gjrBt["Kupiec p"].toFixed(3), "Kupiec frequency p-value", 884, 300, 298);
  metric(s, gjrBt["Christoffersen p"].toFixed(3), "independence p-value", 884, 396, 298);
  const tests = [
    ["Kupiec POF", "Is the total exception count plausible?"],
    ["Christoffersen", "Are exceptions independent rather than clustered?"],
    ["Conditional coverage", "Do frequency and timing pass together?"],
    ["Basel traffic light", "Is the recent count green, yellow or red?"],
  ];
  tests.forEach((t, i) => bullet(s, t[0], t[1], 54 + (i % 2) * 566, 540 + Math.floor(i / 2) * 64, 510, i === 3 ? C.green : C.red));
  finish(s, 10, "Backtesting compares each forecast with the loss that occurred afterward. An exception occurs when the actual loss exceeds VaR. Kupiec checks frequency, Christoffersen checks clustering, and conditional coverage checks both. A green traffic-light result is useful, but it does not replace the statistical tests.");
}

// 11. Phase 9
{
  const s = baseSlide("Phase 9  Model comparison", "PHASE 09", "The best model earns its role through validation, not by producing the smallest risk number");
  addImage(s, "exceptions", 54, 182, 536, 300, "Actual and expected exceptions by VaR model");
  const cols = [610, 760, 884, 1000, 1122];
  addRect(s, 602, 180, 586, 44, C.ink);
  ["Model", "Exceptions", "Kupiec", "Independence", "Decision"].forEach((h, i) => addText(s, h, cols[i], 190, i === 3 ? 116 : 100, 28, { fontSize: 11, bold: true, color: C.white }));
  R.bt99.forEach((row, r) => {
    const top = 236 + r * 58; if (r % 2 === 1) addRect(s, 602, top - 6, 586, 50, C.paper);
    addText(s, row.model, cols[0], top, 140, 24, { fontSize: 13, bold: row.rank === 1 });
    addText(s, `${row.exceptions} / ${row.expected.toFixed(1)}`, cols[1], top, 112, 24, { fontSize: 12 });
    addText(s, row["Kupiec p"].toFixed(3), cols[2], top, 90, 24, { fontSize: 12 });
    addText(s, row["Christoffersen p"].toFixed(3), cols[3], top, 108, 24, { fontSize: 12, color: row["Christoffersen p"] < 0.05 ? C.red : C.green });
    addText(s, row["passes all"] ? "PASS" : "REVIEW", cols[4], top, 74, 24, { fontSize: 11, bold: true, color: row["passes all"] ? C.green : C.red });
  });
  callout(s, "Primary: GJR-HS  |  Challenger: EWMA-HS  |  Transparent benchmark: Historical Simulation", 54, 524, 1134, 52, C.softTeal, C.teal);
  bullet(s, "Comparison metrics", "Exceptions, exception ratio, average VaR, VaR volatility, worst loss, Expected Shortfall, p-values and traffic-light zone.", 54, 604, 1130, C.red);
  finish(s, 11, "Phase 9 compares all four models using exception counts, clustering, average risk, stability and Expected Shortfall. GJR-HS ranks first because it passes frequency, independence and joint coverage at the selected level. EWMA remains a fast challenger, and Historical Simulation remains the simplest benchmark.");
}

// 12. Phase 10
{
  const s = baseSlide("Phase 10  Stress testing", "PHASE 10", "VaR supports daily monitoring; stress testing asks whether the portfolio can survive a crisis"); phaseNumber(s, 10);
  addImage(s, "stress", 54, 182, 790, 350, "Historical and hypothetical stress scenario losses ranked from worst to best");
  metric(s, money(R.stress[0].loss * R.value), "2008 crisis replay", 884, 206, 300, C.red);
  metric(s, money(R.stress[1].loss * R.value), "COVID crash replay", 884, 302, 300, C.red);
  metric(s, money(R.stress[0].stressed_var * R.value), "stressed VaR", 884, 398, 300);
  bullet(s, "Historical", "2008, COVID, 2022 inflation, 2023 banking stress and the technology selloff.", 54, 566, 520, C.teal);
  bullet(s, "Hypothetical", "Market falls, doubled volatility, correlation spikes and sector-specific shocks.", 618, 566, 520, C.teal);
  finish(s, 12, "Stress testing asks what would happen to today's portfolio if a severe historical or hypothetical shock occurred. It is not a forecast and it assigns no probability. The 2008 replay produces the largest tested loss, about 4.40 million dollars, far beyond ordinary one-day VaR.");
}

// 13. Portfolio evidence
{
  const s = baseSlide("Strong returns came with a 34.9% drawdown", "RESULTS", "Historical performance is not a forecast; the path reveals the risk taken to achieve it");
  addImage(s, "drawdown", 54, 182, 760, 314, "Portfolio drawdown through time");
  metric(s, pct(R.portfolio["annual return"]), "annualized return", 856, 204, 310, C.teal);
  metric(s, pct(R.portfolio["annual volatility"]), "annualized volatility", 856, 300, 310);
  metric(s, pct(R.portfolio["max drawdown"]), "maximum drawdown", 856, 396, 310, C.red);
  callout(s, `Sharpe ${R.portfolio.sharpe.toFixed(2)}  |  beta ${R.portfolio.beta.toFixed(2)}  |  correlation with SPY ${R.portfolio.correlation.toFixed(2)}`, 54, 536, 1114, 54, C.paper, C.ink);
  bullet(s, "Interpretation", "Ten stocks reduce company-specific risk, but high market correlation leaves the portfolio exposed to broad equity shocks.", 54, 608, 1114, C.red);
  finish(s, 13, "The portfolio delivered strong historical returns, but it also experienced a drawdown close to 35 percent. Beta above one and a 0.90 correlation with SPY show that broad market stress still reaches most holdings at the same time.");
}

// 14. Current risk
{
  const s = baseSlide("Current model choice moves one-day VaR from $240K to $337K", "RESULTS", "All figures use 99% confidence, a one-day horizon and today's $10 million portfolio value");
  addImage(s, "hs", 54, 182, 700, 278, "Historical P&L distribution used to locate VaR and Expected Shortfall");
  const rows = R.var_today;
  rows.forEach((row, i) => {
    const top = 182 + i * 86; addText(s, row.model, 800, top, 132, 28, { fontSize: 14, bold: true });
    addText(s, money(row.var * R.value), 938, top, 120, 28, { fontSize: 18, bold: true, color: C.teal });
    addText(s, money(row.es * R.value), 1064, top, 120, 28, { fontSize: 18, bold: true, color: C.red });
    addText(s, "VaR", 938, top + 28, 80, 20, { fontSize: 9, color: C.mid }); addText(s, "ES", 1064, top + 28, 80, 20, { fontSize: 9, color: C.mid });
    if (i < rows.length - 1) addRect(s, 800, top + 58, 384, 1, C.light);
  });
  callout(s, "Model risk is visible: the method changes the threshold, so governance keeps a primary model, challenger and benchmark", 54, 510, 1130, 60, C.softRed, C.red);
  bullet(s, "Rule", "Expected Shortfall must remain above VaR because it averages losses after the threshold is crossed.", 54, 604, 1130, C.teal);
  finish(s, 14, "The filtered models currently produce lower VaR than unscaled Historical Simulation because recent volatility is below the longer-window level. This difference is model risk. The selected number must therefore be accompanied by a challenger, a benchmark and regular validation.");
}

// 15. Volatility evidence
{
  const s = baseSlide("Volatility changes regime, and downside shocks matter more", "MODEL EVIDENCE", "The models respond to both persistence and asymmetry in equity returns");
  addImage(s, "volModels", 54, 182, 722, 274, "Four volatility estimates through time");
  addImage(s, "regimes", 54, 482, 722, 164, "Calm, normal and stormy volatility regimes");
  metric(s, R.garch["GJR-GARCH"].persistence.toFixed(3), "GJR persistence", 828, 202, 350, C.teal);
  metric(s, `${R.garch["GJR-GARCH"]["half-life (days)"].toFixed(1)} days`, "shock half-life", 828, 300, 350);
  metric(s, R.garch["GJR-GARCH"].gamma.toFixed(3), "downside leverage parameter", 828, 398, 350, C.red);
  bullet(s, "Residual check", `Standardized-residual kurtosis falls from ${R.resid.kurt_raw.toFixed(1)} to ${R.resid.kurt_z.toFixed(1)}, but extreme tails remain.`, 828, 518, 350, C.red);
  finish(s, 15, "The volatility models capture the main regime changes and the slower decay of shocks. GJR-GARCH adds the stronger response after negative returns. Standardization improves the residual distribution, but it does not make extreme tail risk disappear.");
}

// 16. Backtest evidence
{
  const s = baseSlide("GJR-HS is the only model that passes all 99% backtests", "VALIDATION", "A reasonable exception count is not enough when losses still arrive in clusters");
  addImage(s, "backtest", 54, 182, 740, 310, "Actual profit and loss against the GJR-HS VaR forecast");
  const labels = [["Kupiec", gjrBt["Kupiec p"]], ["Independence", gjrBt["Christoffersen p"]], ["Conditional", gjrBt["Coverage p"]]];
  labels.forEach((x, i) => { metric(s, x[1].toFixed(3), `${x[0]} p-value`, 842, 200 + i * 94, 326, x[1] >= 0.05 ? C.green : C.red); });
  callout(s, `34 exceptions versus ${gjrBt.expected.toFixed(1)} expected  |  Basel zone: ${gjrBt.zone.toUpperCase()}`, 54, 530, 1114, 50, C.softTeal, C.green);
  bullet(s, "Boundary", "Passing the historical backtest supports daily use. It does not prove the model will capture a new crisis, liquidity shock or structural break.", 54, 608, 1114, C.red);
  finish(s, 16, "GJR-HS produces 34 exceptions against 31.2 expected. Its p-values do not reject frequency, independence or joint coverage at the five percent level. The model earns the primary role, but the pass is conditional on this sample and must be monitored.");
}

// 17. Stress and concentration
{
  const s = baseSlide("Crisis loss and tail concentration are larger than daily VaR", "STRESS AND ATTRIBUTION", "The worst historical replay removes 44% of value, while two stocks supply 39% of Expected Shortfall");
  addImage(s, "stressVar", 54, 182, 550, 240, "Stressed VaR compared with today's VaR");
  addImage(s, "stressStock", 634, 182, 550, 240, "2008 crisis replay loss by stock");
  metric(s, pct(R.stress[0].loss), "2008 replay loss", 54, 464, 260, C.red);
  metric(s, pct(R.attribution[0].es_share + R.attribution[1].es_share), "TSLA and AMZN share of ES", 350, 464, 300, C.red);
  metric(s, pct(R.attribution[0].weight + R.attribution[1].weight), "their share of capital", 686, 464, 260);
  metric(s, pct(R.diversification.benefit_share), "diversification benefit", 974, 464, 210, C.teal);
  bullet(s, "Decision insight", "Equal money weights do not create equal tail-risk contributions. Risk reduction should target the positions that dominate severe losses.", 54, 578, 1130, C.red);
  finish(s, 17, "The stress tests answer a different question from daily VaR. The 2008 replay removes about 44 percent of portfolio value. Tail attribution also shows that Tesla and Amazon contribute about 39 percent of Expected Shortfall from roughly 21 percent of capital.");
}

// 18. Decisions
{
  const s = baseSlide("The analytics support hedging or reallocation, not automatic trading", "DECISIONS", "Every action changes costs, exposures and the assumptions behind the risk estimate");
  addImage(s, "decisions", 54, 182, 760, 220, "Current and optimized portfolio weights from the dashboard");
  metric(s, pct(R.hedges[0].reduction), "illustrative SPY hedge VaR reduction", 860, 190, 320, C.teal);
  metric(s, money(R.optimizer.compare[1].ES), "optimized-split ES", 860, 286, 320);
  metric(s, money(R.optimizer.compare[0].ES), "current-split ES", 860, 382, 320, C.red);
  bullet(s, "Hedge", `A beta-neutral SPY example uses a ${money(R.hedges[0].amount)} short. It cuts modelled VaR but creates basis, financing and execution risk.`, 54, 456, 520, C.teal);
  bullet(s, "Reallocate", "The historical optimization lowers tail risk but also changes expected return and concentrates the new portfolio in five names.", 618, 456, 550, C.teal);
  callout(s, "Before acting: test liquidity, transaction costs, taxes, borrowing constraints and performance on new data", 54, 602, 1114, 48, C.softRed, C.red);
  finish(s, 18, "The engine supports two possible responses. A broad-market hedge can cut systematic risk, while reallocation can reduce tail contribution from the riskiest positions. Both examples are analytical scenarios, not trade instructions, and both need cost and implementation checks.");
}

// 19. Governance
{
  const s = baseSlide("Risk limits turn model output into a repeatable control process", "GOVERNANCE", "Numbers become useful only when ownership, escalation and review are explicit");
  const steps = [
    ["01", "Monitor", "Calculate primary, challenger and benchmark VaR each day."],
    ["02", "Investigate", "Review every exception, data issue and unexplained model divergence."],
    ["03", "Escalate", "Trigger portfolio review when limits, stress losses or concentration thresholds are breached."],
    ["04", "Decide", "Reduce, hedge or explicitly accept the residual risk with named approval."],
    ["05", "Document", "Record the estimate, evidence, action, owner and follow-up date."],
  ];
  steps.forEach((x, i) => {
    const top = 184 + i * 84; addText(s, x[0], 62, top, 72, 32, { fontSize: 18, bold: true, color: C.red });
    addText(s, x[1], 146, top, 190, 32, { fontSize: 20, bold: true }); addText(s, x[2], 360, top + 2, 780, 44, { fontSize: 15, color: C.dark });
    if (i < steps.length - 1) addRect(s, 146, top + 58, 996, 1, C.light);
  });
  callout(s, "Proposed controls require approval; they are not policies already in force", 54, 612, 1114, 44, C.softRed, C.red);
  finish(s, 19, "The dashboard becomes a control only when the organization defines who monitors it, who investigates exceptions, who approves action and how the decision is recorded. These are proposed governance steps for approval, not existing policy.");
}

// 20. Close
{
  const s = presentation.slides.add(); s.background.fill = C.ink;
  addText(s, "RECOMMENDATION", 58, 42, 300, 24, { fontSize: 10, bold: true, color: C.red });
  addText(s, "Use GJR-HS for daily risk,\nbut manage the crisis exposure separately", 58, 118, 1050, 118, { fontSize: 42, bold: true, color: C.white });
  addRect(s, 58, 274, 1158, 3, C.white);
  const items = [
    ["Primary", "GJR-HS", "Only model to pass frequency, independence and joint coverage at 99%."],
    ["Challenger", "EWMA-HS", "Fast response and a useful second opinion when volatility changes quickly."],
    ["Benchmark", "Historical Simulation", "Transparent loss ranking that keeps the complex models accountable."],
    ["Action", "Review concentration", "TSLA and AMZN supply about 39% of Expected Shortfall from about 21% of capital."],
  ];
  items.forEach((x, i) => {
    const top = 320 + i * 74; addText(s, x[0].toUpperCase(), 58, top, 120, 24, { fontSize: 10, bold: true, color: C.red });
    addText(s, x[1], 194, top - 2, 240, 30, { fontSize: 20, bold: true, color: C.white });
    addText(s, x[2], 458, top, 700, 34, { fontSize: 14, color: "#D7D7D2" });
  });
  addText(s, "Daily VaR is a control threshold, not a crisis-loss ceiling", 58, 638, 920, 34, { fontSize: 18, bold: true, color: C.white });
  addText(s, "20", 1162, 680, 64, 18, { fontSize: 9, bold: true, alignment: "right", color: C.white });
  s.speakerNotes.text = "My recommendation is to use GJR-HS as the primary daily model, EWMA-HS as the challenger and Historical Simulation as the transparent benchmark. Expected Shortfall, stress testing and risk contribution must remain beside VaR. If the 44 percent crisis loss or the concentration in Tesla and Amazon does not fit the risk appetite, management must reduce it, hedge it or explicitly accept it.";
  s.speakerNotes.setVisible(true);
}

// 21. Simulated performance
{
  const s = baseSlide("What the historical simulation produced from a $10M start", "SIMULATED PERFORMANCE", "Equal weighted and rebalanced monthly from June 2012 through October 2026");
  const simulatedEnd = 10_000_000 * (1 + R.portfolio["total return"]);
  const simulatedProfit = simulatedEnd - 10_000_000;
  const seriesScale = simulatedEnd / PERF.end;
  const growth = PERF.growth_dates
    .map((date, i) => ({ date, value: PERF.growth_millions[i] * seriesScale }))
    .filter((_, i, rows) => i % 12 === 0 || i === rows.length - 1);
  const contributions = PERF.contribution_millions.map((value) => value * seriesScale);
  const drawdown = PERF.drawdown_dates
    .map((date, i) => ({ date, value: PERF.drawdown_pct[i] }))
    .filter((_, i, rows) => i % 3 === 0 || i === rows.length - 1);

  const stats = [
    [money(simulatedEnd, 1), "ending value", C.teal],
    [money(simulatedProfit, 1), "cumulative profit", C.teal],
    [pct(R.portfolio["annual return"]), "annualized return", C.ink],
    [pct(R.portfolio["annual volatility"]), "annualized volatility", C.ink],
    [pct(R.portfolio["max drawdown"]), "maximum drawdown", C.red],
  ];
  stats.forEach((x, i) => metric(s, x[0], x[1], 54 + i * 232, 176, 204, x[2]));

  addText(s, "Portfolio value from a $10M starting investment", 54, 264, 520, 24, { fontSize: 14, bold: true });
  s.charts.add("line", {
    position: { left: 54, top: 294, width: 560, height: 236 },
    categories: growth.map((x) => x.date.slice(0, 4)),
    series: [{ name: "Portfolio value ($M)", values: growth.map((x) => Number(x.value.toFixed(1))), line: { fill: C.teal, width: 3 } }],
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { fill: C.dark, fontSize: 10 } },
    xAxis: { textStyle: { fill: C.mid, fontSize: 9 }, majorGridlines: null },
    yAxis: { numberFormatCode: "$0", textStyle: { fill: C.mid, fontSize: 9 }, majorGridlines: { style: "solid", fill: C.pale, width: 1 }, min: 0 },
    chartFill: C.white, plotAreaFill: C.white,
    chartLine: { style: "solid", fill: C.white, width: 0 }, plotAreaLine: { style: "solid", fill: C.white, width: 0 },
  });

  addText(s, "Contribution to simulated profit by holding", 648, 264, 520, 24, { fontSize: 14, bold: true });
  s.charts.add("bar", {
    position: { left: 648, top: 294, width: 560, height: 236 },
    categories: PERF.contribution_names,
    series: [{ name: "Contribution ($M)", values: contributions.map((x) => Number(x.toFixed(1))), fill: C.teal }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 42 },
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { fill: C.dark, fontSize: 10 } },
    xAxis: { textStyle: { fill: C.dark, fontSize: 9 }, majorGridlines: null },
    yAxis: { numberFormatCode: "$0", textStyle: { fill: C.mid, fontSize: 9 }, majorGridlines: { style: "solid", fill: C.pale, width: 1 }, min: 0 },
    chartFill: C.white, plotAreaFill: C.white,
    chartLine: { style: "solid", fill: C.white, width: 0 }, plotAreaLine: { style: "solid", fill: C.white, width: 0 },
  });

  addText(s, "Drawdown from the previous portfolio peak", 54, 542, 520, 22, { fontSize: 13, bold: true });
  s.charts.add("line", {
    position: { left: 54, top: 568, width: 850, height: 88 },
    categories: drawdown.map((x) => x.date),
    series: [{ name: "Drawdown (%)", values: drawdown.map((x) => Number(x.value.toFixed(1))), line: { fill: C.red, width: 2 } }],
    hasLegend: true,
    legend: { position: "right", overlay: false, textStyle: { fill: C.dark, fontSize: 9 } },
    xAxis: { textStyle: { fill: C.mid, fontSize: 7 }, majorGridlines: null },
    yAxis: { numberFormatCode: "0.0", textStyle: { fill: C.mid, fontSize: 8 }, majorGridlines: { style: "solid", fill: C.pale, width: 1 }, max: 0 },
    chartFill: C.white, plotAreaFill: C.white,
    chartLine: { style: "solid", fill: C.white, width: 0 }, plotAreaLine: { style: "solid", fill: C.white, width: 0 },
  });
  callout(s, `Worst period: 19 Feb to 23 Mar 2020  |  ${pct(R.portfolio["max drawdown"])}  |  recovered by 5 Jun 2020`, 934, 568, 274, 48, C.softRed, C.red);
  addText(s, "Nvidia was the largest contributor, followed by Tesla and Alphabet. Monthly rebalancing repeatedly redistributed gains back toward the target weights.", 934, 622, 274, 38, { fontSize: 10, color: C.dark });
  addText(s, "Historical simulation before transaction costs and taxes. It is not a forecast of future performance.", 54, 682, 1030, 18, { fontSize: 8, color: C.mid });
  addText(s, "21", 1162, 680, 64, 18, { fontSize: 9, bold: true, alignment: "right" });
  s.speakerNotes.text = `A hypothetical ten-million-dollar investment at the beginning of the sample grows to about ${money(simulatedEnd, 1)}, creating about ${money(simulatedProfit, 1)} of cumulative simulated profit. Nvidia contributes the most, followed by Tesla and Alphabet. The worst drawdown occurred during the COVID shock, when the portfolio fell ${pct(R.portfolio["max drawdown"])} from its previous peak. These figures are historical, before transaction costs and taxes, and do not forecast future performance.`;
  s.speakerNotes.setVisible(true);
}

await fs.mkdir(BUILD, { recursive: true });
await fs.mkdir(path.dirname(OUTPUT), { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(BUILD, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
}
const montage = await presentation.export({ format: "webp", montage: true });
await fs.writeFile(path.join(BUILD, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));
const candidatePath = path.join(BUILD, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

await finalizePresentation({
  explicitTotalSlideCount: 21,
  workspaceDir: ROOT,
  candidatePath,
  finalPath: OUTPUT,
  pythonExecutable: path.join(RUNTIME_ROOT, "python", "python.exe"),
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit"],
  requiredNativeChartOwnerSlides: [],
  materializeLiteralChartWorkbooks: true,
  requiredNativeTableOwnerSlides: [],
  fontPolicy: { basis: "design", families: [FONT, "Arial"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(BUILD, "validation-v4.json"),
});

console.log(OUTPUT);
