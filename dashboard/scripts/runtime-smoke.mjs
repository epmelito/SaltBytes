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
  "/species-assessments",
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

async function selectRevisionMetric(page, field, label) {
  const option = page.locator(`[data-revision-measurement="${field}"]`);
  if (await option.count() !== 1) throw new Error(`${label} is not populated`);
  await option.click();
  await page.waitForFunction(
    (selectedField) => document.querySelector(`[data-revision-measurement="${selectedField}"]`)
      ?.getAttribute("aria-pressed") === "true",
    field
  );
}

async function assertKeyboardFocus(page, locator, label) {
  await page.locator("body").focus();
  for (let index = 0; index < 50; index += 1) {
    await page.keyboard.press("Tab");
    if (await locator.evaluate((element) => document.activeElement === element)) {
      const outlineStyle = await locator.evaluate(
        (element) => getComputedStyle(element).outlineStyle
      );
      if (outlineStyle === "none") throw new Error(`${label} has no visible keyboard focus`);
      return;
    }
  }
  throw new Error(`${label} is not reachable by keyboard`);
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
      const themeControl = document.querySelector("[data-saltbytes-theme-control]");
      return activeSection?.textContent.trim() === sectionName
        && activeRoute?.textContent.trim() === routeName
        && home?.href === landingUrl
        && themeControl
        && themeControl.querySelector('[data-saltbytes-theme-choice][aria-pressed="true"]');
    },
    {sectionName: section, routeName: route, landingUrl: publicLandingUrl}
  );
  const colors = await page.locator(".shell-home").evaluate((element) => ({
    home: getComputedStyle(element).color,
    header: getComputedStyle(element.closest(".shell-header")).color,
    page: getComputedStyle(document.body).backgroundColor
  }));
  if (colors.home === colors.page || colors.header === colors.page) {
    throw new Error("dashboard shell text is not visible against the page background");
  }
  const shellLayout = await page.evaluate(() => {
    const main = document.querySelector("#observablehq-main");
    const themeControl = document.querySelector("[data-saltbytes-theme-control]");
    const sidebarHome = document.querySelector("#observablehq-sidebar > ol:first-child a");
    const sidebar = document.querySelector("#observablehq-sidebar");
    const sidebarHeader = sidebar?.querySelector(":scope > ol:first-child");
    const sidebarHeaderItem = sidebarHeader?.querySelector(":scope > li");
    const headerHome = document.querySelector(".shell-home");
    const headingAnchors = [...document.querySelectorAll(
      '#observablehq-main :is(h2, h3) > a[data-saltbytes-heading-anchor="true"]'
    )];
    return {
      sidebarHomeDisplay: sidebarHome ? getComputedStyle(sidebarHome).display : null,
      sidebarHeaderLabel: sidebarHeaderItem
        ? getComputedStyle(sidebarHeaderItem, "::before").content.replaceAll('"', "")
        : null,
      headerHomeHref: headerHome?.href ?? null,
      sidebarBackground: sidebar ? getComputedStyle(sidebar).backgroundColor : null,
      sidebarHeaderBackground: sidebarHeader ? getComputedStyle(sidebarHeader, "::before").backgroundColor : null,
      themeRightGap: main && themeControl
        ? Math.abs(main.getBoundingClientRect().right - themeControl.getBoundingClientRect().right)
        : null,
      headingAnchorCount: headingAnchors.length,
      headingAnchorsNoninteractive: headingAnchors.every(
        (anchor) => !anchor.hasAttribute("href") && anchor.tabIndex === -1
      ),
      headingTargetsPreserved: headingAnchors.every(
        (anchor) => Boolean(anchor.parentElement?.id)
      )
    };
  });
  if (
    shellLayout.sidebarHomeDisplay !== "none"
    || shellLayout.sidebarHeaderLabel !== "Navigation"
    || shellLayout.headerHomeHref !== "https://epmelito.github.io/SaltBytes/"
    || !shellLayout.sidebarBackground
    || shellLayout.sidebarHeaderBackground !== shellLayout.sidebarBackground
    || shellLayout.themeRightGap === null
    || shellLayout.themeRightGap > 32
    || shellLayout.headingAnchorCount === 0
    || !shellLayout.headingAnchorsNoninteractive
    || !shellLayout.headingTargetsPreserved
  ) {
    throw new Error(`dashboard shell polish is incomplete: ${JSON.stringify(shellLayout)}`);
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

async function assertThemeBehavior(page, base, errors) {
  await page.evaluate(() => localStorage.removeItem("saltbytes-theme"));
  await page.emulateMedia({colorScheme: "light"});
  await openPage(page, `${base}/conditions`, errors);

  const readTheme = () => page.evaluate(() => ({
    resolved: document.documentElement.dataset.saltbytesTheme,
    preference: document.documentElement.dataset.saltbytesThemePreference,
    stored: localStorage.getItem("saltbytes-theme"),
    activeChoice: document.querySelector(
      '[data-saltbytes-theme-choice][aria-pressed="true"]'
    )?.dataset.saltbytesThemeChoice
  }));

  await page.waitForFunction(() =>
    document.documentElement.dataset.saltbytesTheme === "light"
      && document.querySelector('[data-saltbytes-theme-choice="system"]')?.getAttribute("aria-pressed") === "true"
  );
  let state = await readTheme();
  if (state.resolved !== "light" || state.preference !== "system" || state.stored !== null) {
    throw new Error(`System theme default is incorrect: ${JSON.stringify(state)}`);
  }

  await page.locator('[data-saltbytes-theme-choice="dark"]').click();
  await page.waitForFunction(() => document.documentElement.dataset.saltbytesTheme === "dark");
  state = await readTheme();
  if (state.preference !== "dark" || state.stored !== "dark" || state.activeChoice !== "dark") {
    throw new Error(`Dark theme selection did not persist: ${JSON.stringify(state)}`);
  }

  await openPage(page, `${base}/pipeline-monitoring`, errors);
  await page.reload({waitUntil: "networkidle"});
  state = await readTheme();
  if (state.resolved !== "dark" || state.preference !== "dark" || state.activeChoice !== "dark") {
    throw new Error(`Dark theme did not persist across routes and refresh: ${JSON.stringify(state)}`);
  }

  await page.locator('[data-saltbytes-theme-choice="system"]').click();
  await page.emulateMedia({colorScheme: "dark"});
  await page.waitForFunction(() => document.documentElement.dataset.saltbytesTheme === "dark");
  await page.emulateMedia({colorScheme: "light"});
  await page.waitForFunction(() => document.documentElement.dataset.saltbytesTheme === "light");
  state = await readTheme();
  if (state.preference !== "system" || state.stored !== "system" || state.activeChoice !== "system") {
    throw new Error(`System theme did not follow the operating system preference: ${JSON.stringify(state)}`);
  }

  await page.locator('[data-saltbytes-theme-choice="light"]').click();
  await page.emulateMedia({colorScheme: "dark"});
  state = await readTheme();
  if (state.resolved !== "light" || state.preference !== "light" || state.stored !== "light") {
    throw new Error(`Explicit light theme did not override the operating system: ${JSON.stringify(state)}`);
  }

  await page.locator('[data-saltbytes-theme-choice="system"]').click();
  await page.emulateMedia({colorScheme: "light"});
}

async function assertForecastRevisions(page) {
  await page.waitForFunction(() => {
    const summary = document.querySelector(".revision-summary");
    const chart = document.querySelector(".revision-chart svg");
    const recent = document.querySelector(".revision-recent-table");
    return summary && chart && recent;
  });

  const readState = () => page.evaluate(() => {
    const metrics = Object.fromEntries(
      [...document.querySelectorAll("[data-revision-metric]")]
        .map((item) => [
          item.dataset.revisionMetric,
          {
            value: item.querySelector("strong")?.textContent.trim() ?? "",
            detail: item.querySelector("small")?.textContent.trim() ?? ""
          }
        ])
    );
    const recentRows = [...document.querySelectorAll(".revision-recent-table tbody tr")];
    const runIds = recentRows.map((row) => ({
      text: row.querySelector("code")?.textContent ?? "",
      full: row.querySelector("code")?.title ?? ""
    }));
    const summary = document.querySelector(".revision-summary");
    const chart = document.querySelector(".revision-chart");
    const chartText = chart?.textContent ?? "";
    const linePath = chart?.querySelector(".revision-history-line path")?.getAttribute("d")
      ?? chart?.querySelector('[aria-label="line"] path')?.getAttribute("d")
      ?? "";
    return {
      summaryState: summary?.dataset.revisionState,
      headline: summary?.querySelector("h2")?.textContent.trim() ?? "",
      summaryText: summary?.textContent.trim() ?? "",
      contextText: summary?.querySelector(".revision-summary-context")?.textContent.trim() ?? "",
      metrics,
      recentRows: recentRows.length,
      runIds,
      detailsCount: document.querySelectorAll(".revision-details").length,
      contextPanelCount: document.querySelectorAll(".revision-context").length,
      chartCount: chart?.querySelectorAll("svg").length ?? 0,
      chartHeight: chart?.querySelector("svg")?.getBoundingClientRect().height ?? 0,
      chartText,
      linePath,
      largestSegments: chart?.querySelectorAll(".revision-largest-segment").length ?? 0,
      latestDots: chart?.querySelectorAll(".revision-latest-dot").length ?? 0,
      oldLanguage: /forecast vintage|persisted vintages|persisted values|universal significance threshold|factual change summary/i.test(document.body.innerText),
      measurementChoices: document.querySelectorAll(".revision-measurement-option").length,
      selectedMeasurement: document.querySelector('.revision-measurement-option[aria-pressed="true"]')
        ?.dataset.revisionMeasurement ?? "",
      summaryMaxWidth: Number.parseFloat(getComputedStyle(summary).maxWidth),
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth
    };
  });

  const initial = await readState();
  if (
    initial.summaryState !== "available"
    || initial.headline !== "Wind speed finished 1.4 km/h lower"
    || !initial.contextText.includes("Jennette's Pier")
    || !initial.contextText.includes("Aug 02, 2026, 08:00 AM EDT")
    || initial.summaryText.includes("It varied from")
    || initial.metrics.latest?.value !== "18.0 km/h"
    || initial.metrics.earliest?.value !== "19.4 km/h"
    || initial.metrics.range?.value !== "18.0–19.4 km/h"
    || initial.metrics["largest-update"]?.value !== "−0.7 km/h"
    || initial.metrics["changed-updates"]?.value !== "2 of 2"
  ) {
    throw new Error(`Forecast revision summary is incorrect: ${JSON.stringify(initial)}`);
  }
  if (
    initial.recentRows !== 3
    || initial.runIds.some((item) => item.text !== item.full || !item.text.startsWith("run-2026"))
    || initial.detailsCount !== 0
    || initial.contextPanelCount !== 0
    || initial.chartCount !== 1
    || initial.chartHeight > 320
    || !initial.linePath
    || initial.largestSegments !== 1
    || initial.latestDots !== 1
    || !initial.chartText.includes("Saved at (ET)")
    || !initial.chartText.includes("Aug 1, 8 PM")
    || initial.chartText.includes("Aug 2, 12 AM")
    || initial.oldLanguage
    || initial.measurementChoices !== 4
    || initial.selectedMeasurement !== "wind_speed_10m"
    || Math.abs(initial.summaryMaxWidth - 1312) > 2
    || initial.pageWidth > initial.viewportWidth
  ) {
    throw new Error(`Forecast revision presentation is incomplete: ${JSON.stringify(initial)}`);
  }

  const initialHeadline = initial.headline;
  const waveChoice = page.locator('[data-revision-measurement="wave_height"]');
  await assertKeyboardFocus(page, waveChoice, "Forecast revisions measurement control");
  await waveChoice.press("Enter");
  await page.waitForFunction(
    (before) => document.querySelector(".revision-summary h2")?.textContent.trim() !== before,
    initialHeadline
  );
  const metricState = await readState();
  if (
    metricState.headline !== "Wave height finished 0.20 m lower"
    || metricState.metrics.latest?.value !== "1.20 m"
    || metricState.metrics.range?.value !== "1.20–1.40 m"
    || metricState.metrics["largest-update"]?.value !== "−0.10 m"
    || metricState.metrics["changed-updates"]?.value !== "2 of 2"
  ) {
    throw new Error(`Forecast revisions measurement control is incorrect: ${JSON.stringify(metricState)}`);
  }

  const contextBeforeTime = metricState.contextText;
  const validOptions = await page.locator("select").nth(1).locator("option").count();
  await selectOption(page, 1, validOptions - 1, "Forecast revisions forecast time control");
  await page.waitForFunction(
    (before) => document.querySelector(".revision-summary-context")?.textContent.trim() !== before,
    contextBeforeTime
  );
  const timeState = await readState();
  if (
    timeState.selectedMeasurement !== "wave_height"
    || timeState.recentRows !== 3
    || timeState.chartCount !== 1
  ) {
    throw new Error(`Forecast revisions time selection is out of sync: ${JSON.stringify(timeState)}`);
  }

  const contextBeforeLocation = await page.locator(".revision-summary-context").innerText();
  await selectOption(page, 0, 1, "Forecast revisions location control");
  await page.waitForFunction(
    (before) => document.querySelector(".revision-summary-context")?.textContent.trim() !== before,
    contextBeforeLocation
  );
  const locationState = await readState();
  if (
    locationState.selectedMeasurement !== "wave_height"
    || locationState.recentRows !== 3
    || locationState.chartCount !== 1
    || !locationState.contextText.includes("Ocracoke Island")
  ) {
    throw new Error(`Forecast revisions location selection is out of sync: ${JSON.stringify(locationState)}`);
  }
}

async function assertForecastRevisionLongHistory(page, base, errors) {
  const historyPattern = "**/forecast-history.*.json";
  const longHistoryHandler = async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    const template = payload[0];
    const firstRun = Date.parse(template.run_started_at) - 36 * 60 * 60 * 1000;
    const windValues = [20.5, 20.3, null, 19.9, 20.1, 20.3, 20.5];
    const waveValues = [0.62, 0.64, 0.64, 0.60, 0.58, 0.60, 0.62];
    const expanded = windValues.map((value, index) => {
      const runDate = new Date(firstRun + index * 6 * 60 * 60 * 1000);
      const runId = `run-${runDate.toISOString().replaceAll("-", "").replaceAll(":", "").replace(".000", "")}`;
      return {
        ...template,
        run_id: runId,
        run_started_at: runDate.toISOString(),
        wind_speed_10m: value,
        wave_height: waveValues[index]
      };
    });
    await route.fulfill({
      response,
      contentType: "application/json",
      body: JSON.stringify(expanded)
    });
  };

  await page.route(historyPattern, longHistoryHandler);
  await openPage(page, `${base}/forecast-revisions`, errors);
  await page.waitForFunction(() => document.querySelector(".revision-details"));

  const readLongState = () => page.evaluate(() => {
    const summary = document.querySelector(".revision-summary");
    const metrics = Object.fromEntries(
      [...document.querySelectorAll("[data-revision-metric]")]
        .map((item) => [
          item.dataset.revisionMetric,
          item.querySelector("strong")?.textContent.trim() ?? ""
        ])
    );
    return {
      headline: summary?.querySelector("h2")?.textContent.trim() ?? "",
      summaryText: summary?.textContent.trim() ?? "",
      metrics,
      recentRows: document.querySelectorAll(".revision-recent-table tbody tr").length,
      runIds: [...document.querySelectorAll(".revision-recent-table code")].map((item) => ({
        text: item.textContent,
        full: item.title
      })),
      detailsClosed: !document.querySelector(".revision-details")?.open,
      chartCount: document.querySelectorAll(".revision-chart svg").length,
      chartDots: document.querySelectorAll(".revision-chart svg circle").length,
      largestSegments: document.querySelectorAll(".revision-largest-segment").length,
      notice: document.querySelector(".revision-notice")?.textContent.trim() ?? "",
      chartFooter: document.querySelector(".revision-chart-footer")?.textContent.trim() ?? ""
    };
  });

  const state = await readLongState();
  if (
    state.headline !== "Wind speed finished where it started"
    || state.metrics.range !== "19.9–20.5 km/h"
    || state.metrics["largest-update"] !== "−0.4 km/h"
    || state.metrics["changed-updates"] !== "5 of 5"
    || state.summaryText.includes("It varied from")
    || state.recentRows !== 5
    || state.runIds.some((item) => !item.text.includes("…") || item.full.length <= item.text.length)
    || state.runIds.some((item) => item.full === "run-20260801T000000Z")
    || !state.runIds.some((item) => item.full === "run-20260731T180000Z")
    || !state.detailsClosed
    || state.chartCount !== 1
    || state.chartDots !== 7
    || state.largestSegments !== 1
  ) {
    throw new Error(`Forecast revision long history is incomplete: ${JSON.stringify(state)}`);
  }

  await selectRevisionMetric(page, "wave_height", "Forecast revisions long history wave control");
  await page.waitForFunction(() =>
    document.querySelector(".revision-summary h2")?.textContent.trim()
      === "Wave height finished where it started"
  );
  const waveState = await readLongState();
  if (
    waveState.metrics.latest !== "0.62 m"
    || waveState.metrics.range !== "0.58–0.64 m"
    || waveState.metrics["largest-update"] !== "−0.04 m"
    || waveState.metrics["changed-updates"] !== "5 of 6"
    || waveState.chartCount !== 1
    || waveState.chartDots !== 8
    || waveState.largestSegments !== 1
    || !waveState.chartFooter.includes("−0.04 m")
    || waveState.chartFooter.includes("0.00 m")
  ) {
    throw new Error(`Forecast revision precision is incorrect: ${JSON.stringify(waveState)}`);
  }

  const waveDetails = page.locator(".revision-details");
  await waveDetails.locator("summary").click();
  await page.waitForFunction(() => document.querySelector(".revision-details")?.open);
  const waveCompleteRows = await page.locator(".revision-complete-table tbody tr").count();
  if (waveCompleteRows !== 7) {
    throw new Error(`Forecast revision wave complete history is incomplete: ${waveCompleteRows}`);
  }
  await waveDetails.locator("summary").click();
  await page.waitForFunction(() => !document.querySelector(".revision-details")?.open);

  await page.locator(".revision-chart svg circle").first().hover();
  try {
    await page.waitForFunction(() =>
      document.querySelector(".revision-chart")?.textContent
        .includes("Jul 31, 2026, 08:00 AM EDT")
    );
  } catch {
    throw new Error("Forecast revision tooltip does not show the full local saved time");
  }

  await selectRevisionMetric(page, "tide_predicted_range", "Forecast revisions long history flat control");
  await page.waitForFunction(() =>
    document.querySelector(".revision-summary h2")?.textContent.trim()
      === "Predicted tide range did not change"
  );
  const flatState = await readLongState();
  if (
    flatState.metrics.range !== "0.86 m"
    || flatState.metrics["largest-update"] !== "No change"
    || flatState.metrics["changed-updates"] !== "0 of 6"
    || flatState.chartCount !== 0
    || flatState.largestSegments !== 0
    || !flatState.notice.includes("No changes to plot")
  ) {
    throw new Error(`Forecast revision flat history is incorrect: ${JSON.stringify(flatState)}`);
  }

  await selectRevisionMetric(page, "wind_speed_10m", "Forecast revisions long history wind control");
  await page.waitForFunction(() =>
    document.querySelector(".revision-summary h2")?.textContent.trim()
      === "Wind speed finished where it started"
  );

  const details = page.locator(".revision-details");
  await assertKeyboardFocus(
    page,
    details.locator("summary"),
    "Forecast revision details"
  );
  await details.locator("summary").press("Enter");
  await page.waitForFunction(() => document.querySelector(".revision-details")?.open);
  const completeRows = await page.locator(".revision-complete-table tbody tr").count();
  const detailText = await details.innerText();
  if (
    completeRows !== 6
    || !detailText.includes("run-20260731T120000Z")
    || !detailText.includes("Complete available history and exact run identifiers")
  ) {
    throw new Error("Forecast revision complete history is incomplete");
  }

  await page.unroute(historyPattern, longHistoryHandler);
}

