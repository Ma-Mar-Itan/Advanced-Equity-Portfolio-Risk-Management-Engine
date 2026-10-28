import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "file:///C:/Users/malek/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const workspaceDir = "C:/Users/malek/Desktop/HomeBase/Job/QFI/QFI Deliverables/V2";
const sourcePath = path.join(workspaceDir, "QFI_V2_slides_updated.pptx");
const buildDir = path.join(workspaceDir, ".swiss-build");
const outputDir = path.join(workspaceDir, "presentation_mockups");
const finalPath = path.join(outputDir, "QFI_V2_slides_swiss_monochrome_phases_final_v2.pptx");
const skillDir = "C:/Users/malek/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11618/skills/presentations";
const runtimePython = "C:/Users/malek/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";

const BLACK = "#111111";
const DARK_GRAY = "#3F3F46";
const MID_GRAY = "#71717A";
const LIGHT_GRAY = "#E4E4E7";
const PALE_GRAY = "#F4F4F5";
const WHITE = "#FFFFFF";
const RED = "#B91C1C";
const FONT = "Aptos";

const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));

function addBox(slide, left, top, width, height, fill, options = {}) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill,
    line: {
      style: "solid",
      fill: options.lineFill ?? fill,
      width: options.lineWidth ?? 0,
    },
  });
}

