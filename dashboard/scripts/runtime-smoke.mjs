import {spawnSync} from "node:child_process";
import {existsSync} from "node:fs";
import {readFile, stat} from "node:fs/promises";
import {createServer} from "node:http";
import {extname, join, resolve, sep} from "node:path";

import {chromium} from "playwright-core";

const dist = resolve(process.argv[2] ?? "dist");
const timeoutMs = 12_000;
const routes = [
  "/",
  "/conditions",
  "/forecast-revisions",
  "/pipeline-monitoring",
  "/data-provenance"
];
const publicLandingUrl = "https://epmelito.github.io/SaltBytes/";

function contentType(path) {
  return {
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8"
  }[extname(path)] ?? "application/octet-stream";
}

function requestPath(pathname) {
  let relative = decodeURIComponent(pathname).replace(/^\/+/, "");
  if (!relative) relative = "index.html";
  if (!extname(relative)) relative += ".html";
  const file = resolve(dist, relative);
  if (file !== dist && !file.startsWith(`${dist}${sep}`)) throw new Error("invalid path");
  return file;
}

async function startServer() {
  const server = createServer(async (request, response) => {
    try {
      const file = requestPath(new URL(request.url, "http://localhost").pathname);
      await stat(file);
      response.writeHead(200, {"content-type": contentType(file)});
      response.end(await readFile(file));
    } catch {
      response.writeHead(404, {"content-type": "text/plain; charset=utf-8"});
      response.end("not found");
    }
  });
  await new Promise((resolveListen) => server.listen(0, "127.0.0.1", resolveListen));
  return {server, port: server.address().port};
}

function findCommand(command) {
  const lookup = process.platform === "win32" ? "where.exe" : "which";
  const result = spawnSync(lookup, [command], {encoding: "utf8"});
  return result.status === 0 ? result.stdout.trim().split(/\r?\n/)[0] : null;
}

function browserPath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const commands = process.platform === "win32"
    ? ["chrome.exe", "msedge.exe"]
    : ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"];
  for (const command of commands) {
    const found = findCommand(command);
    if (found) return found;
  }
  if (process.platform === "win32") {
    const candidates = [
      join(process.env.PROGRAMFILES ?? "", "Google", "Chrome", "Application", "chrome.exe"),
      join(process.env["PROGRAMFILES(X86)"] ?? "", "Google", "Chrome", "Application", "chrome.exe"),
      join(process.env.LOCALAPPDATA ?? "", "Google", "Chrome", "Application", "chrome.exe"),
      join(process.env.PROGRAMFILES ?? "", "Microsoft", "Edge", "Application", "msedge.exe"),
      join(process.env["PROGRAMFILES(X86)"] ?? "", "Microsoft", "Edge", "Application", "msedge.exe")
    ];
    for (const candidate of candidates) if (existsSync(candidate)) return candidate;
  }
  throw new Error("Chrome or Chromium was not found; set CHROME_PATH");
}

async function openPage(page, url, errors) {
  errors.length = 0;
  await page.goto(url, {waitUntil: "networkidle"});
  const text = await page.locator("body").innerText();
  if (/RuntimeError:|Failed to resolve module specifier|TypeError:/.test(text)) {
    throw new Error(`runtime error rendered at ${url}`);
  }
  if (errors.length) throw new Error(`${url}: ${errors.join(" | ")}`);
}

async function assertHealthy(page, errors, label) {
  const text = await page.locator("body").innerText();
  if (/RuntimeError:|Failed to resolve module specifier/.test(text)) {
    throw new Error(`${label}: rendered runtime error`);
  }
  if (errors.length) throw new Error(`${label}: ${errors.join(" | ")}`);
}

async function selectOption(page, index, optionIndex, label) {
  const select = page.locator("select").nth(index);
  if (optionIndex < 0 || await select.locator("option").count() <= optionIndex) {
    throw new Error(`${label} is not populated`);
  }
  await select.selectOption({index: optionIndex});
}

