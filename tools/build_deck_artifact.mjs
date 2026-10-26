// Compatibility wrapper for users who previously invoked the Node entry point.
// The maintained presentation builder is the portable Python module.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const virtualEnvPython = path.join(
  root,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const candidates = [
  process.env.PYTHON,
  existsSync(virtualEnvPython) ? virtualEnvPython : null,
  process.platform === "win32" ? "python" : "python3",
].filter(Boolean);

for (const executable of candidates) {
  const result = spawnSync(executable, ["-m", "tools.build_deck"], {
    cwd: root,
    stdio: "inherit",
  });
  if (result.status === 0) process.exit(0);
  if (!result.error || result.error.code !== "ENOENT") process.exit(result.status ?? 1);
}

console.error("Python 3.10 or newer is required to build the presentation.");
process.exit(1);

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const USER = process.env.USERPROFILE || process.env.HOME;
const RUNTIME_ROOT = path.join(USER, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies");
const ARTIFACT_MODULE = path.join(
  RUNTIME_ROOT,
  "node",
  "node_modules",
  "@oai",
  "artifact-tool",
  "dist",
  "artifact_tool.mjs",
);
const PRESENTATION_SKILL = path.join(
  USER,
  ".codex",
  "plugins",
  "cache",
  "openai-primary-runtime",
  "presentations",
  "26.1015.12040",
  "skills",
  "presentations",
);
const RUNTIME_PYTHON = path.join(RUNTIME_ROOT, "python", "python.exe");
process.env.RUNTIME_NODE_MODULES = path.join(RUNTIME_ROOT, "node", "node_modules");
process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES = process.env.RUNTIME_NODE_MODULES;

const { FileBlob, Presentation, PresentationFile, fr } = await import(
  pathToFileURL(ARTIFACT_MODULE).href
);
const { finalizePresentation } = await import(
  pathToFileURL(path.join(PRESENTATION_SKILL, "container_tools", "artifact_tool_utils.mjs")).href
);

const R = JSON.parse(await fs.readFile(path.join(ROOT, "report_assets", "results.json"), "utf8"));
const BUILD_DIR = path.join(ROOT, "extra", "deck_build");
const PREVIEW_DIR = path.join(BUILD_DIR, "previews");
const STAGING_DIR = path.join(BUILD_DIR, "staging");
const RECEIPT_DIR = path.join(ROOT, "extra", "deck_receipts");
const ROOT_OUTPUT = path.join(ROOT, "QFI_V2_slides.pptx");
const runId = new Date().toISOString().replace(/[:.]/g, "-");
const FINAL_PPTX = path.join(BUILD_DIR, `QFI_V2_slides-${runId}.pptx`);

await fs.mkdir(PREVIEW_DIR, { recursive: true });
await fs.mkdir(STAGING_DIR, { recursive: true });
await fs.mkdir(RECEIPT_DIR, { recursive: true });

const C = {
  paper: "#F6F1E8",
  white: "#FFFEFB",
  ink: "#1B2928",
  muted: "#5E6865",
  green: "#174C4F",
  green2: "#2E6A68",
  mint: "#DDE9E4",
  gold: "#C9973A",
  goldLight: "#F1E2BE",
  coral: "#B84A3A",
  coralLight: "#F3DCD7",
  blue: "#477F8F",
  line: "#D7D0C1",
};

const sourceLine =
  "Source: QFI_V2_report.docx; Advanced Equity Portfolio Risk Management brief; report_assets/results.json, as of 16 October 2026.";

function addText(slide, text, position, style = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    typeface: "Arial",
    fontSize: 20,
    color: C.ink,
    ...style,
  };
  return box;
}

function addRect(slide, position, fill, line = "none", radius = null) {
  const shape = slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position,
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
    ...(radius ? { borderRadius: radius } : {}),
  });
  return shape;
}

function addLine(slide, left, top, width, color = C.line, thickness = 2) {
  return addRect(slide, { left, top, width, height: thickness }, color);
}

function baseSlide(title, subtitle = "") {
  const slide = presentation.slides.add();
  slide.background.fill = C.paper;
  addText(slide, title, { left: 64, top: 42, width: 1050, height: 48 }, {
    fontSize: 34,
    bold: true,
    color: C.ink,
  });
  addRect(slide, { left: 64, top: 103, width: 72, height: 5 }, C.gold);
  if (subtitle) {
    addText(slide, subtitle, { left: 154, top: 91, width: 990, height: 32 }, {
      fontSize: 16,
      color: C.muted,
    });
  }
  return slide;
}