function addText(slide, text, left, top, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontFamily: FONT,
    fontSize: options.fontSize ?? 20,
    bold: options.bold ?? false,
    color: options.color ?? BLACK,
  };
  return shape;
}

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function wrapWords(value, maxLength) {
  const lines = [];
  let line = "";
  for (const word of String(value).split(/\s+/)) {
    const candidate = line ? `${line} ${word}` : word;
    if (candidate.length > maxLength && line) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function addFlattenedPhaseOverlay(slide, phaseNumber, title, summary, items, output) {
  const phase = String(phaseNumber).padStart(2, "0");
  const summaryLines = wrapWords(summary, 74);
  const outputLines = output.split("\n");
  const itemMarkup = items.map((item, index) => {
    const y = 392 + index * 54;
    return `<text x="74" y="${y}" font-size="12" font-weight="700" fill="${RED}">${String(index + 1).padStart(2, "0")}</text>
      <text x="134" y="${y + 7}" font-size="18" fill="${BLACK}">${escapeXml(item)}</text>
      <line x1="124" y1="${y + 30}" x2="784" y2="${y + 30}" stroke="${LIGHT_GRAY}" stroke-width="1"/>`;
  }).join("\n");
  const summaryMarkup = summaryLines.map((line, index) =>
    `<text x="74" y="${236 + index * 24}" font-size="20" fill="${DARK_GRAY}">${escapeXml(line)}</text>`,
  ).join("\n");
  const outputMarkup = outputLines.map((line, index) =>
    `<text x="860" y="${452 + index * 27}" font-size="22" font-weight="700" fill="${BLACK}">${escapeXml(line)}</text>`,
  ).join("\n");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
    <rect width="1280" height="720" fill="${WHITE}"/>
    <g font-family="Aptos, Arial, sans-serif">
      <text x="74" y="58" font-size="12" font-weight="700" fill="${RED}">PHASE ${phase}</text>
      <text x="74" y="140" font-size="38" font-weight="700" fill="${BLACK}">${escapeXml(title)}</text>
      <line x1="64" y1="181" x2="1212" y2="181" stroke="${BLACK}" stroke-width="6"/>
      ${summaryMarkup}
      <text x="978" y="296" font-size="84" font-weight="700" fill="${BLACK}">${phase}</text>
      <text x="74" y="352" font-size="12" font-weight="700" fill="${MID_GRAY}">IMPLEMENTATION</text>
      ${itemMarkup}
      <text x="860" y="398" font-size="12" font-weight="700" fill="${MID_GRAY}">OUTPUT</text>
      ${outputMarkup}
    </g>
  </svg>`;
  slide.images.add({
    svg,
    alt: `${title} phase summary`,
    fit: "cover",
    position: { left: 0, top: 0, width: 1280, height: 720 },
  });
}

function isNumericCallout(text) {
  return /^[−\-+]?\$?\d[\d.,%$KMBx×\s–—]*$/i.test(text.trim());
}

function restyleShape(shape, slideNumber) {
  const snapshot = shape.toSnapshot();
  const frame = snapshot.frame ?? { left: 0, top: 0, width: 0, height: 0 };
  const content = String(snapshot.text ?? "").trim();
  const hasText = content.length > 0;

  if (!hasText) {
    if (frame.width > 1100 && frame.height > 560) {
      shape.fill = WHITE;
      shape.line = { style: "solid", fill: WHITE, width: 0 };
    } else if (frame.height <= 6 || frame.width <= 8) {
      shape.fill = BLACK;
      shape.line = { style: "solid", fill: BLACK, width: 0 };
    } else if (shape.geometry === "ellipse") {
      shape.fill = slideNumber === 8 ? RED : BLACK;
      shape.line = { style: "solid", fill: WHITE, width: 1 };
    } else {
      shape.fill = WHITE;
      shape.line = { style: "solid", fill: LIGHT_GRAY, width: 1 };
      shape.shadow = "none";
    }
    return;
  }

  shape.text.typeface = FONT;
  shape.text.color = BLACK;
  shape.shadow = "none";

  if (frame.top < 84 && content.length > 3 && frame.width > 250) {
    shape.text.bold = true;
    shape.text.fontSize = slideNumber === 1 ? 44 : 28;
    shape.text.color = BLACK;
  } else if (frame.top < 126) {
    shape.text.color = DARK_GRAY;
  } else if (frame.top > 650) {
    shape.text.color = MID_GRAY;
    shape.text.fontSize = 9;
  }

  if (isNumericCallout(content)) {
    shape.text.bold = true;
    if (/^-|^−|44\.1|34\.6|19\.9|17\.4/.test(content)) {
      shape.text.color = RED;
    }
  }

  const compactLabel = frame.width < 125 && frame.height < 48 && content.length < 20;
  const riskLabel = /^(critical|fail|red|exception|loss)$/i.test(content);
  if (compactLabel) {
    shape.fill = riskLabel ? RED : BLACK;
    shape.line = { style: "solid", fill: riskLabel ? RED : BLACK, width: 0 };
    shape.text.color = WHITE;
    shape.text.bold = true;
  } else if (shape.geometry === "roundRect") {
    shape.fill = WHITE;
    shape.line = { style: "solid", fill: LIGHT_GRAY, width: 1 };
  } else {
    shape.fill = "none";
    shape.line = { style: "solid", fill: "none", width: 0 };
  }
}

function restyleChart(chart) {
  chart.chartFill = WHITE;
  chart.plotAreaFill = WHITE;
  chart.chartLine = { style: "solid", fill: WHITE, width: 0 };
  chart.hasLegend = true;
  chart.legend = { position: "bottom" };

  const palette = [BLACK, "#737373", RED, "#A3A3A3", "#D4D4D4"];
  for (const [index, series] of chart.series.items.entries()) {
    const color = palette[index % palette.length];
    series.fill = color;
    series.line = { style: "solid", fill: color, width: 2 };
    series.stroke = { style: "solid", fill: color, width: 2 };
    series.formula = "";
    series.categoryFormula = "";
    series.xFormula = "";
    series.bubbleSizeFormula = "";
  }
}

function restyleTable(table) {
  table.fill = WHITE;
  for (let row = 0; row < table.rowCount; row += 1) {
    for (let column = 0; column < table.columnCount; column += 1) {
      const cell = table.getCell(row, column);
      cell.fill = row === 0 ? BLACK : row % 2 === 0 ? PALE_GRAY : WHITE;
      cell.text.typeface = FONT;
      cell.text.color = row === 0 ? WHITE : BLACK;
      cell.text.bold = row === 0;
      cell.borders = {
        top: { style: "solid", fill: LIGHT_GRAY, width: 1 },
        bottom: { style: "solid", fill: LIGHT_GRAY, width: 1 },
        left: { style: "solid", fill: WHITE, width: 0 },
        right: { style: "solid", fill: WHITE, width: 0 },
      };
    }
  }
}

function rebuildCover(slide) {
  slide.shapes.deleteAll();
  slide.background.fill = WHITE;
  addText(slide, "QFI / PORTFOLIO RISK", 64, 42, 350, 28, { fontSize: 12, bold: true, color: RED });
  addText(slide, "Advanced Equity Portfolio\nRisk Management", 64, 132, 950, 154, {
    fontSize: 52,
    bold: true,
    color: BLACK,
  });
  addBox(slide, 64, 318, 1148, 8, BLACK);
  addText(slide, "Measurement, validation, stress testing and portfolio decisions", 64, 372, 820, 54, {
    fontSize: 22,
    color: DARK_GRAY,
  });
  addText(slide, "15 years of S&P 500 history\nFour VaR model families\n5,000 out-of-sample observations", 64, 500, 520, 104, {
    fontSize: 17,
    color: BLACK,
  });
  addText(slide, "Quantitative Finance Project", 64, 652, 340, 26, { fontSize: 12, color: MID_GRAY });
  addText(slide, "01", 1148, 652, 64, 26, { fontSize: 12, bold: true, color: BLACK });
}

function addPhaseSlide(phaseNumber, title, summary, items, output) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addText(slide, `PHASE ${String(phaseNumber).padStart(2, "0")}`, 64, 42, 240, 28, {
    fontSize: 12,
    bold: true,
    color: RED,
  });
  addText(slide, title, 64, 98, 860, 66, { fontSize: 38, bold: true, color: BLACK });
  addBox(slide, 64, 178, 1148, 6, BLACK);
  addText(slide, summary, 64, 218, 700, 72, { fontSize: 20, color: DARK_GRAY });
  addText(slide, String(phaseNumber).padStart(2, "0"), 968, 210, 240, 116, {
    fontSize: 84,
    bold: true,
    color: BLACK,
  });
  addText(slide, "IMPLEMENTATION", 64, 336, 260, 26, { fontSize: 12, bold: true, color: MID_GRAY });
  items.forEach((item, index) => {
    const top = 384 + index * 54;
    addText(slide, String(index + 1).padStart(2, "0"), 64, top, 44, 28, {
      fontSize: 12,
      bold: true,
      color: RED,
    });
    addText(slide, item, 124, top - 3, 660, 36, { fontSize: 18, color: BLACK });
    addBox(slide, 124, top + 38, 660, 1, LIGHT_GRAY);
  });
  addText(slide, "OUTPUT", 850, 382, 180, 26, { fontSize: 12, bold: true, color: MID_GRAY });
  addText(slide, output, 850, 428, 330, 150, { fontSize: 22, bold: true, color: BLACK });

  // Redraw small labels and the phase numeral on top. PowerPoint otherwise
  // occasionally places neighboring transparent text boxes above these items.
  addBox(slide, 60, 38, 250, 36, WHITE);
  addText(slide, `PHASE ${String(phaseNumber).padStart(2, "0")}`, 64, 42, 240, 28, {
    fontSize: 12,
    bold: true,
    color: RED,
  });
  addBox(slide, 950, 202, 260, 126, WHITE);
  addText(slide, String(phaseNumber).padStart(2, "0"), 968, 210, 240, 116, {
    fontSize: 84,
    bold: true,
    color: BLACK,
  });
  addBox(slide, 60, 330, 270, 38, WHITE);
  addText(slide, "IMPLEMENTATION", 64, 336, 260, 26, { fontSize: 12, bold: true, color: MID_GRAY });
  items.forEach((_, index) => {
    const top = 384 + index * 54;
    addBox(slide, 60, top - 2, 52, 34, WHITE);
    addText(slide, String(index + 1).padStart(2, "0"), 64, top, 44, 28, {
      fontSize: 12,
      bold: true,
      color: RED,
    });
  });
  addBox(slide, 846, 378, 190, 34, WHITE);
  addText(slide, "OUTPUT", 850, 382, 180, 26, { fontSize: 12, bold: true, color: MID_GRAY });
  if (phaseNumber === 10) {
    slide.shapes.deleteAll();
  }
  if (phaseNumber === 6 || phaseNumber === 10) {
    addFlattenedPhaseOverlay(slide, phaseNumber, title, summary, items, output);
  }
  return slide;
}

function addScopeSlide() {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addText(slide, "PROJECT SCOPE", 64, 42, 260, 28, { fontSize: 12, bold: true, color: RED });
  addText(slide, "Portfolio risk from raw prices to decisions", 64, 98, 960, 66, {
    fontSize: 38,
    bold: true,
    color: BLACK,
  });
  addBox(slide, 64, 178, 1148, 6, BLACK);
  addText(slide, "Ten phases form one auditable workflow. Each stage produces an output used by the next stage.", 64, 218, 920, 48, {
    fontSize: 20,
    color: DARK_GRAY,
  });
  const phases = [
    "Data collection",
    "Data cleaning",
    "Portfolio construction",
    "Historical Simulation VaR",
    "EWMA volatility scaling",
    "GARCH volatility scaling",
    "GJR-GARCH volatility scaling",
    "VaR backtesting",
    "Model comparison",
    "Stress testing",
  ];
  phases.forEach((phase, index) => {
    const column = index < 5 ? 0 : 1;
    const row = index % 5;
    const left = column === 0 ? 64 : 660;
    const top = 320 + row * 66;
    addText(slide, String(index + 1).padStart(2, "0"), left, top, 44, 26, {
      fontSize: 12,
      bold: true,
      color: RED,
    });
    addText(slide, phase, left + 60, top - 4, 470, 34, { fontSize: 19, bold: true, color: BLACK });
    addBox(slide, left + 60, top + 36, 470, 1, LIGHT_GRAY);
  });
  return slide;
}

for (const [index, slide] of presentation.slides.items.entries()) {
  const slideNumber = index + 1;
  if (slideNumber === 1) {
    rebuildCover(slide);
    continue;
  }

  slide.background.fill = WHITE;
  for (const shape of slide.shapes.items) restyleShape(shape, slideNumber);
  for (const shape of slide.shapes.items) {
    const snapshot = shape.toSnapshot();
    const content = String(snapshot.text ?? "").trim();
    if (content && snapshot.frame?.top >= 84 && snapshot.frame?.top <= 104 && snapshot.frame?.height <= 40) {
      shape.text = content;
      shape.text.style = { fontFamily: FONT, fontSize: 15, color: DARK_GRAY };
      shape.position = { left: 164, top: 82, width: 980, height: 30 };
    }
  }
  for (const chart of slide.charts.items) restyleChart(chart);
  for (const table of slide.tables.items) restyleTable(table);

  addBox(slide, 64, 112, 1148, 3, BLACK);
}

const originalSlideIds = presentation.slides.items.map((slide) => slide.id);
const insertedSlides = [
  addScopeSlide(),
  addPhaseSlide(
    1,
    "Data Collection",
    "Build a repeatable, cache-first market-data layer for the portfolio, benchmark and risk inputs.",
    ["Collect adjusted daily prices", "Load benchmark and risk-free series", "Cache each provider response", "Record source and date coverage"],
    "Price history\nBenchmark prices\nRisk-free rate\nReference data",
  ),
  addPhaseSlide(
    2,
    "Data Cleaning",
    "Convert raw vendor histories into aligned matrices that the portfolio and risk engines can trust.",
    ["Adjust splits and dividends", "Align trading dates", "Handle missing and stale prices", "Winsorize data errors when required"],
    "Clean price matrix\nClean log-return matrix\nRolling volatility inputs",
  ),
  addPhaseSlide(
    3,
    "Portfolio Construction",
    "Translate tickers, weights, value and rebalancing rules into daily portfolio economics.",
    ["Validate weights and exposures", "Support equal and custom weights", "Apply the rebalancing schedule", "Calculate value, return and P&L"],
    "Daily portfolio value\nDaily return series\nDaily P&L\nPortfolio weights",
  ),
  addPhaseSlide(
    4,
    "Historical Simulation VaR",
    "Measure downside risk directly from the empirical loss distribution without imposing normality.",
    ["Use 250, 500 or 750 observations", "Apply 95%, 99% or 99.5% confidence", "Estimate VaR and Expected Shortfall", "Produce rolling risk histories"],
    "P&L distribution\nHistorical VaR\nExpected Shortfall\nRolling VaR",
  ),
  addPhaseSlide(
    5,
    "EWMA Volatility Scaling",
    "Give recent shocks more weight and restate historical returns at today’s volatility level.",
    ["Set daily lambda to 0.94", "Estimate EWMA variance and volatility", "Scale historical returns", "Recalculate Historical VaR"],
    "EWMA volatility\nScaled returns\nEWMA-scaled VaR\nException comparison",
  ),
  addPhaseSlide(
    6,
    "GARCH Volatility Scaling",
    "Model volatility clustering and forecast the next trading day before scaling the historical distribution.",
    ["Fit GARCH(1,1)", "Estimate conditional volatility", "Forecast one-day volatility", "Scale returns and calculate VaR"],
    "Conditional volatility\nForecast volatility\nStandardized residuals\nGARCH-scaled VaR",
  ),
  addPhaseSlide(
    7,
    "GJR-GARCH Volatility Scaling",
    "Capture the stronger volatility response that often follows negative equity returns.",
    ["Fit the asymmetric variance model", "Estimate the leverage parameter", "Forecast next-day volatility", "Calculate GJR-scaled VaR"],
    "Leverage effect\nConditional volatility\nForecast volatility\nGJR-GARCH VaR",
  ),
  addPhaseSlide(
    8,
    "VaR Backtesting",
    "Test whether realized losses breach the forecast at the expected rate and whether exceptions cluster.",
    ["Run a rolling out-of-sample test", "Count and timestamp exceptions", "Apply Kupiec and Christoffersen tests", "Assign the Basel traffic-light zone"],
    "Exception count\nCoverage p-values\nIndependence result\nPass or fail conclusion",
  ),
  addPhaseSlide(
    9,
    "Model Comparison",
    "Compare the four VaR approaches on accuracy, stability, tail severity and backtesting performance.",
    ["Compare exceptions and average VaR", "Measure VaR volatility", "Compare Expected Shortfall", "Rank models using test evidence"],
    "Comparison table\nException overlays\nBacktest summary\nModel ranking",
  ),
  addPhaseSlide(
    10,
    "Stress Testing",
    "Replay historical crises and apply hypothetical market, volatility, correlation and sector shocks.",
    ["Replay named historical crises", "Apply market fall scenarios", "Shock volatility and correlation", "Rank losses and stressed risk"],
    "Stressed loss\nStressed VaR and ES\nWorst-case loss\nScenario ranking",
  ),
];

presentation.slides.reorder([
  `sl/${originalSlideIds[0]}`,
  ...insertedSlides.map((slide) => `sl/${slide.id}`),
  ...originalSlideIds.slice(1).map((id) => `sl/${id}`),
]);

for (const [index, slide] of presentation.slides.items.entries()) {
  const displayNumber = index + 1;
  if (displayNumber > 1) {
    addText(slide, String(displayNumber).padStart(2, "0"), 1148, 42, 64, 22, {
      fontSize: 10,
      bold: true,
      color: displayNumber === 26 ? RED : BLACK,
    });
  }
  for (const shape of slide.shapes.items) {
    const snapshot = shape.toSnapshot();
    const content = String(snapshot.text ?? "").trim();
    if (snapshot.frame?.top > 630 && snapshot.frame?.width < 100 && /^\d{1,2}$/.test(content)) {
      shape.text = String(displayNumber).padStart(2, "0");
      shape.text.style = { fontFamily: FONT, fontSize: 9, bold: true, color: WHITE };
    }
  }
}

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(
    path.join(buildDir, `slide-${String(index + 1).padStart(2, "0")}.png`),
    new Uint8Array(await png.arrayBuffer()),
  );
}
const montage = await presentation.export({ format: "webp", montage: true });
await fs.writeFile(path.join(buildDir, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const candidatePath = path.join(buildDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const { finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);
await finalizePresentation({
  explicitTotalSlideCount: 26,
  sourceTemplatePath: sourcePath,
  requiredNativeChartOwnerSlides: [15, 17, 19, 20, 22, 23, 24],
  nativeChartTargetApplication: "powerpoint",
  requiredNativeTableOwnerSlides: [18, 21, 25],
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu",
    "12192000,6858000",
    "--validate-heading-fit",
    "--require-native-table-slide",
    "18",
    "--require-native-table-slide",
    "21",
    "--require-native-table-slide",
    "25",
  ],
  fontPolicy: { basis: "design", families: [FONT, "Arial"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "validation-phases-final-v2.json"),
});

console.log(finalPath);