async function assertForecastRevisionSparseStates(page, base, errors) {
  const historyPattern = "**/forecast-history.*.json";
  const singleHandler = async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    await route.fulfill({
      response,
      contentType: "application/json",
      body: JSON.stringify(payload.slice(0, 1))
    });
  };

  await page.route(historyPattern, singleHandler);
  await openPage(page, `${base}/forecast-revisions`, errors);
  await page.waitForFunction(() =>
    document.querySelector(".revision-summary")?.dataset.revisionState === "single"
  );
  const single = await page.evaluate(() => ({
    headline: document.querySelector(".revision-summary h2")?.textContent.trim() ?? "",
    latest: document.querySelector('[data-revision-metric="latest"] strong')?.textContent.trim(),
    range: document.querySelector('[data-revision-metric="range"] strong')?.textContent.trim(),
    changed: document.querySelector('[data-revision-metric="changed-updates"] strong')?.textContent.trim(),
    recentRows: document.querySelectorAll(".revision-recent-table tbody tr").length,
    chartCount: document.querySelectorAll(".revision-chart svg").length,
    notice: document.querySelector(".revision-notice")?.textContent.trim() ?? "",
    detailsCount: document.querySelectorAll(".revision-details").length
  }));
  if (
    single.headline !== "Wind speed has one saved value"
    || single.latest !== "19.4 km/h"
    || single.range !== "19.4 km/h"
    || single.changed !== "0 of 0"
    || single.recentRows !== 1
    || single.chartCount !== 0
    || !single.notice.includes("Another saved forecast is needed")
    || single.detailsCount !== 0
  ) {
    throw new Error(`Forecast revision single state is incorrect: ${JSON.stringify(single)}`);
  }
  await page.unroute(historyPattern, singleHandler);

  const emptyHandler = async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: "[]"
    });
  };
  await page.route(historyPattern, emptyHandler);
  await openPage(page, `${base}/forecast-revisions`, errors);
  await page.waitForFunction(() =>
    document.querySelector(".revision-summary")?.dataset.revisionState === "empty"
  );
  const empty = await page.evaluate(() => ({
    headline: document.querySelector(".revision-summary h2")?.textContent.trim() ?? "",
    latest: document.querySelector('[data-revision-metric="latest"] strong')?.textContent.trim(),
    range: document.querySelector('[data-revision-metric="range"] strong')?.textContent.trim(),
    changed: document.querySelector('[data-revision-metric="changed-updates"] strong')?.textContent.trim(),
    notice: document.querySelector(".revision-notice")?.textContent.trim() ?? "",
    chartCount: document.querySelectorAll(".revision-chart svg").length,
    recentTableCount: document.querySelectorAll(".revision-recent-table").length,
    detailsCount: document.querySelectorAll(".revision-details").length
  }));
  if (
    empty.headline !== "No saved wind speed values"
    || empty.latest !== "Unavailable"
    || empty.range !== "Unavailable"
    || empty.changed !== "0 of 0"
    || !empty.notice.includes("Try another location, forecast time, or measurement")
    || empty.chartCount !== 0
    || empty.recentTableCount !== 0
    || empty.detailsCount !== 0
  ) {
    throw new Error(`Forecast revision empty state is incorrect: ${JSON.stringify(empty)}`);
  }
  await page.unroute(historyPattern, emptyHandler);
}