function finishSlide(slide, number, note = "") {
  addLine(slide, 64, 668, 1152, C.line, 1);
  addText(slide, sourceLine, { left: 64, top: 675, width: 1040, height: 22 }, {
    fontSize: 9,
    color: C.muted,
  });
  addText(slide, String(number).padStart(2, "0"), { left: 1138, top: 672, width: 74, height: 24 }, {
    fontSize: 11,
    bold: true,
    color: C.green,
    alignment: "right",
  });
  slide.speakerNotes.text = `${note}\n\n${sourceLine}`.trim();
  slide.speakerNotes.setVisible(true);
}

function addBullet(slide, text, top, left = 74, width = 500, color = C.ink, size = 20) {
  addText(slide, "•", { left, top: top - 1, width: 24, height: 28 }, { fontSize: size + 2, bold: true, color: C.gold });
  return addText(slide, text, { left: left + 28, top, width, height: 54 }, { fontSize: size, color });
}

function addMetric(slide, value, label, left, top, width, accent = C.green) {
  addText(slide, value, { left, top, width, height: 56 }, { fontSize: 36, bold: true, color: accent });
  addText(slide, label, { left, top: top + 55, width, height: 42 }, { fontSize: 16, color: C.muted });
}

function addCallout(slide, title, body, left, top, width, fill = C.mint, accent = C.green) {
  addRect(slide, { left, top, width, height: 116 }, fill, "none", "rounded-lg");
  addRect(slide, { left, top, width: 7, height: 116 }, accent);
  addText(slide, title, { left: left + 24, top: top + 18, width: width - 42, height: 30 }, {
    fontSize: 20,
    bold: true,
    color: accent,
  });
  addText(slide, body, { left: left + 24, top: top + 52, width: width - 42, height: 50 }, {
    fontSize: 15,
    color: C.ink,
  });
}

function styleTable(table, rows, columns, headerColor = C.green) {
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: columns }).assign({
    fill: headerColor,
    textStyle: { typeface: "Arial", fontSize: 16, bold: true, color: C.white },
    margins: { left: 10, right: 10, top: 8, bottom: 8 },
  });
  if (rows > 1) {
    table.cells.block({ row: 1, column: 0, rowCount: rows - 1, columnCount: columns }).assign({
      fill: C.white,
      textStyle: { typeface: "Arial", fontSize: 15, color: C.ink },
      margins: { left: 10, right: 10, top: 8, bottom: 8 },
    });
  }
  table.styleOptions = { headerRow: true, bandedRows: true };
}

function addBarChart(slide, { left, top, width, height, categories, series, horizontal = false, numberFormat = "0.0", legend = true, min, max }) {
  return slide.charts.add("bar", {
    position: { left, top, width, height },
    categories,
    series: series.map((item) => ({
      ...item,
      values: item.values.map((value) => (value == null ? null : Number(Number(value).toFixed(4)))),
    })),
    barOptions: { direction: horizontal ? "bar" : "column", grouping: "clustered", gapWidth: horizontal ? 55 : 65 },
    hasLegend: legend,
    legend: { position: "bottom", overlay: false, textStyle: { fill: C.muted, fontSize: 13 } },
    xAxis: {
      textStyle: { fill: C.muted, fontSize: 12 },
      line: { style: "solid", fill: C.line, width: 1 },
      majorGridlines: null,
    },
    yAxis: {
      numberFormatCode: numberFormat,
      textStyle: { fill: C.muted, fontSize: 12 },
      line: { style: "solid", fill: C.line, width: 1 },
      majorGridlines: { style: "solid", fill: "#E7E1D6", width: 1 },
      ...(min !== undefined ? { min } : {}),
      ...(max !== undefined ? { max } : {}),
    },
    chartFill: "none",
    chartLine: { style: "solid", fill: "none", width: 0 },
    plotAreaFill: "none",
    plotAreaLine: { style: "solid", fill: "none", width: 0 },
  });
}

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
presentation.theme.defaultFont = "Arial";
presentation.theme.colorScheme = {
  name: "QFI Editorial",
  themeColors: {
    bg1: C.white,
    bg2: C.paper,
    tx1: C.ink,
    tx2: C.muted,
    dk1: C.ink,
    lt1: C.white,
    dk2: C.green,
    lt2: C.paper,
    accent1: C.green,
    accent2: C.gold,
    accent3: C.coral,
    accent4: C.blue,
    accent5: C.green2,
    accent6: "#8E7446",
    hlink: C.blue,
    folHlink: C.coral,
  },
};

