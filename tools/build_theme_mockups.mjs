import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/malek/Desktop/HomeBase/Job/QFI/QFI Deliverables/V2";
const skillDir = "C:/Users/malek/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11618/skills/presentations";
const runtimePython = "C:/Users/malek/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const buildDir = path.join(workspaceDir, ".mockups-build");
const outputDir = path.join(workspaceDir, "presentation_mockups");
const finalPath = path.join(outputDir, "QFI_PowerPoint_Theme_Mockups.pptx");
const fontFamily = "Aptos";

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function box(slide, left, top, width, height, fill, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "rect",
    position: { left, top, width, height },
    fill,
    line: {
      style: "solid",
      fill: options.lineFill ?? fill,
      width: options.lineWidth ?? 0,
    },
    ...(options.borderRadius ? { borderRadius: options.borderRadius } : {}),
  });
}

function textBox(slide, text, left, top, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontFamily,
    fontSize: options.fontSize ?? 24,
    bold: options.bold ?? false,
    color: options.color ?? "#111827",
    ...(options.italic ? { italic: true } : {}),
    ...(options.align ? { alignment: options.align } : {}),
  };
  return shape;
}

function themeTag(slide, number, name, color, dark = false) {
  textBox(slide, String(number).padStart(2, "0"), 54, 36, 42, 24, {
    fontSize: 12,
    bold: true,
    color,
  });
  textBox(slide, name.toUpperCase(), 102, 36, 360, 24, {
    fontSize: 12,
    bold: true,
    color: dark ? "#CBD5E1" : "#475569",
  });
}

function addLineChart(slide, position, colors, dark = false, legend = true) {
  const chart = slide.charts.add("line", {
    position,
    categories: ["2019", "2020", "2021", "2022", "2023", "2024"],
    series: [
      { name: "Portfolio", values: [100, 92, 126, 119, 151, 184], fill: colors[0] },
      { name: "Benchmark", values: [100, 95, 117, 109, 128, 149], fill: colors[1] },
    ],
    hasLegend: legend,
    legend: legend ? { position: "bottom" } : undefined,
    xAxis: { labelColor: dark ? "#CBD5E1" : "#64748B" },
    yAxis: {
      labelColor: dark ? "#CBD5E1" : "#64748B",
      majorGridlines: { style: "solid", fill: dark ? "#334155" : "#E2E8F0", width: 1 },
    },
  });
  return chart;
}

function addBarChart(slide, position, colors, dark = false) {
  return slide.charts.add("bar", {
    position,
    categories: ["HS", "EWMA", "GARCH", "GJR"],
    series: [{ name: "1-day VaR", values: [3.37, 2.36, 2.65, 2.82], fill: colors[0] }],
    hasLegend: true,
    legend: { position: "bottom" },
    dataLabels: { showValue: true, position: "outEnd" },
    xAxis: {
      labelColor: dark ? "#CBD5E1" : "#64748B",
      majorGridlines: { style: "solid", fill: dark ? "#334155" : "#E2E8F0", width: 1 },
    },
    yAxis: { labelColor: dark ? "#CBD5E1" : "#64748B" },
  });
}

function metric(slide, value, label, left, top, color, muted) {
  textBox(slide, value, left, top, 210, 58, { fontSize: 38, bold: true, color });
  textBox(slide, label, left, top + 56, 210, 34, { fontSize: 14, color: muted });
}

// 1. Institutional navy
{
  const slide = presentation.slides.add();
  slide.background.fill = "#F7F9FC";
  box(slide, 0, 0, 1280, 14, "#0B2A4A");
  themeTag(slide, 1, "Institutional navy", "#0B2A4A");
  textBox(slide, "Advanced Equity Portfolio\nRisk Management", 64, 120, 510, 158, {
    fontSize: 44,
    bold: true,
    color: "#0B2A4A",
  });
  textBox(slide, "Portfolio construction, volatility models, VaR backtesting and stress testing", 68, 308, 470, 78, {
    fontSize: 19,
    color: "#52657A",
  });
  box(slide, 620, 92, 580, 500, "#FFFFFF", { lineFill: "#D8E1EA", lineWidth: 1 });
  addLineChart(slide, { left: 660, top: 164, width: 500, height: 320 }, ["#0B6B75", "#8FA3B7"]);
  textBox(slide, "Portfolio growth", 660, 116, 220, 34, { fontSize: 19, bold: true, color: "#0B2A4A" });
  textBox(slide, "Quantitative Finance Project", 68, 630, 340, 28, { fontSize: 14, color: "#6B7C8F" });
}