async function assertPipelineMonitoring(page) {
  await page.waitForFunction(() => {
    const health = document.querySelector(".pipeline-health");
    const chart = document.querySelector(".pipeline-reliability svg");
    const matrix = document.querySelector(".pipeline-matrix");
    return health && chart && matrix;
  });

  const state = await page.evaluate(() => {
    const headings = [...document.querySelectorAll("#observablehq-main h2")]
      .map((heading) => heading.textContent.trim());
    const health = document.querySelector(".pipeline-health");
    const activeExceptions = [...document.querySelectorAll(".pipeline-exception")];
    const matrix = document.querySelector(".pipeline-matrix");
    const matrixRows = [...(matrix?.querySelectorAll("tbody tr") ?? [])];
    const latestRows = [...document.querySelectorAll(".pipeline-runs-table tbody tr")];
    const shortIds = latestRows.map((row) => ({
      text: row.querySelector("code")?.textContent ?? "",
      full: row.querySelector("code")?.title ?? ""
    }));
    const details = document.querySelector(".pipeline-details");
    const reliability = document.querySelector(".pipeline-reliability");
    return {
      headings,
      healthState: health?.dataset.healthState,
      healthText: health?.textContent ?? "",
      activeCount: activeExceptions.length,
      activeText: activeExceptions.map((item) => item.textContent.trim()),
      matrixRows: matrixRows.length,
      matrixColumns: matrix?.querySelectorAll("thead th").length ?? 0,
      attentionCells: matrix?.querySelectorAll(".coverage-failed, .coverage-missing").length ?? 0,
      notApplicableCells: [...(matrix?.querySelectorAll("td") ?? [])]
        .filter((cell) => cell.textContent.trim() === "Not applicable").length,
      latestRows: latestRows.length,
      shortIds,
      detailsClosed: details ? !details.open : false,
      reliabilityCharts: reliability?.querySelectorAll("svg").length ?? 0,
      oldChartGrid: Boolean(document.querySelector(".chart-grid")),
      oldSourceHeading: headings.includes("Source success rates"),
      oldRowsHeading: headings.includes("Rows loaded"),
      coverageControlAfterHeading: Boolean([...document.querySelectorAll("#observablehq-main h2")]
        .find((heading) => heading.textContent.trim() === "Source and location health")
        ?.compareDocumentPosition(document.querySelector("select")?.closest(".observablehq--block")) & Node.DOCUMENT_POSITION_FOLLOWING),
      gridMaxWidth: Number.parseFloat(getComputedStyle(health).maxWidth),
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth
    };
  });

  const expectedOrder = [
    "Active failures and missing data",
    "Recent reliability",
    "Source and location health",
    "Latest runs"
  ];
  const order = expectedOrder.map((heading) => state.headings.indexOf(heading));
  if (order.some((index) => index < 0) || order.some((index, position) => position && index <= order[position - 1])) {
    throw new Error(`Pipeline monitoring hierarchy is incorrect: ${JSON.stringify(state.headings)}`);
  }
  if (
    state.healthState !== "degraded"
    || !state.healthText.includes("partial forecast data remains available")
    || !state.healthText.includes("6 of 25 source checks")
    || state.activeCount !== 6
    || !state.activeText.some((item) => item.includes("Fetch failed"))
    || !state.activeText.some((item) => item.includes("Not recorded"))
  ) {
    throw new Error(`Pipeline degraded state is incomplete: ${JSON.stringify(state)}`);
  }
  if (
    state.matrixRows !== 5
    || state.matrixColumns !== 6
    || state.attentionCells !== 6
    || state.notApplicableCells !== 0
    || state.latestRows < 1
    || state.latestRows > 10
    || state.shortIds.some((item) => !item.text.includes("…") || item.full.length <= item.text.length)
  ) {
    throw new Error(`Pipeline compact evidence is incomplete: ${JSON.stringify(state)}`);
  }
  if (
    !state.detailsClosed
    || state.reliabilityCharts !== 1
    || state.oldChartGrid
    || state.oldSourceHeading
    || state.oldRowsHeading
    || !state.coverageControlAfterHeading
    || Math.abs(state.gridMaxWidth - 1152) > 2
    || state.pageWidth > state.viewportWidth
  ) {
    throw new Error(`Pipeline layout is incomplete: ${JSON.stringify(state)}`);
  }

  const details = page.locator(".pipeline-details");
  await details.locator("summary").focus();
  const focusStyle = await details.locator("summary").evaluate(
    (element) => getComputedStyle(element).outlineStyle
  );
  if (focusStyle === "none") throw new Error("Pipeline details disclosure has no visible keyboard focus");
  await details.locator("summary").press("Enter");
  await page.waitForFunction(() => document.querySelector(".pipeline-details")?.open);
  const detailText = await details.innerText();
  if (
    !detailText.includes("Complete run records")
    || !detailText.includes("Recent source summary")
    || !detailText.includes("The public dashboard shows source status labels without raw error details.")
  ) {
    throw new Error("Pipeline detailed evidence is incomplete");
  }

  const pipelineWidths = await page.evaluate(() => ({
    runs: document.querySelector(".pipeline-runs-scroll")?.getBoundingClientRect().width ?? 0,
    details: document.querySelector(".pipeline-details")?.getBoundingClientRect().width ?? 0
  }));
  if (!pipelineWidths.runs || Math.abs(pipelineWidths.runs - pipelineWidths.details) > 2) {
    throw new Error(`Pipeline run sections are not aligned: ${JSON.stringify(pipelineWidths)}`);
  }

  const coverageSummary = await page.locator(".pipeline-section-summary strong").innerText();
  await selectOption(page, 0, 1, "Pipeline coverage control");
  await page.waitForFunction(
    (before) => document.querySelector(".pipeline-section-summary strong")?.textContent !== before,
    coverageSummary
  );
  const selectedCoverage = await page.evaluate(() => ({
    summary: document.querySelector(".pipeline-section-summary strong")?.textContent ?? "",
    attentionCells: document.querySelectorAll(".pipeline-matrix .coverage-failed, .pipeline-matrix .coverage-missing").length
  }));
  if (!selectedCoverage.summary.includes("All 25 source checks succeeded") || selectedCoverage.attentionCells !== 0) {
    throw new Error(`Pipeline coverage selection did not update: ${JSON.stringify(selectedCoverage)}`);
  }
}