// 1 — Cover
{
  const slide = presentation.slides.add();
  slide.background.fill = C.green;
  addRect(slide, { left: 0, top: 0, width: 28, height: 720 }, C.gold);
  addText(slide, "Advanced Equity\nPortfolio Risk Management", { left: 84, top: 132, width: 860, height: 164 }, {
    fontSize: 48,
    bold: true,
    color: C.white,
  });
  addText(slide, "VaR, Expected Shortfall, backtesting, stress testing and decisions", { left: 88, top: 325, width: 900, height: 48 }, {
    fontSize: 22,
    color: C.goldLight,
  });
  addLine(slide, 88, 401, 430, C.gold, 4);
  addText(slide, "Marwan Itani  ·  QFI  ·  October 2026", { left: 88, top: 438, width: 700, height: 36 }, {
    fontSize: 17,
    color: C.white,
  });
  addText(slide, "A reproducible risk system for a $10 million, 10-stock U.S. equity portfolio", { left: 88, top: 548, width: 830, height: 60 }, {
    fontSize: 18,
    color: "#DDE9E4",
  });
  addText(slide, "01", { left: 1138, top: 656, width: 74, height: 24 }, { fontSize: 11, bold: true, color: C.goldLight, alignment: "right" });
  slide.speakerNotes.text = `Open with the decision question: how much can the portfolio lose, when do the models fail, and what should a risk manager do?\n\n${sourceLine}`;
  slide.speakerNotes.setVisible(true);
}

// 2 — Scope and design
{
  const slide = baseSlide("Portfolio and research design", "One portfolio, four risk models, three validation layers");
  addMetric(slide, "$10m", "Current portfolio value", 74, 158, 220, C.green);
  addMetric(slide, "10", "Large U.S. equities", 324, 158, 200, C.green);
  addMetric(slide, "3,614", "Daily observations", 554, 158, 220, C.green);
  addMetric(slide, "2012–26", "Sample period", 804, 158, 220, C.green);
  addLine(slide, 74, 280, 1035, C.line, 2);
  const steps = [
    ["1", "Collect", "Adjusted closes, benchmark and risk-free series"],
    ["2", "Clean", "Align calendars, audit gaps and flag extremes"],
    ["3", "Model", "HS, EWMA-HS, GARCH-HS and GJR-HS"],
    ["4", "Challenge", "Backtests, stress tests and attribution"],
  ];
  steps.forEach(([n, title, body], i) => {
    const left = 74 + i * 277;
    addRect(slide, { left, top: 330, width: 44, height: 44 }, i === 3 ? C.gold : C.green, "none", "rounded-full");
    addText(slide, n, { left, top: 337, width: 44, height: 28 }, { fontSize: 18, bold: true, color: C.white, alignment: "center" });
    addText(slide, title, { left: left + 59, top: 328, width: 178, height: 32 }, { fontSize: 21, bold: true, color: C.ink });
    addText(slide, body, { left: left + 59, top: 365, width: 188, height: 92 }, { fontSize: 15, color: C.muted });
  });
  addCallout(slide, "Design principle", "Every risk estimate is paired with a validation or stress lens; no single model is treated as truth.", 74, 512, 1040, C.mint, C.green);
  finishSlide(slide, 2, "Explain the system as a sequence: collect, clean, model and challenge. The dashboard exposes the same sequence interactively.");
}