async function assertScrollableTables(page, label) {
  try {
    await page.waitForFunction(() => {
      const tables = [...document.querySelectorAll("table")];
      return tables.length > 0 && tables.every((table) => {
        const container = table.closest(".table-scroll");
        const cell = table.querySelector("th, td");
        return container
          && getComputedStyle(container).overflowX === "auto"
          && (!cell || getComputedStyle(cell).whiteSpace === "nowrap");
      });
    });
  } catch {
    throw new Error(`${label}: tables are not protected by horizontal scrolling`);
  }
}

async function assertShell(page, section, route) {
  await page.waitForFunction(
    ({sectionName, routeName, landingUrl}) => {
      const activeSection = document.querySelector("#observablehq-sidebar section.observablehq-section-active > summary");
      const activeRoute = document.querySelector("#observablehq-sidebar .observablehq-link-active > a");
      const home = document.querySelector(".shell-home");
      return activeSection?.textContent.trim() === sectionName
        && activeRoute?.textContent.trim() === routeName
        && home?.href === landingUrl;
    },
    {sectionName: section, routeName: route, landingUrl: publicLandingUrl}
  );
  const colors = await page.locator(".shell-home").evaluate((element) => ({
    home: getComputedStyle(element).color,
    header: getComputedStyle(element.parentElement).color,
    page: getComputedStyle(document.body).backgroundColor
  }));
  if (colors.home === colors.page || colors.header === colors.page) {
    throw new Error("dashboard shell text is not visible against the page background");
  }
  await page.locator("body").focus();
  for (let index = 0; index < 20; index += 1) {
    await page.keyboard.press("Tab");
    if (await page.locator(".shell-home").evaluate((element) => document.activeElement === element)) {
      const outlineStyle = await page.locator(".shell-home").evaluate(
        (element) => getComputedStyle(element).outlineStyle
      );
      if (outlineStyle === "none") throw new Error("SaltBytes landing link has no visible keyboard focus");
      return;
    }
  }
  throw new Error("SaltBytes landing link is not reachable by keyboard");
}