async function assertObservationHealthStates(page, base, errors) {
  const observationPattern = "**/observation-health.*.json";
  const attempt = (source, status) => ({
    source,
    attempted_at: "2026-08-13T12:00:00Z",
    status,
    new_review_patterns: 0,
    previously_seen_review_patterns: 0,
    outstanding_review_patterns: 0
  });
  const cases = [
    {
      state: "completed",
      message: "Latest fishing observation update completed.",
      attempts: [attempt("jennettes_pier", "success"), attempt("sunset_beach_pier", "success")]
    },
    {
      state: "attention",
      message: "Latest fishing observation update needs attention. One or more report sources did not complete.",
      attempts: [attempt("jennettes_pier", "failed"), attempt("sunset_beach_pier", "success")]
    },
    {
      state: "attention",
      message: "Latest fishing observation update needs attention. One or more report sources did not complete.",
      attempts: [attempt("jennettes_pier", "success"), attempt("sunset_beach_pier", "failed")]
    },
    {
      state: "not-run",
      message: "Fishing observation update has not run yet.",
      attempts: []
    }
  ];

  for (const testCase of cases) {
    const handler = async (route) => {
      const response = await route.fetch();
      await route.fulfill({
        response,
        contentType: "application/json",
        body: JSON.stringify({
          latest_attempt: testCase.attempts.at(-1) ?? null,
          latest_attempts: testCase.attempts,
          outstanding_patterns: []
        })
      });
    };
    await page.route(observationPattern, handler);
    await openPage(page, `${base}/pipeline-monitoring`, errors);
    await page.waitForFunction((state) =>
      document.querySelector(".observation-review-summary")?.dataset.observationState === state,
      testCase.state
    );
    const message = await page.locator(".observation-review-summary strong").textContent();
    if (message?.trim() !== testCase.message) {
      throw new Error(`Fishing observation summary is incorrect for ${testCase.state}: ${message}`);
    }
    await page.unroute(observationPattern, handler);
  }
}