// 3 — Data and portfolio behavior
{
  const slide = baseSlide("Data quality and return behavior", "The portfolio is investable, but the return distribution is not Gaussian");
  const stocks = R.data.stocks;
  addBarChart(slide, {
    left: 62,
    top: 144,
    width: 760,
    height: 430,
    categories: stocks.map((d) => d.stock),
    series: [{ name: "Annualized volatility", values: stocks.map((d) => d.ann_vol * 100), fill: C.green }],
    numberFormat: "0.0\\%",
    legend: false,
    min: 0,
    max: 65,
  });
  addText(slide, "Annualized volatility (%)", { left: 76, top: 126, width: 260, height: 22 }, { fontSize: 12, bold: true, color: C.muted });
  addMetric(slide, "6 / 6", "Data checks passed", 858, 156, 270, C.green);
  addMetric(slide, "0", "Missing or stale values", 858, 274, 270, C.green);
  addMetric(slide, "−0.53", "Portfolio skewness", 858, 392, 270, C.coral);
  addMetric(slide, "12.0", "Excess kurtosis", 858, 510, 270, C.coral);
  finishSlide(slide, 3, "Volatility varies materially across holdings. Tesla is the most volatile; the portfolio is left-skewed and fat-tailed, so Gaussian loss assumptions are unsafe.");
}

// 4 — Volatility dynamics
{
  const slide = baseSlide("Volatility is clustered and asymmetric", "Large negative moves are followed by elevated risk");
  addBarChart(slide, {
    left: 62,
    top: 145,
    width: 760,
    height: 420,
    categories: R.leverage.map((d) => d.move),
    series: [{ name: "Average absolute move, next 5 days", values: R.leverage.map((d) => d["avg move next 5 days"] * 100), fill: C.coral }],
    numberFormat: "0.0\\%",
    legend: false,
    min: 0,
    max: 2.6,
  });
  addText(slide, "Average absolute move, next 5 days (%)", { left: 76, top: 126, width: 360, height: 22 }, { fontSize: 12, bold: true, color: C.muted });
  addCallout(slide, "GJR asymmetry", `γ = ${R.garch["GJR-GARCH"].gamma.toFixed(3)}. Negative shocks add materially more conditional variance than positive shocks.`, 850, 162, 344, C.coralLight, C.coral);
  addCallout(slide, "Persistent, not permanent", `Persistence = ${R.garch["GJR-GARCH"].persistence.toFixed(3)}; shock half-life ≈ ${R.garch["GJR-GARCH"]["half-life (days)"].toFixed(1)} trading days.`, 850, 310, 344, C.mint, C.green);
  addCallout(slide, "Model fit", `GJR AIC ${Math.round(R.garch["GJR-GARCH"].AIC).toLocaleString()} versus GARCH ${Math.round(R.garch.GARCH.AIC).toLocaleString()}; lower is better.`, 850, 458, 344, C.goldLight, "#7A5A1E");
  finishSlide(slide, 4, "The five-day response pattern and the positive GJR leverage coefficient support asymmetric volatility scaling.");
}

// 5 — Models
{
  const slide = baseSlide("Four risk models answer different questions", "All use historical residuals; only the volatility clock changes");
  const models = [
    ["HS", "What did losses look like in the last 500 days?", "No volatility scaling", C.muted],
    ["EWMA-HS", "What if recent shocks matter more?", "λ = 0.94 recursive variance", C.blue],
    ["GARCH-HS", "What if volatility mean-reverts?", "Symmetric conditional variance", C.green2],
    ["GJR-HS", "What if bad news raises risk more?", "Asymmetric conditional variance", C.coral],
  ];
  models.forEach(([name, question, method, color], i) => {
    const top = 146 + i * 116;
    addRect(slide, { left: 68, top, width: 132, height: 80 }, color, "none", "rounded-lg");
    addText(slide, name, { left: 72, top: top + 24, width: 124, height: 34 }, { fontSize: name.length > 6 ? 17 : 20, bold: true, color: C.white, alignment: "center" });
    addText(slide, question, { left: 216, top: top + 7, width: 590, height: 34 }, { fontSize: 22, bold: true, color: C.ink });
    addText(slide, method, { left: 216, top: top + 47, width: 590, height: 30 }, { fontSize: 16, color: C.muted });
    addLine(slide, 216, top + 91, 850, C.line, 1);
  });
  addCallout(slide, "Shared loss definition", "VaR is the loss threshold; Expected Shortfall is the average loss beyond that threshold. Both are reported in percent and dollars.", 842, 180, 352, C.goldLight, "#7A5A1E");
  addCallout(slide, "Scaling rule", "Filtered models standardize returns by conditional volatility, take a historical tail quantile, then rescale by today’s volatility.", 842, 338, 352, C.mint, C.green);
  finishSlide(slide, 5, "Set up the comparison: HS is transparent but slow-moving; the filtered models adapt to volatility; GJR also responds asymmetrically.");
}