async function assertConditionsHierarchy(page, available) {
  await page.waitForFunction((scoreAvailable) => {
    const headings = [...document.querySelectorAll("#observablehq-main h2")]
      .map((heading) => heading.textContent.trim());
    const assessment = document.querySelector(".conditions-assessment");
    const current = document.querySelector(".conditions-current");
    const details = assessment?.querySelector("details");
    return headings.indexOf("Spanish mackerel assessment") < headings.indexOf("Current coastal conditions")
      && headings.indexOf("Current coastal conditions") < headings.indexOf("Upcoming changes")
      && headings.indexOf("Upcoming changes") < headings.indexOf("Supporting evidence and limitations")
      && assessment
      && current
      && (scoreAvailable
        ? assessment.querySelector(".assessment-score")?.textContent.match(/[0-9]+ \/ 100/)
          && assessment.textContent.includes("support the assessment, while waves limit it.")
          && assessment.textContent.includes("Overall confidence")
          && assessment.textContent.includes("What SaltBytes cannot observe")
          && assessment.textContent.includes("does not estimate fish presence, catch likelihood, or safety")
          && details?.querySelector("summary")?.textContent.includes("Assessment factors and confidence")
          && !assessment.textContent.includes("spanish-mackerel-v1.0.0")
          && !assessment.textContent.includes("Recent fish observations")
          && !current.textContent.includes("Success")
          && !current.textContent.includes("Exact forecast values")
          && current.textContent.includes("From the E (110°)")
          && current.querySelector(".conditions-tide summary")?.textContent.includes("Tide details")
          && current.querySelectorAll("article").length === 5
        : assessment.classList.contains("conditions-assessment-unavailable")
          && assessment.textContent.includes("Assessment unavailable")
          && !assessment.querySelector(".assessment-highlights")
          && current.textContent.includes("Water temperature")
          && current.textContent.includes("Unavailable"));
  }, available);

  if (available) {
    const disclosure = page.locator(".conditions-assessment details");
    await disclosure.locator("summary").focus();
    const focusStyle = await disclosure.locator("summary").evaluate(
      (element) => getComputedStyle(element).outlineStyle
    );
    if (focusStyle === "none") throw new Error("assessment disclosure has no visible keyboard focus");
    await disclosure.locator("summary").press("Enter");
    await page.waitForFunction(() => document.querySelector(".conditions-assessment details")?.open);
    const confidenceText = await page.locator(".confidence-values").innerText();
    if (!confidenceText.toLowerCase().includes("seasonal evidence") || !confidenceText.toLowerCase().includes("forecast data")) {
      throw new Error("assessment disclosure does not retain complete deeper evidence");
    }
    const layout = await page.evaluate(() => {
      const values = document.querySelector(".confidence-values");
      const controls = [...document.querySelectorAll("select")];
      const sourceDetails = [...document.querySelectorAll("#observablehq-main > details")]
        .find((details) => details.querySelector("summary")?.textContent.includes("Sources and forecast limitations"));
      if (!values || controls.length !== 2 || !sourceDetails) return {ready: false};
      const grid = getComputedStyle(values);
      const firstControl = controls[0].getBoundingClientRect();
      const secondControl = controls[1].getBoundingClientRect();
      return {
        ready: values.children.length === 6
        && grid.gridAutoFlow === "column"
        && grid.gridTemplateColumns.split(" ").length === 2
        && Math.abs(firstControl.top - secondControl.top) < 2
        && controls.every((control) => {
          const label = control.previousElementSibling;
          const form = control.closest("form");
          return label?.matches("label") && form && getComputedStyle(form).display === "grid"
            && control.getBoundingClientRect().top > label.getBoundingClientRect().top;
        })
      };
    });
    if (!layout.ready) throw new Error("Conditions layout did not render as required");
    const tideDetails = page.locator(".conditions-tide details");
    if ((await page.locator(".conditions-tide").innerText()).includes("Previous ")) {
      throw new Error("tide events are visible before Tide details opens");
    }
    await tideDetails.locator("summary").press("Enter");
    await page.waitForFunction(() => document.querySelector(".conditions-tide details")?.open);
    const tideText = await tideDetails.innerText();
    if (!tideText.includes("Previous low") || !tideText.includes("Next high")) {
      throw new Error("Tide details does not show separate predicted events");
    }
    const sourceDetails = page.locator("#observablehq-main > details").filter({
      hasText: "Sources and forecast limitations"
    });
    await sourceDetails.locator("summary").press("Enter");
    const sourceText = await sourceDetails.innerText();
    if (
      !sourceText.includes("regional marine forecast grid")
      || sourceText.includes("Previous low")
      || sourceText.includes("Next high")
    ) {
      throw new Error("Sources and forecast limitations does not contain the intended concise explanations");
    }
  }
}