async function assertConditionsHierarchy(page, verifyDetails = false) {
  await page.waitForFunction(() => {
    const headings = [...document.querySelectorAll("#observablehq-main h2")]
      .map((heading) => heading.textContent.trim());
    const handoff = document.querySelector(".species-handoff");
    const current = document.querySelector(".conditions-current");
    const text = document.querySelector("#observablehq-main")?.textContent ?? "";
    const currentText = current?.textContent ?? "";
    const groups = [...(current?.querySelectorAll(".conditions-current-group") ?? [])]
      .map((group) => group.textContent ?? "");
    return headings.indexOf("Current coastal conditions") >= 0
      && headings.indexOf("Current coastal conditions") < headings.indexOf("Upcoming changes")
      && headings.indexOf("Upcoming changes") < headings.indexOf("Supporting evidence and limitations")
      && !headings.includes("Spanish mackerel assessment")
      && current && handoff
      && !text.includes("What SaltBytes cannot observe")
      && !text.includes("Assessment factors and confidence")
      && !document.querySelector(".conditions-assessment")
      && currentText.includes("Air temperature")
      && currentText.includes("Barometric pressure")
      && currentText.includes("Sky and sun")
      && groups.length === 2
      && groups[0].includes("Coastal conditions")
      && ["Wind", "Waves", "Water temperature", "Tide"].every((label) => groups[0].includes(label))
      && groups[1].includes("Weather and sky")
      && ["Air temperature", "Barometric pressure", "Sky and sun", "Precipitation"].every((label) => groups[1].includes(label))
      && current.querySelector(".conditions-tide-details summary")?.textContent.includes("Tide details");
  });

  if (!verifyDetails) return;

  const tideDetails = page.locator(".conditions-tide-details");
  if ((await tideDetails.innerText()).includes("Previous ")) {
    throw new Error("tide events are visible before Tide details opens");
  }
  await tideDetails.locator("summary").press("Enter");
  await page.waitForFunction(() => document.querySelector(".conditions-tide-details")?.open);
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
    || !sourceText.includes("exact fishing location may differ")
    || sourceText.includes("Previous low")
    || sourceText.includes("Next high")
  ) {
    throw new Error("Sources and forecast limitations does not contain the intended concise explanations");
  }
}

async function assertConditionsAssessmentHandoff(page, base, errors) {
  const handoff = page.locator(".species-handoff a");
  const href = await handoff.getAttribute("href");
  const expected = new URL(href ?? "", base);
  const context = await page.evaluate(() => ({
    location: document.querySelector(".conditions-context h2")?.textContent,
    time: document.querySelector(".conditions-context p strong")?.parentElement?.textContent
  }));
  if (expected.pathname !== "/species-assessments" || !expected.searchParams.get("location") || !expected.searchParams.get("forecast_time")) {
    throw new Error("Conditions species-assessment handoff has no selected context");
  }
  await Promise.all([
    page.waitForURL(expected.href),
    handoff.click()
  ]);
  await page.waitForFunction(
    (expectedContext) => document.querySelector(".conditions-context h2")?.textContent === expectedContext.location
      && document.querySelector(".conditions-context p strong")?.parentElement?.textContent === expectedContext.time,
    context
  );
  await assertHealthy(page, errors, "Conditions species-assessment handoff");
}