// 6 — Current risk
{
  const slide = baseSlide("Current one-day VaR and Expected Shortfall", "At 99% confidence, model choice changes both the threshold and the tail mean");
  addBarChart(slide, {
    left: 58,
    top: 145,
    width: 810,
    height: 430,
    categories: R.var_today.map((d) => d.model),
    series: [
      { name: "VaR ($000s)", values: R.var_today.map((d) => d.var * R.value / 1000), fill: C.green },
      { name: "ES ($000s)", values: R.var_today.map((d) => d.es * R.value / 1000), fill: C.gold },
    ],
    numberFormat: "$0",
    legend: true,
    min: 0,
    max: 520,
  });
  const gjr = R.var_today.find((d) => d.model === "GJR-HS");
  addMetric(slide, `$${Math.round(gjr.var * R.value / 1000)}k`, "GJR-HS 99% VaR", 910, 190, 250, C.green);
  addMetric(slide, `$${Math.round(gjr.es * R.value / 1000)}k`, "GJR-HS 99% ES", 910, 320, 250, C.gold);
  addCallout(slide, "Interpretation", "On roughly 1 day in 100, losses may exceed the VaR threshold. ES estimates the average loss on those worse days.", 900, 474, 294, C.coralLight, C.coral);
  finishSlide(slide, 6, "The filtered models currently sit below unscaled HS because recent conditional volatility is below the full-window average. ES remains above VaR by construction.");
}

// 7 — Sensitivity table
{
  const slide = baseSlide("Confidence and window choice materially change VaR", "GJR-HS sensitivity, as a percent of portfolio value");
  const values = [
    ["Confidence", ...R.var_grid.cols],
    ...R.var_grid.rows.map((row, i) => [row, ...R.var_grid.values[i].map((v) => `${(v * 100).toFixed(2)}%`)]),
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: values[0].length,
    left: 92,
    top: 176,
    width: 770,
    height: 310,
    columnTracks: [fr(1.25), fr(1), fr(1), fr(1)],
    values,
  });
  styleTable(table, values.length, values[0].length);
  table.cells.block({ row: 2, column: 2, rowCount: 1, columnCount: 1 }).assign({
    fill: C.goldLight,
    textStyle: { typeface: "Arial", fontSize: 18, bold: true, color: "#6F4E12" },
  });
  addMetric(slide, "2.97%", "Base choice: 99%, 500 days", 912, 190, 270, C.gold);
  addMetric(slide, "1.34–3.34%", "Range across the grid", 912, 322, 270, C.coral);
  addCallout(slide, "Governance implication", "A limit should name the model, confidence level and estimation window—not just “VaR.”", 902, 470, 292, C.mint, C.green);
  finishSlide(slide, 7, "Sensitivity is large enough to change limit usage. The base estimate is highlighted; alternative windows and confidence levels should be monitored as model risk.");
}

// 8 — Backtesting design
{
  const slide = baseSlide("Backtesting asks three separate questions", "3,114 one-day-ahead forecasts; every forecast uses only information available at the time");
  const items = [
    ["1", "Exception rate", "Kupiec", "Is the number of breaches consistent with 1%?"],
    ["2", "Independence", "Christoffersen", "Do breaches arrive randomly rather than in clusters?"],
    ["3", "Joint coverage", "Conditional coverage", "Are both frequency and independence acceptable?"],
  ];
  items.forEach(([n, title, test, question], i) => {
    const left = 72 + i * 380;
    addRect(slide, { left, top: 176, width: 70, height: 70 }, i === 2 ? C.gold : C.green, "none", "rounded-full");
    addText(slide, n, { left, top: 191, width: 70, height: 36 }, { fontSize: 28, bold: true, color: C.white, alignment: "center" });
    addText(slide, title, { left, top: 276, width: 324, height: 34 }, { fontSize: 24, bold: true, color: C.ink });
    addText(slide, test, { left, top: 317, width: 324, height: 28 }, { fontSize: 17, bold: true, color: i === 2 ? "#7A5A1E" : C.green });
    addText(slide, question, { left, top: 360, width: 324, height: 76 }, { fontSize: 17, color: C.muted });
  });
  addLine(slide, 72, 474, 1080, C.line, 2);
  addMetric(slide, "31.1", "Expected exceptions at 99%", 86, 512, 250, C.green);
  addMetric(slide, "5%", "Decision threshold for p-values", 420, 512, 270, C.green);
  addMetric(slide, "Next day", "Forecast horizon prevents look-ahead", 774, 512, 330, C.green);
  finishSlide(slide, 8, "A model can get the count right yet still fail because breaches cluster. That distinction is central to the results on the next two slides.");
}