async function assertConditionsVisualizations(page, available) {
  await page.waitForFunction(() => document.querySelector(".shore-direction")
    && document.querySelectorAll(".trend-track svg").length === 3);
  const readiness = await page.evaluate(() => {
    const trendStory = document.querySelector(".forecast-context");
    const tide = document.querySelector(".tide-timing, .visual-unavailable");
    const direction = document.querySelector(".shore-direction");
    const selectedRules = document.querySelectorAll(".selected-time-rule");
    return {
      trendStory: Boolean(trendStory),
      trendTracks: document.querySelectorAll(".forecast-surface").length === 3,
      selectedRules: selectedRules.length,
      tide: Boolean(tide),
      direction: Boolean(direction),
      oldChartGrid: Boolean(document.querySelector(".chart-grid"))
    };
  });
  if (
    !readiness.trendStory
    || !readiness.trendTracks
    || readiness.selectedRules !== 3
    || !readiness.tide
    || !readiness.direction
    || readiness.oldChartGrid
  ) {
    throw new Error(`Conditions visualization hierarchy is incomplete: ${JSON.stringify(readiness)}`);
  }

  const visualState = await page.evaluate((scoreAvailable) => {
    const tide = document.querySelector(".tide-timing");
    const direction = document.querySelector(".shore-direction");
    const forecastTrends = document.querySelector(".forecast-context");
    const selectedMarkers = [...document.querySelectorAll(".forecast-surface .selected-time-rule")];
    const directionPanels = [...document.querySelectorAll(".direction-panel")];
    const visualGrid = document.querySelector(".conditions-visual-grid");
    const plotLayouts = [...document.querySelectorAll(".trend-track")].map((track) => {
      const trackBox = track.getBoundingClientRect();
      const svgBox = track.querySelector("svg")?.getBoundingClientRect();
      return {
        trackWidth: trackBox.width,
        svgWidth: svgBox?.width,
        svgHeight: svgBox?.height
      };
    });
    const pageWidth = document.documentElement.scrollWidth;
    const viewportWidth = document.documentElement.clientWidth;
    return {
      exactTideEndpoints: tide?.textContent.includes("Previous low: 0.2 m")
        && tide?.textContent.includes("Next high: 1.1 m"),
      selectedTideText: [...(tide?.querySelectorAll("text") ?? [])]
        .find((text) => text.textContent.includes("Selected time"))?.textContent ?? "",
      tideLimitation: tide?.textContent.includes("The line shows timing between tide predictions, not an exact water level."),
      directionText: direction?.textContent ?? "",
      trendValues: [...document.querySelectorAll(".forecast-surface title")].map((title) => title.textContent),
      selectedMarkers: selectedMarkers.map((marker) => marker.getBoundingClientRect().left),
      selectedTime: forecastTrends?.textContent ?? "",
      waterUnavailable: document.querySelector(".visual-data-unavailable")?.textContent ?? "",
      noOverflow: pageWidth <= viewportWidth,
      limitedPreview: forecastTrends?.textContent.includes("Only 4 forecast hours are available in this preview.") ?? false,
      localTicks: [...document.querySelectorAll(".forecast-temperature .trend-track svg text")].map((text) => text.textContent),
      gridMaxWidth: Number.parseFloat(getComputedStyle(visualGrid).maxWidth),
      plotLayouts,
      tideBox: tide?.querySelector("svg")?.getBoundingClientRect(),
      tideMarker: tide?.querySelector(".tide-selected")?.getBoundingClientRect().left,
      arrows: directionPanels.map((panel) => {
        const arrow = panel.querySelector(".direction-arrow");
        const svg = panel.querySelector("svg");
        const box = arrow?.getBoundingClientRect();
        const svgBox = svg?.getBoundingClientRect();
        return {left: box?.left, top: box?.top, length: Math.hypot(box?.width ?? 0, box?.height ?? 0), inside: box && svgBox && box.left >= svgBox.left && box.right <= svgBox.right && box.top >= svgBox.top && box.bottom <= svgBox.bottom};
      }),
      scoreAvailable
    };
  }, available);
  if (
    !visualState.tideLimitation
    || !visualState.noOverflow
    || visualState.selectedMarkers.some((marker) => !Number.isFinite(marker))
    || !visualState.selectedTime.includes("Selected time:")
    || !visualState.limitedPreview
    || !Number.isFinite(visualState.gridMaxWidth)
    || visualState.gridMaxWidth > 1152.5
    || visualState.plotLayouts.length !== 3
    || visualState.plotLayouts.some((layout) => !Number.isFinite(layout.svgWidth)
      || Math.abs(layout.trackWidth - layout.svgWidth) > 2
      || layout.svgHeight < 200
      || layout.svgHeight > 300)
    || visualState.tideBox.width > 1024
    || visualState.tideBox.height > 300
    || visualState.arrows.length !== 2
    || visualState.arrows.some((arrow) => arrow.length < 20 || !arrow.inside)
  ) {
    throw new Error(`Conditions visualization hierarchy did not render correctly: ${JSON.stringify(visualState)}`);
  }
  if (available) {
    if (
      !visualState.exactTideEndpoints
      || !/^Selected time · (rising|falling)$/.test(visualState.selectedTideText)
      || !visualState.directionText.includes("Open water")
      || !visualState.directionText.includes("Shoreline")
      || !visualState.directionText.includes("Land")
      || !visualState.directionText.includes("Wind")
      || !visualState.directionText.includes("Waves")
      || !/(Onshore component|Offshore component|Alongshore)/.test(visualState.directionText)
      || visualState.directionText.includes("degrees from seaward shore normal")
      || visualState.localTicks.some((tick) => /(?:EDT|EST|UTC)/.test(tick))
      || !visualState.localTicks.some((tick) => /^\d{1,2} (?:AM|PM)$/.test(tick))
    ) {
      throw new Error("Conditions tide or direction visual did not retain the required user-facing meaning");
    }
  } else if (!visualState.waterUnavailable.includes("Water temperature is unavailable at the selected time")) {
    throw new Error("Conditions unavailable forecast state is not explicit");
  }
  return visualState;
}