async function assertSpeciesAssessments(page, base, errors) {
  const query = "location=jennettes_pier&forecast_time=2026-08-02T12%3A00%3A00Z";
  await openPage(page, `${base}/species-assessments?${query}`, errors);
  await assertShell(page, "Coastal conditions", "Species assessments");
  await page.waitForFunction(() => document.querySelectorAll("select").length === 2);
  const state = await page.evaluate(() => ({
    location: document.querySelector(".conditions-context h2")?.textContent,
    time: document.querySelector(".conditions-context p strong")?.parentElement?.textContent,
    text: document.querySelector("#observablehq-main")?.textContent ?? "",
    width: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth
  }));
  if (state.location !== "Jennette's Pier" || !state.time?.includes("Aug 02, 2026, 08:00 AM EDT") || state.width > state.viewport
    || !state.text.includes("Spanish mackerel assessment") || !state.text.includes("Score")
    || !state.text.includes("support the assessment, while waves limit it.")
    || !state.text.includes("What SaltBytes cannot observe") || !state.text.includes("does not estimate fish presence, catch likelihood, or safety")
    || state.text.includes("spanish-mackerel-v1.0.0")) {
    throw new Error(`Species assessments direct context is incorrect: ${JSON.stringify(state)}`);
  }
  const disclosure = page.locator(".conditions-assessment details summary");
  await disclosure.focus();
  if (await disclosure.evaluate((element) => getComputedStyle(element).outlineStyle) === "none") {
    throw new Error("Species assessment disclosure has no visible keyboard focus");
  }
  await disclosure.press("Enter");
  await page.waitForFunction(() => document.querySelector(".conditions-assessment details")?.open);
  const before = state.text;
  await selectOption(page, 0, 1, "Species assessments location control");
  await page.waitForFunction((previous) => document.querySelector("#observablehq-main")?.textContent !== previous, before);
  await assertHealthy(page, errors, "Species assessments");
}

