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

async function run() {
  const {server, port} = await startServer();
  const browser = await chromium.launch({
    executablePath: browserPath(),
    headless: true,
    args: ["--no-sandbox"]
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(timeoutMs);
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const base = `http://127.0.0.1:${port}`;

  try {
    await openPage(page, `${base}/`, errors);

    await openPage(page, `${base}/conditions`, errors);
    await page.waitForFunction(() => document.querySelectorAll("select").length === 2);
    const initialConditions = await page.locator(".metric-card").first().innerText();
    if (!initialConditions || initialConditions.includes("Unavailable")) {
      throw new Error("Conditions did not initialize with data");
    }
    await page.waitForFunction(() => {
      const text = document.body.innerText;
      return text.toLowerCase().includes("conditions alignment score")
        && new RegExp("[0-9]+ / 100").test(text);
    });
    const initialScore = await page.locator("body").innerText();
    if (!initialScore.toLowerCase().includes("conditions alignment score") || !new RegExp("[0-9]+ / 100").test(initialScore)) {
      throw new Error("Conditions score did not initialize with an available result");
    }
    await selectOption(page, 0, 1, "Conditions location control");
    await page.waitForFunction(
      (before) => document.querySelector(".metric-card")?.innerText !== before,
      initialConditions
    );
    const locationConditions = await page.locator(".metric-card").first().innerText();
    await page.waitForFunction(() => document.querySelectorAll("select")[1]?.options.length > 1);
    const forecastOptions = await page.locator("select").nth(1).locator("option").count();
    await selectOption(page, 1, forecastOptions - 1, "Conditions forecast control");
    await page.waitForFunction(
      (before) => document.querySelector(".metric-card")?.innerText !== before,
      locationConditions
    );
    await page.waitForFunction(() => document.body.innerText.includes("Score unavailable"));
    await assertHealthy(page, errors, "Conditions");

    await openPage(page, `${base}/forecast-revisions`, errors);
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