async function run() {
  const {server, port} = await startServer();
  const browser = await chromium.launch({
    executablePath: browserPath(),
    headless: true,
    args: ["--no-sandbox"]
  });
  const page = await browser.newPage({viewport: {width: 1440, height: 900}});
  page.setDefaultTimeout(timeoutMs);
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const base = `http://127.0.0.1:${port}`;

  try {
    await openPage(page, `${base}/`, errors);
    await page.waitForURL(`${base}/conditions`);
    await assertShell(page, "Coastal conditions", "Conditions");

    await page.waitForFunction(() => document.querySelectorAll("select").length === 2);
    const initialConditions = await page.locator(".conditions-context").innerText();
    if (!initialConditions || initialConditions.includes("Unavailable")) {
      throw new Error("Conditions did not initialize with data");
    }
    await assertConditionsHierarchy(page, true);
    const initialVisuals = await assertConditionsVisualizations(page, true);
    await selectOption(page, 0, 1, "Conditions location control");
    await page.waitForFunction(
      (before) => document.querySelector(".conditions-context")?.innerText !== before,
      initialConditions
    );
    const locationConditions = await page.locator(".conditions-context").innerText();
    await page.waitForFunction(() => document.querySelectorAll("select")[1]?.options.length > 1);
    const locationVisuals = await assertConditionsVisualizations(page, true);
    if (
      locationVisuals.directionText === initialVisuals.directionText
      && locationVisuals.trendValues.join("\n") === initialVisuals.trendValues.join("\n")
    ) {
      throw new Error("Conditions location control did not update the visual context");
    }
    const forecastOptions = await page.locator("select").nth(1).locator("option").count();
    await selectOption(page, 1, forecastOptions - 1, "Conditions forecast control");
    await page.waitForFunction(
      (before) => document.querySelector(".conditions-context")?.innerText !== before,
      locationConditions
    );
    await assertConditionsHierarchy(page, false);
    const updatedVisuals = await assertConditionsVisualizations(page, false);
    if (
      updatedVisuals.selectedTime === locationVisuals.selectedTime
      || updatedVisuals.selectedMarkers.some((marker, index) => marker === locationVisuals.selectedMarkers[index])
      || updatedVisuals.tideMarker === locationVisuals.tideMarker
      || updatedVisuals.arrows.every((arrow, index) => arrow.left === locationVisuals.arrows[index]?.left && arrow.top === locationVisuals.arrows[index]?.top)
    ) {
      throw new Error("Conditions forecast control did not update every selected-time marker");
    }
    await assertHealthy(page, errors, "Conditions");

    await openPage(page, `${base}/forecast-revisions`, errors);
    await assertShell(page, "Operations and product health", "Forecast revisions");
    await page.waitForFunction(() => document.querySelectorAll("select").length === 3);
    const detailValues = page.locator(".detail-card .detail-value");
    const revisionTime = await detailValues.nth(1).innerText();
    await page.waitForFunction(() => document.querySelectorAll("select")[1]?.options.length > 1);
    const validOptions = await page.locator("select").nth(1).locator("option").count();
    await selectOption(page, 1, validOptions - 1, "Forecast revisions valid time control");
    await page.waitForFunction(
      (before) => document.querySelectorAll(".detail-card .detail-value")[1]?.innerText !== before,
      revisionTime
    );
    const revisionLocation = await detailValues.nth(0).innerText();
    await selectOption(page, 0, 1, "Forecast revisions location control");
    await page.waitForFunction(
      (before) => document.querySelector(".detail-card .detail-value")?.innerText !== before,
      revisionLocation
    );
    const tableHeader = await page.locator("table thead").innerText();
    await selectOption(page, 2, 1, "Forecast revisions metric control");
    await page.waitForFunction(
      (before) => document.querySelector("table thead")?.innerText !== before,
      tableHeader
    );
    await assertScrollableTables(page, "Forecast revisions");
    await assertHealthy(page, errors, "Forecast revisions");

    await openPage(page, `${base}/pipeline-monitoring`, errors);
    await assertShell(page, "Operations and product health", "Pipeline monitoring");
    await page.waitForFunction(() => document.querySelectorAll("select").length === 1);
    await page.evaluate(() => {
      window.__saltbytesMutations = 0;
      new MutationObserver((items) => window.__saltbytesMutations += items.length)
        .observe(document.body, {childList: true, subtree: true, characterData: true});
    });
    await selectOption(page, 0, 1, "Pipeline coverage control");
    await page.waitForFunction(() => window.__saltbytesMutations > 0);
    await assertScrollableTables(page, "Pipeline monitoring");
    await assertHealthy(page, errors, "Pipeline monitoring");

    await openPage(page, `${base}/data-provenance`, errors);
    await assertShell(page, "Operations and product health", "Data provenance");
    await page.waitForFunction(() => document.querySelectorAll("select").length === 2);
    const metricValues = page.locator(".metric-card .metric-value");
    await page.waitForFunction(() =>
      document.body.innerText.includes("Tide relationship metadata is available")
    );
    const initialProvenance = await page.locator("body").textContent();
    if (
      initialProvenance.includes("${isTide ? html`")
      || initialProvenance.includes("Prediction location")
    ) {
      throw new Error("Data provenance tide content did not initialize correctly");
    }
    const sourceValue = await metricValues.nth(1).innerText();
    const sourceControl = page.locator("select").nth(1);
    const sourceLabels = await sourceControl.locator("option").allTextContents();
    const tideIndex = sourceLabels.findIndex((label) => label.trim() === "Tide");
    if (tideIndex < 0) {
      throw new Error("Data provenance Tide source option is not populated");
    }
    await sourceControl.selectOption({index: tideIndex});
    await page.waitForFunction(
      (before) => document.querySelectorAll(".metric-card .metric-value")[1]?.innerText !== before,
      sourceValue
    );
    await page.waitForFunction(() => {
      const text = document.body.textContent;
      return text.includes("Prediction location")
        && !text.includes("Tide relationship metadata is available");
    });
    const provenanceLocation = await metricValues.nth(0).innerText();
    await selectOption(page, 0, 1, "Data provenance location control");
    await page.waitForFunction(
      (before) => document.querySelector(".metric-card .metric-value")?.innerText !== before,
      provenanceLocation
    );
    await assertHealthy(page, errors, "Data provenance");

    await page.emulateMedia({colorScheme: "dark"});
    await openPage(page, `${base}/conditions`, errors);
    await assertShell(page, "Coastal conditions", "Conditions");
    await openPage(page, `${base}/pipeline-monitoring`, errors);
    await assertShell(page, "Operations and product health", "Pipeline monitoring");
    await assertHealthy(page, errors, "Dark dashboard shell");
    await page.emulateMedia({colorScheme: "light"});

    for (const route of routes) {
      await openPage(page, `${base}${route}`, errors);
      await page.reload({waitUntil: "networkidle"});
      await assertHealthy(page, errors, `route refresh ${route}`);
    }

    console.log("dashboard_runtime_smoke=passed");
  } finally {
    await browser.close();
    await new Promise((resolveClose) => server.close(resolveClose));
  }
}

run().catch((error) => {
  console.error(error.stack ?? error.message);
  process.exitCode = 1;
});