// 2. Terminal dark
{
  const slide = presentation.slides.add();
  slide.background.fill = "#07110F";
  themeTag(slide, 2, "Terminal dark", "#4ADE80", true);
  textBox(slide, "Risk engine", 64, 112, 500, 72, { fontSize: 50, bold: true, color: "#F0FDF4" });
  textBox(slide, "Live portfolio diagnostics", 68, 184, 400, 38, { fontSize: 18, color: "#86EFAC" });
  box(slide, 64, 266, 1148, 1, "#24443A");
  metric(slide, "31.6%", "annual return", 68, 300, "#F0FDF4", "#7C9A8F");
  metric(slide, "21.9%", "annual volatility", 320, 300, "#F0FDF4", "#7C9A8F");
  metric(slide, "1.28", "Sharpe ratio", 572, 300, "#4ADE80", "#7C9A8F");
  metric(slide, "−34.9%", "maximum drawdown", 824, 300, "#FB7185", "#7C9A8F");
  addLineChart(slide, { left: 68, top: 440, width: 1060, height: 214 }, ["#4ADE80", "#64748B"], true, true);
}

// 3. Editorial ivory
{
  const slide = presentation.slides.add();
  slide.background.fill = "#F4F0E8";
  themeTag(slide, 3, "Editorial ivory", "#9A3412");
  textBox(slide, "How much can the portfolio lose\non a difficult trading day?", 64, 106, 760, 150, {
    fontSize: 43,
    bold: true,
    color: "#1F2933",
  });
  box(slide, 64, 286, 1128, 2, "#1F2933");
  textBox(slide, "The models place one-day loss at risk between 2.36% and 3.37% at the selected confidence level.", 64, 320, 540, 104, {
    fontSize: 22,
    color: "#3F4A54",
  });
  textBox(slide, "3.37%", 714, 306, 300, 100, { fontSize: 66, bold: true, color: "#9A3412" });
  textBox(slide, "Historical Simulation VaR", 720, 404, 300, 34, { fontSize: 16, color: "#6B6258" });
  textBox(slide, "A restrained report style for an academic panel or investment committee.", 64, 606, 760, 36, {
    fontSize: 15,
    italic: true,
    color: "#6B6258",
  });
}

// 4. Risk signal red
{
  const slide = presentation.slides.add();
  slide.background.fill = "#FFF8F6";
  box(slide, 0, 0, 1280, 720, "#9F1239");
  box(slide, 420, 0, 860, 720, "#FFF8F6");
  themeTag(slide, 4, "Risk signal red", "#FECDD3", true);
  textBox(slide, "STRESS\nTESTING", 62, 156, 300, 122, { fontSize: 48, bold: true, color: "#FFFFFF" });
  textBox(slide, "Historical crises replayed on today’s portfolio", 64, 312, 280, 84, {
    fontSize: 18,
    color: "#FFE4E6",
  });
  textBox(slide, "Worst scenario", 478, 86, 240, 32, { fontSize: 17, color: "#7F1D1D" });
  textBox(slide, "$4.40M", 476, 122, 320, 86, { fontSize: 56, bold: true, color: "#9F1239" });
  textBox(slide, "2008 financial crisis", 482, 210, 320, 34, { fontSize: 17, color: "#6B2937" });
  const labels = ["2008 crisis", "COVID crash", "Inflation 2022", "Tech selloff"];
  const widths = [590, 462, 342, 280];
  labels.forEach((label, i) => {
    textBox(slide, label, 478, 304 + i * 70, 170, 24, { fontSize: 14, color: "#5F2833" });
    box(slide, 650, 302 + i * 70, widths[i], 28, i === 0 ? "#9F1239" : "#FDA4AF");
  });
}