// 9 — Backtest exceptions
{
  const slide = baseSlide("Exception counts look acceptable; clustering is the problem", "99% one-day backtest across 3,114 forecasts");
  const bt = [...R.bt99].sort((a, b) => ["HS", "EWMA-HS", "GARCH-HS", "GJR-HS"].indexOf(a.model) - ["HS", "EWMA-HS", "GARCH-HS", "GJR-HS"].indexOf(b.model));
  addBarChart(slide, {
    left: 70,
    top: 160,
    width: 790,
    height: 390,
    categories: bt.map((d) => d.model),
    series: [
      { name: "Actual exceptions", values: bt.map((d) => d.exceptions), fill: C.coral },
      { name: "Expected", values: bt.map((d) => d.expected), fill: C.gold },
    ],
    numberFormat: "0",
    legend: true,
    min: 0,
    max: 42,
  });
  addCallout(slide, "All four", "Pass unconditional coverage: exception counts are close to the expected 31.1.", 902, 170, 292, C.mint, C.green);
  addCallout(slide, "Only GJR-HS", `Passes all three 99% tests; independence p = ${R.bt99.find((d) => d.model === "GJR-HS")["Christoffersen p"].toFixed(3)}.`, 902, 324, 292, C.goldLight, "#7A5A1E");
  addCallout(slide, "Plain HS", `Fails independence most strongly; p = ${R.bt99.find((d) => d.model === "HS")["Christoffersen p"].toFixed(4)}.`, 902, 478, 292, C.coralLight, C.coral);
  finishSlide(slide, 9, "Counts alone would make every model look acceptable. Independence tests reveal that HS, EWMA-HS and GARCH-HS still cluster breaches at the 5% level.");
}

// 10 — Model comparison table
{
  const slide = baseSlide("GJR-HS ranks first in the 99% backtest", "Coverage, independence and joint test p-values");
  const order = [...R.bt99].sort((a, b) => a.rank - b.rank);
  const values = [
    ["Model", "Actual / expected", "Kupiec p", "Independence p", "Joint p", "Pass all", "Rank"],
    ...order.map((d) => [
      d.model,
      `${d.exceptions} / ${d.expected.toFixed(1)}`,
      d["Kupiec p"].toFixed(3),
      d["Christoffersen p"].toFixed(3),
      d["Coverage p"].toFixed(3),
      d["passes all"] ? "Yes" : "No",
      String(d.rank),
    ]),
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: values[0].length,
    left: 66,
    top: 164,
    width: 1148,
    height: 330,
    columnTracks: [fr(1.25), fr(1.45), fr(1), fr(1.25), fr(1), fr(0.9), fr(0.65)],
    values,
  });
  styleTable(table, values.length, values[0].length);
  table.cells.block({ row: 1, column: 0, rowCount: 1, columnCount: values[0].length }).assign({
    fill: C.goldLight,
    textStyle: { typeface: "Arial", fontSize: 16, bold: true, color: C.ink },
  });
  addCallout(slide, "Decision", "Use GJR-HS as the primary monitoring model, keep EWMA-HS as a responsive challenger, and retain HS for transparent benchmarking.", 140, 530, 1000, C.mint, C.green);
  finishSlide(slide, 10, "Rank is based on the test suite, not on whichever model produces the smallest VaR. At 95%, GJR-HS and GARCH-HS both perform well, reinforcing the value of volatility filtering.");
}