async function assertConditionsVisualizations(page, available) {
  await page.waitForFunction(() => document.querySelector(".shore-direction")
    && document.querySelectorAll(".trend-track svg").length === 5);
  const readiness = await page.evaluate(() => {
    const trendStory = document.querySelector(".forecast-context");
    const tide = document.querySelector(".tide-timing, .visual-unavailable");
    const direction = document.querySelector(".shore-direction");
    const selectedRules = document.querySelectorAll(".selected-time-rule");
    return {
      trendStory: Boolean(trendStory),
      trendTracks: document.querySelectorAll(".forecast-surface").length === 5,
      selectedRules: selectedRules.length,
      tide: Boolean(tide),
      direction: Boolean(direction),
      oldChartGrid: Boolean(document.querySelector(".chart-grid"))
    };
  });
  if (
    !readiness.trendStory
    || !readiness.trendTracks
    || readiness.selectedRules !== 5
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
      forecastOptionCount: document.querySelectorAll("select")[1]?.options.length ?? 0,
      limitedPreview: forecastTrends?.textContent.includes("forecast hours are available in this preview.") ?? false,
      localTicks: [...document.querySelectorAll(".forecast-temperature .trend-track svg text")].map((text) => text.textContent),
      duplicateLocalTimeTicks: (() => {
        const labels = [...document.querySelectorAll(".forecast-temperature .trend-track svg text")]
          .map((text) => text.textContent.trim())
          .filter((text) => /(?:AM|PM)$/.test(text));
        return new Set(labels).size !== labels.length;
      })(),
      gridMaxWidth: Number.parseFloat(getComputedStyle(visualGrid).maxWidth),
      plotLayouts,
      airTemperatureSolid: (() => {
        const line = document.querySelector(".forecast-air-temperature .air-temperature-line");
        return Boolean(line) && getComputedStyle(line).strokeDasharray === "none";
      })(),
      apparentTemperatureDashed: (() => {
        const line = document.querySelector(".forecast-air-temperature .apparent-temperature-line");
        return Boolean(line) && getComputedStyle(line).strokeDasharray !== "none";
      })(),
      pressureTrend: Boolean(document.querySelector(".forecast-pressure .pressure-line")),
      noCloudOrSolarTrend: !document.querySelector(".forecast-cloud, .forecast-solar"),
      tideBox: tide?.querySelector("svg")?.getBoundingClientRect(),
      tideMarker: tide?.querySelector(".tide-selected")?.getBoundingClientRect().left,
      arrows: directionPanels.map((panel) => {
        const arrow = panel.querySelector(".direction-arrow");
        const svg = panel.querySelector("svg");
        const box = arrow?.getBoundingClientRect();
        const svgBox = svg?.getBoundingClientRect();
        const style = arrow ? getComputedStyle(arrow) : null;
        return {
          left: box?.left,
          top: box?.top,
          length: Math.hypot(box?.width ?? 0, box?.height ?? 0),
          inside: box && svgBox && box.left >= svgBox.left && box.right <= svgBox.right && box.top >= svgBox.top && box.bottom <= svgBox.bottom,
          dashArray: style?.strokeDasharray,
          strokeWidth: style?.strokeWidth
        };
      }),
      scoreAvailable
    };
  }, available);
  if (
    !visualState.tideLimitation
    || !visualState.noOverflow
    || visualState.selectedMarkers.some((marker) => !Number.isFinite(marker))
    || !visualState.selectedTime.includes("Selected time:")
    || visualState.forecastOptionCount < 1
    || (visualState.forecastOptionCount < 12 && !visualState.limitedPreview)
    || (visualState.forecastOptionCount >= 12 && visualState.limitedPreview)
    || visualState.duplicateLocalTimeTicks
    || !Number.isFinite(visualState.gridMaxWidth)
    || visualState.gridMaxWidth > 1152.5
    || visualState.plotLayouts.length !== 5
    || visualState.plotLayouts.some((layout) => !Number.isFinite(layout.svgWidth)
      || Math.abs(layout.trackWidth - layout.svgWidth) > 2
      || layout.svgHeight < 200
      || layout.svgHeight > 300)
    || !visualState.airTemperatureSolid
    || !visualState.apparentTemperatureDashed
    || !visualState.pressureTrend
    || !visualState.noCloudOrSolarTrend
    || visualState.tideBox.width > 1024
    || visualState.tideBox.height > 300
    || visualState.arrows.length !== 2
    || visualState.arrows.some((arrow) => arrow.length < 20 || !arrow.inside || arrow.dashArray !== "none")
    || new Set(visualState.arrows.map((arrow) => arrow.strokeWidth)).size !== 1
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

async function assertConditionsUnavailableContextAndSolarRollover(page, base, errors) {
  const conditionsPattern = "**/conditions.*.json";
  const handler = async (route) => {
    const response = await route.fetch();
    const conditions = await response.json();
    const selected = conditions.find((row) => row.location_id === "jennettes_pier");
    if (!selected) throw new Error("Conditions fixture has no Jennette's Pier row");
    const rollover = {
      ...selected,
      forecast_time: "2026-08-03T12:00:00Z",
      sunrise: "2026-08-03T10:00:00Z",
      sunset: "2026-08-03T22:00:00Z",
      air_temperature: null,
      apparent_temperature: null,
      pressure_msl: null
    };
    for (const row of conditions) {
      row.air_temperature = null;
      row.apparent_temperature = null;
      row.pressure_msl = null;
      row.sunrise = "2026-08-02T06:00:00Z";
      row.sunset = "2026-08-02T10:00:00Z";
    }
    conditions.push(rollover);
    await route.fulfill({
      response,
      contentType: "application/json",
      body: JSON.stringify(conditions)
    });
  };
  await page.route(conditionsPattern, handler);
  await openPage(page, `${base}/conditions`, errors);
  await page.waitForFunction(() => document.querySelector(".forecast-pressure"));
  const state = await page.evaluate(() => ({
    text: document.querySelector(".conditions-current")?.textContent ?? "",
    unavailable: [...document.querySelectorAll(".visual-data-unavailable")]
      .map((notice) => notice.textContent),
    airLine: Boolean(document.querySelector(".air-temperature-line, .apparent-temperature-line")),
    pressureLine: Boolean(document.querySelector(".pressure-line"))
  }));
  if (
    !state.text.includes("Sunrise in 22h")
    || !state.unavailable.includes("Air temperature and feels-like temperature are unavailable in this forecast.")
    || !state.unavailable.includes("Barometric pressure is unavailable in this forecast.")
    || state.airLine
    || state.pressureLine
  ) {
    throw new Error(`Conditions unavailable context is incorrect: ${JSON.stringify(state)}`);
  }
  await assertHealthy(page, errors, "Conditions unavailable context");
  await page.unroute(conditionsPattern, handler);
}


async function assertDataProvenance(page) {
  await page.waitForFunction(() =>
    document.querySelector('.provenance-verdict[data-traceability-state="complete"]')
      && document.querySelectorAll(".provenance-source-option").length === 5
      && document.querySelectorAll(".provenance-lineage li").length === 4
  );

  const readState = () => page.evaluate(() => {
    const verdict = document.querySelector(".provenance-verdict");
    const sourceRows = [...document.querySelectorAll(".provenance-source-option")];
    const details = document.querySelector(".provenance-details");
    const locationDetails = document.querySelector(".provenance-location-details");
    const sourceInspector = document.querySelector(".provenance-source-inspector");
    const lineage = document.querySelector(".provenance-lineage");
    const columnNames = ["source", "provider", "captured"];
    const columnPositions = Object.fromEntries(columnNames.map((column) => [
      column,
      sourceRows.map((row) =>
        row.querySelector(`[data-provenance-column="${column}"]`)?.getBoundingClientRect().left
      )
    ]));
    const columnsAligned = Object.values(columnPositions).every((positions) =>
      positions.length === 5
        && positions.every((position) => Number.isFinite(position))
        && Math.max(...positions) - Math.min(...positions) < 1
    );
    return {
      pageTitle: document.querySelector("#observablehq-main h1")?.textContent.trim() ?? "",
      introText: document.querySelector(".provenance-intro")?.textContent.trim() ?? "",
      verdictState: verdict?.dataset.traceabilityState ?? "",
      headline: verdict?.querySelector("h2")?.textContent.trim() ?? "",
      verdictText: verdict?.textContent.trim() ?? "",
      sourceRows: sourceRows.map((row) => ({
        source: row.dataset.provenanceSource,
        state: row.dataset.traceabilityState,
        selected: row.getAttribute("aria-pressed"),
        text: row.textContent.trim()
      })),
      columnsAligned,
      lineageStages: document.querySelectorAll(".provenance-lineage li").length,
      detailsClosed: !details?.open,
      locationDetailsClosed: !locationDetails?.open,
      selectedSource: sourceInspector?.dataset.selectedSource ?? "",
      detailsBeforeLineage: Boolean(
        sourceInspector
          && lineage
          && (sourceInspector.compareDocumentPosition(lineage) & Node.DOCUMENT_POSITION_FOLLOWING)
      ),
      selectCount: document.querySelectorAll("select").length,
      repeatedHealthyDetail: document.querySelector(".provenance-source-list")?.innerText
        .includes("Provider details and a saved source record are available.") ?? false,
      oldInventoryLanguage: /persisted shoreline orientation/i.test(document.body.innerText),
      oldSourceLanguage: /traceability status|\btraceable\b|snapshot captured|how the forecast is traced|technical evidence for/i
        .test(document.body.innerText),
      internalExportNote: /excludes raw file paths|private storage metadata/i
        .test(document.body.innerText),
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth
    };
  });

  const initial = await readState();
  if (
    initial.pageTitle !== "Forecast sources"
    || !initial.introText.includes("providers support the latest published forecast")
    || initial.verdictState !== "complete"
    || initial.headline !== "Details are available for all 5 forecast sources"
    || !initial.verdictText.includes("Jennette's Pier")
    || !initial.verdictText.includes("5 of 5")
    || initial.sourceRows.length !== 5
    || initial.sourceRows.some((row) => row.state !== "complete")
    || initial.sourceRows.filter((row) => row.selected === "true").length !== 1
    || initial.sourceRows.find((row) => row.selected === "true")?.source !== "weather"
    || !initial.sourceRows.some((row) => row.text.includes("NOAA Tides and Currents"))
    || initial.sourceRows.filter((row) => row.text.includes("Open-Meteo")).length !== 4
    || initial.sourceRows.some((row) => row.text.includes("Traceable"))
    || initial.sourceRows.some((row) => !row.text.includes("Available"))
    || !initial.columnsAligned
    || initial.lineageStages !== 4
    || !initial.detailsClosed
    || !initial.locationDetailsClosed
    || initial.selectedSource !== "weather"
    || !initial.detailsBeforeLineage
    || initial.selectCount !== 1
    || initial.repeatedHealthyDetail
    || initial.oldInventoryLanguage
    || initial.oldSourceLanguage
    || initial.internalExportNote
    || initial.pageWidth > initial.viewportWidth
  ) {
    throw new Error(`Forecast sources complete state is incorrect: ${JSON.stringify(initial)}`);
  }

  const tideButton = page.locator('[data-provenance-source="tide"]');
  await assertKeyboardFocus(page, tideButton, "Forecast source choices");
  await tideButton.press("Enter");
  await page.waitForFunction(() =>
    document.querySelector(".provenance-source-inspector")?.dataset.selectedSource === "tide"
      && document.querySelector('[data-provenance-source="tide"]')?.getAttribute("aria-pressed") === "true"
  );

  const tideState = await readState();
  if (
    tideState.selectedSource !== "tide"
    || tideState.sourceRows.find((row) => row.source === "tide")?.selected !== "true"
  ) {
    throw new Error(`Forecast source selection is incorrect: ${JSON.stringify(tideState)}`);
  }

  const details = page.locator(".provenance-details");
  await assertKeyboardFocus(
    page,
    details.locator("summary"),
    "Forecast source details"
  );
  await details.locator("summary").press("Enter");
  await page.waitForFunction(() => document.querySelector(".provenance-details")?.open);
  const detailText = await details.textContent();
  if (
    !detailText.includes("run-20260802T120000Z-jennettes_pier-tide")
    || !detailText.includes("8652226")
    || !detailText.includes("Tide prediction location")
    || !detailText.includes("NOAA prediction location")
    || !detailText.includes("How the prediction is used")
    || !detailText.includes("NOAA prediction used directly")
    || !detailText.includes("How it applies here")
    || !detailText.includes("Water level reference")
    || !detailText.includes("Mean Lower Low Water (MLLW)")
    || !detailText.includes("Distance to fishing location")
    || !detailText.includes("Direct use at the Atlantic-facing pier")
    || !detailText.includes("Tide predictions are not observed water levels.")
    || !detailText.includes("Tide source details")
    || detailText.includes("Coastal relationship")
    || detailText.includes("Datum")
    || detailText.includes("Location orientation context")
  ) {
    throw new Error("Forecast source technical evidence is incomplete or contains repeated location metadata");
  }

  await page.locator('[data-provenance-source="sst"]').click();
  await page.waitForFunction(() =>
    document.querySelector(".provenance-source-inspector")?.dataset.selectedSource === "sst"
      && document.querySelector(".provenance-details")?.open
  );
  const gridDetailText = await page.locator(".provenance-details").textContent();
  if (
    !gridDetailText.includes("Forecast grid location")
    || !gridDetailText.includes("Point SaltBytes requested")
    || !gridDetailText.includes("Provider grid point returned")
  ) {
    throw new Error("Forecast source grid location language is incomplete");
  }

  await page.locator('[data-provenance-source="tide"]').click();
  await page.waitForFunction(() =>
    document.querySelector(".provenance-source-inspector")?.dataset.selectedSource === "tide"
      && document.querySelector(".provenance-details")?.open
  );

  const locationDetails = page.locator(".provenance-location-details");
  await locationDetails.locator("summary").press("Enter");
  await page.waitForFunction(() => document.querySelector(".provenance-location-details")?.open);
  const locationDetailText = await locationDetails.textContent();
  if (
    !locationDetailText.includes("Direction straight out from shore")
    || !locationDetailText.includes("East northeast (75°)")
    || !locationDetailText.includes("Direction the pier points offshore")
    || !locationDetailText.includes("East northeast (70°)")
    || !locationDetailText.includes("Estimated from satellite imagery")
    || !locationDetailText.includes("Google Maps satellite imagery reviewed 2026-08-01")
    || !locationDetailText.includes("How directions were estimated")
    || !locationDetailText.includes("Reference imagery")
    || !locationDetailText.includes("Direction note")
  ) {
    throw new Error("Forecast source location directions are incomplete");
  }

  const initialLocation = await page.locator(".provenance-verdict").innerText();
  await selectOption(page, 0, 1, "Forecast sources location control");
  await page.waitForFunction(
    (before) => document.querySelector(".provenance-verdict")?.innerText !== before,
    initialLocation
  );
  const updatedLocation = await page.locator(".provenance-verdict").innerText();
  const disclosuresStayedOpen = await page.evaluate(() =>
    document.querySelector(".provenance-details")?.open
      && document.querySelector(".provenance-location-details")?.open
  );
  if (!updatedLocation.includes("Beach Access Ramp 72") || !disclosuresStayedOpen) {
    throw new Error("Forecast sources location control did not update while preserving open details");
  }
}

async function assertPressureOperationsCoverage() {
  const fixtureDirectory = resolve(dist, "..", "src", "data");
  const sourceHealth = JSON.parse(await readFile(join(fixtureDirectory, "source-health.json"), "utf8"));
  const provenance = JSON.parse(await readFile(join(fixtureDirectory, "provenance.json"), "utf8"));
  const legacySources = ["weather", "wave", "sst", "tide"];
  const pressureSources = ["weather", "pressure", "wave", "sst", "tide"];
  const expectedFor = (rows) => pressureSources.filter((source) =>
    rows.some((row) => row.source === source)
  );
  const traceability = (row) => !row?.snapshot_id
    ? "missing"
    : !row.captured_at || !(row.source === "tide" ? row.station_id : row.model_selector)
      ? "incomplete"
      : "complete";

  const selectedLocation = provenance[0]?.location_id;
  const selectedProvenance = provenance.filter((row) => row.location_id === selectedLocation);
  const preIntroduction = selectedProvenance.filter((row) => row.source !== "pressure");
  const incomplete = preIntroduction.map((row) => row.source === "weather"
    ? {...row, captured_at: null, model_selector: null}
    : row.source === "wave"
      ? {...row, snapshot_id: null, captured_at: null, model_selector: null}
      : row
  );
  const incompleteStates = incomplete.map(traceability);
  if (
    expectedFor(preIntroduction).join(",") !== legacySources.join(",")
    || incompleteStates.filter((state) => state === "incomplete").length !== 1
    || incompleteStates.filter((state) => state === "missing").length !== 1
  ) {
    throw new Error("Pre-pressure Forecast sources fixture state is incorrect");
  }

  const historicalRun = "run-20260802T120000Z";
  const currentRun = "run-20260802T180000Z";
  const historicalCoverage = sourceHealth.coverage.filter((row) => row.run_id === historicalRun);
  const failedPressureCoverage = sourceHealth.coverage.map((row) =>
    row.run_id === currentRun && row.source === "pressure"
      ? {...row, status: "fetch_failed"}
      : row
  );
  if (
    expectedFor(selectedProvenance).join(",") !== pressureSources.join(",")
    || historicalCoverage.some((row) => row.source === "pressure") === false
    || failedPressureCoverage.filter((row) =>
      row.run_id === currentRun && row.source === "pressure" && row.status === "fetch_failed"
    ).length !== 5
  ) {
    throw new Error("Pressure Operations fixture state is incorrect");
  }
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
    await assertConditionsHierarchy(page);
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

    await assertConditionsAssessmentHandoff(page, base, errors);
    await assertSpeciesAssessments(page, base, errors);
    await assertConditionsUnavailableContextAndSolarRollover(page, base, errors);

    await openPage(page, `${base}/forecast-revisions`, errors);
    await assertShell(page, "Operations and product health", "Forecast revisions");
    await page.waitForFunction(() =>
      document.querySelectorAll("select").length === 2
        && document.querySelectorAll(".revision-measurement-option").length === 4
    );
    await assertForecastRevisions(page);
    await assertScrollableTables(page, "Forecast revisions");
    await assertHealthy(page, errors, "Forecast revisions");
    await assertForecastRevisionLongHistory(page, base, errors);
    await assertForecastRevisionSparseStates(page, base, errors);

    await openPage(page, `${base}/pipeline-monitoring`, errors);
    await assertShell(page, "Operations and product health", "Pipeline monitoring");
    await page.waitForFunction(() => document.querySelectorAll("select").length === 1);
    await assertPipelineMonitoring(page);
    await assertObservationHealthStates(page, base, errors);
    await assertScrollableTables(page, "Pipeline monitoring");
    await assertHealthy(page, errors, "Pipeline monitoring");

    await openPage(page, `${base}/data-provenance`, errors);
    await assertShell(page, "Operations and product health", "Forecast sources");
    await page.waitForFunction(() => document.querySelectorAll("select").length === 1);
    await assertDataProvenance(page);
    await assertHealthy(page, errors, "Forecast sources");
    await assertPressureOperationsCoverage();

    await assertThemeBehavior(page, base, errors);

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