// 5. Teal analytics
{
  const slide = presentation.slides.add();
  slide.background.fill = "#ECFEFF";
  themeTag(slide, 5, "Teal analytics", "#0F766E");
  textBox(slide, "VaR model comparison", 64, 94, 540, 60, { fontSize: 38, bold: true, color: "#134E4A" });
  textBox(slide, "One-day loss threshold by model", 66, 156, 400, 32, { fontSize: 17, color: "#477774" });
  box(slide, 64, 218, 768, 414, "#FFFFFF", { lineFill: "#99E6DF", lineWidth: 1 });
  addBarChart(slide, { left: 100, top: 260, width: 694, height: 318 }, ["#0F766E"], false);
  box(slide, 874, 218, 338, 414, "#134E4A");
  textBox(slide, "Model readout", 910, 260, 250, 34, { fontSize: 20, bold: true, color: "#CCFBF1" });
  textBox(slide, "EWMA produces the lowest current VaR\n\nGJR retains the equity leverage effect\n\nExpected Shortfall remains above VaR", 910, 330, 240, 200, {
    fontSize: 17,
    color: "#E6FFFB",
  });
}

// 6. Technical blueprint
{
  const slide = presentation.slides.add();
  slide.background.fill = "#0B3A67";
  themeTag(slide, 6, "Technical blueprint", "#7DD3FC", true);
  textBox(slide, "MODEL ARCHITECTURE", 64, 90, 560, 48, { fontSize: 30, bold: true, color: "#E0F2FE" });
  textBox(slide, "A transparent path from market data to a validated risk decision", 66, 144, 680, 32, {
    fontSize: 17,
    color: "#BAE6FD",
  });
  const steps = ["Market data", "Clean returns", "Volatility", "VaR models", "Backtesting", "Stress loss"];
  steps.forEach((step, i) => {
    const left = 66 + (i % 3) * 390;
    const top = 246 + Math.floor(i / 3) * 180;
    box(slide, left, top, 320, 116, "#0F4C81", { lineFill: "#7DD3FC", lineWidth: 1 });
    textBox(slide, String(i + 1).padStart(2, "0"), left + 20, top + 18, 40, 28, {
      fontSize: 13,
      bold: true,
      color: "#7DD3FC",
    });
    textBox(slide, step, left + 20, top + 56, 260, 34, { fontSize: 20, bold: true, color: "#F0F9FF" });
  });
}

// 7. Charcoal and lime
{
  const slide = presentation.slides.add();
  slide.background.fill = "#171717";
  box(slide, 0, 0, 24, 720, "#BEF264");
  themeTag(slide, 7, "Charcoal and lime", "#BEF264", true);
  textBox(slide, "Backtesting\nthat exposes failure", 68, 102, 540, 130, {
    fontSize: 46,
    bold: true,
    color: "#FAFAFA",
  });
  textBox(slide, "Actual loss against forecast VaR", 72, 246, 420, 34, { fontSize: 18, color: "#A3A3A3" });
  box(slide, 638, 82, 520, 520, "#262626", { lineFill: "#404040", lineWidth: 1 });
  addLineChart(slide, { left: 680, top: 144, width: 438, height: 350 }, ["#BEF264", "#F87171"], true, true);
  textBox(slide, "PASS", 72, 402, 220, 72, { fontSize: 54, bold: true, color: "#BEF264" });
  textBox(slide, "Kupiec coverage test", 76, 480, 260, 32, { fontSize: 16, color: "#D4D4D4" });
}