// 11 — Stress testing
{
  const slide = baseSlide("Crisis losses overwhelm ordinary daily VaR", "Historical and hypothetical scenarios, ranked by portfolio loss");
  const stress = R.stress.filter((d) => d.loss > 0).slice(0, 8);
  addBarChart(slide, {
    left: 52,
    top: 145,
    width: 860,
    height: 465,
    categories: stress.map((d) => d.scenario),
    series: [{ name: "Portfolio loss", values: stress.map((d) => d.loss * 100), fill: C.coral }],
    horizontal: true,
    numberFormat: "0.0\\%",
    legend: false,
    min: 0,
    max: 50,
  });
  addText(slide, "Portfolio loss (%)", { left: 72, top: 126, width: 220, height: 22 }, { fontSize: 12, bold: true, color: C.muted });
  addMetric(slide, "44.1%", "2008 crisis loss", 944, 170, 230, C.coral);
  addMetric(slide, "34.6%", "COVID crash loss", 944, 298, 230, C.coral);
  addMetric(slide, "9.6%", "Basel-style stressed VaR", 944, 426, 230, C.gold);
  addText(slide, "Daily VaR is a control metric—not a crisis loss ceiling.", { left: 944, top: 552, width: 250, height: 62 }, { fontSize: 18, bold: true, color: C.ink });
  finishSlide(slide, 11, "The stress book answers a different question from daily VaR. The 2008 and COVID scenarios are an order of magnitude larger than current one-day VaR.");
}

// 12 — Attribution
{
  const slide = baseSlide("Risk is more concentrated than capital", "Current weights versus Expected Shortfall contribution");
  const attrib = [...R.attribution].sort((a, b) => b.es_share - a.es_share);
  addBarChart(slide, {
    left: 52,
    top: 145,
    width: 900,
    height: 455,
    categories: attrib.map((d) => d.stock),
    series: [
      { name: "Portfolio weight", values: attrib.map((d) => d.weight * 100), fill: C.green },
      { name: "ES contribution", values: attrib.map((d) => d.es_share * 100), fill: C.gold },
    ],
    numberFormat: "0.0\\%",
    legend: true,
    min: 0,
    max: 26,
  });
  addText(slide, "Share of portfolio (%)", { left: 72, top: 126, width: 240, height: 22 }, { fontSize: 12, bold: true, color: C.muted });
  addMetric(slide, "20%", "TSLA share of ES", 982, 178, 210, C.coral);
  addMetric(slide, "17%", "AMZN share of ES", 982, 310, 210, C.coral);
  addMetric(slide, "38%", "Diversification benefit", 982, 442, 210, C.green);
  finishSlide(slide, 12, "Equal capital weights do not imply equal risk. Tesla and Amazon together contribute about 37% of Expected Shortfall despite about 20% of capital.");
}

// 13 — Decisions
{
  const slide = baseSlide("The analytics translate into concrete actions", "Illustrative linear hedge estimates and an in-sample optimization");
  const hedges = R.hedges.slice(0, 3);
  addBarChart(slide, {
    left: 62,
    top: 150,
    width: 770,
    height: 430,
    categories: hedges.map((d) => d.instrument),
    series: [
      { name: "VaR before ($000s)", values: hedges.map((d) => d.var_before / 1000), fill: C.coral },
      { name: "VaR after ($000s)", values: hedges.map((d) => d.var_after / 1000), fill: C.green },
    ],
    numberFormat: "$0",
    legend: true,
    min: 0,
    max: 350,
  });
  addMetric(slide, "−59%", "VaR with beta-neutral SPY hedge", 870, 172, 330, C.green);
  addMetric(slide, "$330k → $229k", "ES in the optimized split", 870, 318, 330, C.gold);
  addCallout(slide, "Use with constraints", "Hedge ratios are linear estimates; optimization is in-sample and needs turnover, liquidity and forecast controls before trading.", 860, 470, 340, C.coralLight, C.coral);
  finishSlide(slide, 13, "The dashboard turns measurement into choices: reduce a concentration, add an index hedge, or re-optimize under explicit constraints. These are decision aids, not automatic trades.");
}