// 8. Quantitative purple
{
  const slide = presentation.slides.add();
  slide.background.fill = "#2E1065";
  box(slide, 0, 0, 1280, 720, "#2E1065");
  box(slide, 0, 510, 1280, 210, "#4C1D95");
  themeTag(slide, 8, "Quantitative purple", "#D8B4FE", true);
  textBox(slide, "Volatility changes the meaning of history", 64, 98, 860, 110, {
    fontSize: 44,
    bold: true,
    color: "#FAF5FF",
  });
  textBox(slide, "EWMA, GARCH and GJR-GARCH rescale past returns to the current market regime.", 66, 224, 720, 64, {
    fontSize: 20,
    color: "#E9D5FF",
  });
  addLineChart(slide, { left: 64, top: 330, width: 1148, height: 292 }, ["#C084FC", "#67E8F9"], true, true);
}

// 9. Swiss monochrome
{
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  themeTag(slide, 9, "Swiss monochrome", "#111111");
  textBox(slide, "PORTFOLIO RISK", 64, 90, 940, 90, { fontSize: 62, bold: true, color: "#111111" });
  box(slide, 64, 194, 1148, 8, "#111111");
  textBox(slide, "31.6", 64, 260, 260, 100, { fontSize: 74, bold: true, color: "#111111" });
  textBox(slide, "% ANNUAL RETURN", 68, 360, 260, 28, { fontSize: 14, bold: true, color: "#111111" });
  textBox(slide, "21.9", 390, 260, 260, 100, { fontSize: 74, bold: true, color: "#111111" });
  textBox(slide, "% ANNUAL VOLATILITY", 394, 360, 260, 28, { fontSize: 14, bold: true, color: "#111111" });
  textBox(slide, "1.28", 730, 260, 260, 100, { fontSize: 74, bold: true, color: "#111111" });
  textBox(slide, "SHARPE RATIO", 734, 360, 260, 28, { fontSize: 14, bold: true, color: "#111111" });
  box(slide, 64, 470, 1148, 1, "#111111");
  textBox(slide, "A typographic direction for a concise academic defense.", 64, 514, 700, 44, {
    fontSize: 20,
    color: "#333333",
  });
}

// 10. Executive sky
{
  const slide = presentation.slides.add();
  slide.background.fill = "#F8FAFC";
  box(slide, 0, 0, 1280, 186, "#DCEEFF");
  themeTag(slide, 10, "Executive sky", "#075985");
  textBox(slide, "Risk conclusions", 64, 92, 540, 64, { fontSize: 40, bold: true, color: "#0C4A6E" });
  textBox(slide, "What the analysis supports today", 66, 154, 400, 30, { fontSize: 17, color: "#3F6F8A" });
  const rows = [
    ["Current risk", "GJR-HS 1-day VaR", "2.82%"],
    ["Tail severity", "GJR-HS Expected Shortfall", "3.22%"],
    ["Historical stress", "2008 crisis replay", "43.98%"],
    ["Portfolio quality", "Annualized Sharpe ratio", "1.28"],
  ];
  rows.forEach((row, i) => {
    const top = 244 + i * 88;
    box(slide, 64, top + 70, 1148, 1, "#D8E3EC");
    textBox(slide, row[0], 70, top, 210, 34, { fontSize: 15, bold: true, color: "#527083" });
    textBox(slide, row[1], 330, top, 520, 34, { fontSize: 20, color: "#16384D" });
    textBox(slide, row[2], 972, top - 4, 220, 44, { fontSize: 28, bold: true, color: "#0369A1", align: "right" });
  });
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await writeBlob(path.join(buildDir, `slide-${String(index + 1).padStart(2, "0")}.png`), png);
}
const montage = await presentation.export({ format: "webp", montage: true });
await writeBlob(path.join(buildDir, "theme-mockups-montage.webp"), montage);

const { finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href
);
const candidatePath = path.join(buildDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

await finalizePresentation({
  explicitTotalSlideCount: 10,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [1, 2, 5, 7, 8],
  materializeLiteralChartWorkbooks: true,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit"],
  fontPolicy: { basis: "design", families: [fontFamily] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "theme-mockups.validation.json"),
});

console.log(finalPath);