// 14 — Limitations
{
  const slide = baseSlide("What the framework does not solve", "Known limitations become explicit governance controls");
  const leftBullets = [
    "Survivorship and selection bias: today’s large stocks are evaluated historically.",
    "Square-root-of-time scaling does not capture path dependence over ten days.",
    "Backtest conclusions are sample-sensitive, especially at 99% confidence.",
  ];
  const rightBullets = [
    "Historical crises and hypothetical shocks remain scenario proxies, not forecasts.",
    "Market-cap rebalancing requires archived, point-in-time shares; current shares are never substituted.",
    "Production use should reconcile prices, corporate actions and exceptions against an independent vendor.",
  ];
  leftBullets.forEach((b, i) => addBullet(slide, b, 170 + i * 128, 78, 470, C.ink, 19));
  rightBullets.forEach((b, i) => addBullet(slide, b, 170 + i * 128, 660, 470, C.ink, 19));
  addLine(slide, 620, 150, 2, C.line, 450);
  addCallout(slide, "Control response", "Document configuration, retain challenger models, monitor breach clusters, and rerun stress tests whenever exposures change materially.", 188, 550, 904, C.mint, C.green);
  finishSlide(slide, 14, "The objective is not to eliminate model risk; it is to expose it, bound it, and preserve an audit trail for the decisions made.");
}

// 15 — Conclusion
{
  const slide = presentation.slides.add();
  slide.background.fill = C.ink;
  addText(slide, "Five conclusions", { left: 72, top: 48, width: 640, height: 54 }, { fontSize: 38, bold: true, color: C.white });
  addRect(slide, { left: 72, top: 119, width: 88, height: 5 }, C.gold);
  const conclusions = [
    "Volatility filtering improves risk timing.",
    "GJR-HS best balances coverage and breach independence.",
    "Expected Shortfall and stress tests reveal losses that VaR hides.",
    "Risk concentration is materially higher than capital concentration.",
    "The dashboard connects measurement, validation and action in one workflow.",
  ];
  conclusions.forEach((text, i) => {
    const top = 160 + i * 88;
    addText(slide, String(i + 1).padStart(2, "0"), { left: 78, top, width: 52, height: 32 }, { fontSize: 16, bold: true, color: C.gold });
    addText(slide, text, { left: 150, top: top - 5, width: 930, height: 48 }, { fontSize: 23, bold: i === 1, color: i === 1 ? C.goldLight : C.white });
    addLine(slide, 150, top + 52, 930, "#334443", 1);
  });
  addText(slide, "Primary recommendation", { left: 860, top: 58, width: 330, height: 30 }, { fontSize: 15, bold: true, color: C.gold, alignment: "right" });
  addText(slide, "Monitor with GJR-HS; challenge with EWMA-HS; govern with stress and attribution.", { left: 785, top: 105, width: 405, height: 92 }, { fontSize: 19, color: C.mint, alignment: "right" });
  addLine(slide, 72, 668, 1152, "#334443", 1);
  addText(slide, sourceLine, { left: 72, top: 675, width: 1040, height: 22 }, { fontSize: 9, color: "#A9B7B2" });
  addText(slide, "15", { left: 1138, top: 672, width: 74, height: 24 }, { fontSize: 11, bold: true, color: C.goldLight, alignment: "right" });
  slide.speakerNotes.text = `Close on the operating model: a primary risk model, a challenger, and stress/attribution as non-negotiable complements.\n\n${sourceLine}`;
  slide.speakerNotes.setVisible(true);
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

// Export draft previews before package validation.
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(PREVIEW_DIR, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
}

const candidatePath = path.join(STAGING_DIR, `candidate-${runId}.pptx`);
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const requirements = {
  explicitTotalSlideCount: 15,
  requiredNativeTableOwnerSlides: [7, 10],
  requiredNativeChartOwnerSlides: [3, 4, 6, 9, 11, 12, 13],
  requiredEmbeddedWorkbookChartOwnerSlides: [],
  materializeLiteralChartWorkbooks: true,
};

const validation = await finalizePresentation({
  ...requirements,
  workspaceDir: ROOT,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(PRESENTATION_SKILL, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(PRESENTATION_SKILL, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu",
    "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    "--require-native-table-slide",
    "7",
    "--require-native-table-slide",
    "10",
  ],
  fontPolicy: { basis: "design", families: ["Arial"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(RECEIPT_DIR, `QFI_V2_slides-${runId}.validation.json`),
});

await fs.copyFile(FINAL_PPTX, ROOT_OUTPUT);

// Re-import the finalized file and refresh the previews from the exact deliverable.
const checked = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
for (const [index, slide] of checked.slides.items.entries()) {
  const stem = `final-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(PREVIEW_DIR, `${stem}.png`), await checked.export({ slide, format: "png", scale: 1 }));
}

console.log(JSON.stringify({ output: ROOT_OUTPUT, final: FINAL_PPTX, slides: presentation.slides.items.length, validation }, null, 2));
