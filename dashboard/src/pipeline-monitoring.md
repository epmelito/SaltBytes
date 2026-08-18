---
title: Pipeline monitoring
---

```js
import * as Inputs from "@observablehq/inputs";
import * as Plot from "@observablehq/plot";
import {html} from "npm:htl";

import {
  asDate,
  formatMinutes,
  formatNumber,
  formatTimestamp,
  locationName,
  sourceName,
  statusLabel
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const runs = await FileAttachment("./data/pipeline-runs.json").json();
const sourceHealth = await FileAttachment("./data/source-health.json").json();
const observationHealth = await FileAttachment("./data/observation-health.json").json();

const sourceOrder = ["weather", "pressure", "wave", "sst", "tide"];
const sourceLabel = sourceName;
const titleCase = (value) => {
  const label = statusLabel(value);
  return label === "Unavailable" ? label : `${label[0].toUpperCase()}${label.slice(1)}`;
};
const shortRunId = (value) => {
  if (!value) return "Unavailable";
  const text = String(value);
  return text.length <= 16 ? text : `${text.slice(0, 6)}…${text.slice(-6)}`;
};
const runOutcome = (run) => {
  if (!run) return {key: "unknown", label: "Unknown"};
  if (run.partial_data) return {key: "partial", label: "Partial data"};
  if (run.status === "success") return {key: "healthy", label: "Healthy"};
  if (run.status === "failed") return {key: "failed", label: "Failed"};
  return {key: "unknown", label: titleCase(run.status)};
};
const statusMeaning = (status) => ({
  success: "Available",
  fetch_failed: "Fetch failed",
  validation_failed: "Validation failed",
  persistence_failed: "Persistence failed",
  not_applicable: "Not applicable",
  not_recorded: "Not recorded"
}[status] ?? titleCase(status));
const statusKey = (status) => status === "success" || status === "not_applicable"
  ? "healthy"
  : status === "not_recorded" ? "missing" : "failed";
const runTimeLabel = new Intl.DateTimeFormat("en-US", {
  timeZone: manifest.display_timezone,
  month: "short",
  day: "numeric",
  hour: "numeric"
});
const sortedRuns = [...runs].sort((left, right) =>
  (asDate(right.started_at)?.getTime() ?? 0) - (asDate(left.started_at)?.getTime() ?? 0)
);
const latestRunId = manifest.latest_attempt?.run_id ?? sortedRuns[0]?.run_id;
const latestRun = sortedRuns.find((run) => run.run_id === latestRunId) ?? sortedRuns[0] ?? null;
const latestCoverageRows = sourceHealth.coverage.filter((row) => row.run_id === latestRun?.run_id);
const latestCoverageExceptions = latestCoverageRows.filter((row) =>
  row.status !== "success" && row.status !== "not_applicable"
);
const latestFailureRows = sourceHealth.failures.filter((row) => row.run_id === latestRun?.run_id);
const latestMissingRows = latestCoverageExceptions.filter((row) => row.status === "not_recorded");
const recentSuccessfulRuns = sortedRuns.filter((run) => run.status === "success" && !run.partial_data);
const successRatioText = sortedRuns.length
  ? `${recentSuccessfulRuns.length} of ${sortedRuns.length} recent runs completed successfully`
  : "No recent runs are available";
const latestCompleteAge = manifest.latest_success_freshness_minutes === null
  || manifest.latest_success_freshness_minutes === undefined
  ? "The age of the latest complete update is unavailable."
  : `The latest complete update was ${formatMinutes(manifest.latest_success_freshness_minutes)} old when this report was generated.`;
const healthState = !latestRun
  ? "unknown"
  : latestRun.status === "failed" && !latestRun.partial_data
    ? "failed"
    : latestRun.partial_data || latestCoverageExceptions.length
      ? "degraded"
      : latestRun.status === "success"
        ? "healthy"
        : "unknown";
const healthPresentation = {
  healthy: {
    label: "Healthy",
    summary: "The latest published update completed and all expected source checks are available."
  },
  degraded: {
    label: "Degraded",
    summary: latestRun?.partial_data
      ? "The latest published update did not complete, but partial forecast data remains available."
      : "The latest published update completed with one or more source checks needing attention."
  },
  failed: {
    label: "Failed",
    summary: "The latest published update failed and did not retain partial forecast data."
  },
  unknown: {
    label: "Unknown",
    summary: "No completed run evidence is available to determine published pipeline health."
  }
}[healthState];
const coverageRunIds = [...new Set(sourceHealth.coverage.map((row) => row.run_id))]
  .sort((left, right) => {
    const leftRun = sortedRuns.find((run) => run.run_id === left);
    const rightRun = sortedRuns.find((run) => run.run_id === right);
    return (asDate(rightRun?.started_at)?.getTime() ?? 0) - (asDate(leftRun?.started_at)?.getTime() ?? 0);
  });
const durations = recentSuccessfulRuns
  .map((run) => Number(run.duration_seconds))
  .filter(Number.isFinite)
  .sort((left, right) => left - right);
const medianDuration = durations.length
  ? durations.length % 2
    ? durations[Math.floor(durations.length / 2)]
    : (durations[durations.length / 2 - 1] + durations[durations.length / 2]) / 2
  : null;
const durationBaselineAvailable = durations.length >= 5;
const durationMaximum = Math.max(
  ...sortedRuns.map((run) => Number(run.duration_seconds)).filter(Number.isFinite),
  medianDuration ?? 0,
  1
) * 1.18;
const runRows = [...sortedRuns].reverse().map((run) => {
  const outcome = runOutcome(run);
  const duration = Number(run.duration_seconds);
  return {
    ...run,
    startedDate: asDate(run.started_at),
    chartLabel: runTimeLabel.format(asDate(run.started_at)),
    outcomeKey: outcome.key,
    outcomeLabel: outcome.label,
    fill: `var(--pipeline-${outcome.key})`,
    duration_seconds: Number.isFinite(duration) ? duration : null,
    durationAnomaly: durationBaselineAvailable
      && Number.isFinite(duration)
      && duration > medianDuration * 1.5,
    latest: run.run_id === latestRun?.run_id
  };
});
const recentRuns = sortedRuns.slice(0, 10);
const pressureRunIds = new Set(sourceHealth.coverage
  .filter((row) => row.source === "pressure")
  .map((row) => row.run_id));
```

# Pipeline monitoring

Pipeline health and recent reliability captured when this dashboard was last
published. Public output includes safe status evidence, not raw exception details.

```js
display(html`<section class="pipeline-health pipeline-health-${healthState}" data-health-state=${healthState}>
  <p class="pipeline-eyebrow">Published pipeline health</p>
  <h2>${healthPresentation.label}</h2>
  <p class="pipeline-health-summary">${healthPresentation.summary}</p>
  <div class="pipeline-health-facts">
    <div>
      <span class="detail-label">Latest attempt</span>
      <strong>${latestRun
        ? `${runOutcome(latestRun).label} · ${formatTimestamp(latestRun.started_at, manifest.display_timezone)}`
        : "Unavailable"}</strong>
    </div>
    <div>
      <span class="detail-label">Complete data freshness</span>
      <strong>${latestCompleteAge}</strong>
    </div>
    <div>
      <span class="detail-label">Affected scope</span>
      <strong>${latestCoverageExceptions.length
        ? `${latestCoverageExceptions.length} of ${latestCoverageRows.length} source checks`
        : "No current source exceptions"}</strong>
    </div>
    <div>
      <span class="detail-label">Recent reliability</span>
      <strong>${successRatioText}</strong>
    </div>
  </div>
</section>`);
```

## Active failures and missing data

```js
display(latestCoverageExceptions.length
  ? html`<section class="pipeline-exceptions" aria-label="Active source exceptions">
      <p class="page-note">These exceptions belong to the latest attempt. Successful checks are omitted.</p>
      <div class="pipeline-exception-list">
        ${latestCoverageExceptions.map((row) => html`<article class="pipeline-exception">
          <div>
            <span class="pipeline-exception-status">${statusMeaning(row.status)}</span>
            <h3>${locationName(row.location_id, locations)}</h3>
          </div>
          <p><strong>${sourceLabel(row.source)}</strong> needs attention.</p>
        </article>`)}
      </div>
      ${latestMissingRows.length
        ? html`<p class="pipeline-exception-note">${latestFailureRows.length} recorded failures and ${latestMissingRows.length} missing source records are represented above.</p>`
        : null}
    </section>`
  : html`<div class="notice pipeline-healthy-notice"><strong>No active source failures.</strong>
      All expected source checks succeeded for the latest attempt.</div>`);
```

## Fishing observation review

```js
const observationAttempt = observationHealth.latest_attempt;
const observationAttempts = observationHealth.latest_attempts ?? (observationAttempt ? [observationAttempt] : []);
const configuredObservationSources = ["jennettes_pier", "sunset_beach_pier"];
const observationStatuses = new Map(observationAttempts.map((attempt) => [attempt.source, attempt.status]));
const observationSummary = observationAttempts.length === 0
  ? {state: "not-run", message: "Fishing observation update has not run yet."}
  : observationAttempts.every((attempt) => attempt.status === "failed")
  ? {state: "failed", message: "Latest fishing observation update failed. Earlier observations remain available."}
  : configuredObservationSources.every((source) => observationStatuses.get(source) === "success")
  ? {state: "completed", message: "Latest fishing observation update completed."}
  : {state: "attention", message: "Latest fishing observation update needs attention. One or more report sources did not complete."};
const outstandingPatterns = observationHealth.outstanding_patterns;
display(html`<section class="pipeline-coverage">
  <div class="observation-review-summary" data-observation-state=${observationSummary.state}>
    <strong>${observationSummary.message}</strong>
    <span>${formatTimestamp(observationAttempt?.attempted_at, manifest.display_timezone)}</span>
  </div>
  ${observationAttempts.length ? html`<div class="table-scroll"><table><thead><tr><th>Report source</th><th>Latest update</th><th>Status</th><th>New patterns</th><th>Outstanding patterns</th></tr></thead><tbody>${observationAttempts.map((attempt) => html`<tr><td>${locationName(attempt.source, locations)}</td><td>${formatTimestamp(attempt.attempted_at, manifest.display_timezone)}</td><td>${titleCase(attempt.status)}</td><td>${formatNumber(attempt.new_review_patterns, 0)}</td><td>${formatNumber(attempt.outstanding_review_patterns, 0)}</td></tr>`)}</tbody></table></div>` : null}
  ${outstandingPatterns.length ? html`<div class="table-scroll"><table><thead><tr><th>Report source</th><th>Pattern ID</th><th>Candidate wording</th><th>Reason</th><th>Occurrences</th><th>Report version</th></tr></thead><tbody>${outstandingPatterns.map((pattern) => html`<tr><td>${locationName(pattern.source, locations)}</td><td><code>${pattern.pattern_id}</code></td><td>${pattern.raw_segment}</td><td>${pattern.reason}</td><td>${formatNumber(pattern.occurrence_count, 0)}</td><td><code>${pattern.report_id}</code>${pattern.report_time_text ? ` · ${pattern.report_time_text}` : ""}</td></tr>`)}</tbody></table></div>` : html`<p class="page-note">No outstanding fishing observation review patterns.</p>`}
</section>`);
```

## Recent reliability

One view combines run outcome and duration. Bar color shows whether each run was
healthy, partial, or failed.

<div class="pipeline-reliability">

```js
resize((width) => Plot.plot({
  width,
  height: 300,
  marginTop: 32,
  marginBottom: 58,
  x: {
    label: null,
    tickRotate: -25,
    padding: 0.28
  },
  y: {
    grid: true,
    label: "Duration (seconds)",
    domain: [0, durationMaximum]
  },
  color: {type: "identity"},
  marks: [
    Plot.barY(runRows, {
      x: "chartLabel",
      y: "duration_seconds",
      fill: "fill",
      inset: 2,
      title: (row) => [
        `Run: ${row.run_id}`,
        `Started: ${formatTimestamp(row.started_at, manifest.display_timezone)}`,
        `Outcome: ${row.outcomeLabel}`,
        `Duration: ${formatNumber(row.duration_seconds, 0, "s")}`,
        `Rows: ${formatNumber(row.rows_loaded, 0)}`,
        `Snapshots: ${formatNumber(row.snapshot_count, 0)}`,
        row.durationAnomaly ? "Duration: unusually long" : null
      ].filter(Boolean).join("\n"),
      tip: true
    }),
    medianDuration === null ? null : Plot.ruleY([medianDuration], {
      stroke: "var(--saltbytes-muted)",
      strokeDasharray: "5,4"
    }),
    Plot.text(runRows.filter((row) => row.latest), {
      x: "chartLabel",
      y: "duration_seconds",
      text: () => "Latest",
      dy: -12,
      fontWeight: 700
    }),
    Plot.ruleY([0])
  ].filter(Boolean)
}))
```

<div class="pipeline-chart-footer">
  <div class="pipeline-legend" aria-label="Run outcome legend">
    <span class="pipeline-legend-healthy">Healthy</span>
    <span class="pipeline-legend-partial">Partial data</span>
    <span class="pipeline-legend-failed">Failed</span>
  </div>
  <p>${medianDuration === null
    ? "A recent successful-run duration baseline is unavailable."
    : `Recent successful-run median: ${formatNumber(medianDuration, 0, "s")}. ${
      durationBaselineAvailable
        ? "Runs above 1.5 times this median are identified in their tooltip."
        : "At least five successful runs are required before labeling duration anomalies."
    }`}</p>
</div>

</div>

## Source and location health

The selected run defaults to the latest attempt. Successful checks stay quiet so
failures and missing records remain easy to scan.

```js
const coverageRunId = view(Inputs.select(coverageRunIds, {
  label: "Coverage run",
  format: (value) => {
    const run = sortedRuns.find((item) => item.run_id === value);
    return `${shortRunId(value)} · ${formatTimestamp(run?.started_at, manifest.display_timezone)}`;
  },
  value: latestRun?.run_id && coverageRunIds.includes(latestRun.run_id)
    ? latestRun.run_id
    : coverageRunIds[0]
}));
```

```js
const coverageRows = sourceHealth.coverage.filter((row) => row.run_id === coverageRunId);
const coverageRun = sortedRuns.find((run) => run.run_id === coverageRunId);
const coverageMatrix = locations.map((location) => ({
  location,
  cells: sourceOrder.map((source) => {
    const row = coverageRows.find((item) =>
      item.location_id === location.location_id && item.source === source
    );
    const applicable = source !== "pressure" || pressureRunIds.has(coverageRunId);
    const status = row?.status ?? (applicable ? "not_recorded" : "not_applicable");
    return {source, status, label: statusMeaning(status), key: statusKey(status)};
  })
}));
const coverageExceptions = coverageMatrix.flatMap((row) =>
  row.cells
    .filter((cell) => cell.status !== "success" && cell.status !== "not_applicable")
    .map((cell) => ({location: row.location, ...cell}))
);
const coverageCheckCount = coverageMatrix
  .flatMap((row) => row.cells)
  .filter((cell) => cell.status !== "not_applicable").length;
const coverageSummary = coverageExceptions.length
  ? `${coverageExceptions.length} of ${coverageCheckCount} source checks need attention.`
  : `All ${coverageCheckCount} source checks succeeded.`;
```

```js
display(html`<section class="pipeline-coverage" aria-live="polite">
  <div class="pipeline-section-summary">
    <strong>${coverageSummary}</strong>
    <span>${formatTimestamp(coverageRun?.started_at, manifest.display_timezone)}</span>
  </div>
  <div class="table-scroll pipeline-matrix-scroll">
    <table class="pipeline-matrix">
      <thead>
        <tr>
          <th scope="col">Location</th>
          ${sourceOrder.map((source) => html`<th scope="col">${sourceLabel(source)}</th>`)}
        </tr>
      </thead>
      <tbody>
        ${coverageMatrix.map((row) => html`<tr>
          <th scope="row">${row.location.name}</th>
          ${row.cells.map((cell) => html`<td class=${`coverage-cell coverage-${cell.key}`}>
            <span title=${`${row.location.name} · ${sourceLabel(cell.source)} · ${cell.label}`}>${cell.label}</span>
          </td>`)}
        </tr>`)}
      </tbody>
    </table>
  </div>
</section>`);
```

## Latest runs

<p class="pipeline-section-note">Recent runs are shown here. Full run IDs and complete records are available below.</p>

```js
display(html`<div class="table-scroll pipeline-runs-scroll">
  <table class="pipeline-runs-table">
    <thead>
      <tr>
        <th scope="col">Run</th>
        <th scope="col">Started</th>
        <th scope="col">Outcome</th>
        <th scope="col">Duration</th>
      </tr>
    </thead>
    <tbody>
      ${recentRuns.map((run) => html`<tr>
        <td><code title=${run.run_id}>${shortRunId(run.run_id)}</code></td>
        <td>${formatTimestamp(run.started_at, manifest.display_timezone)}</td>
        <td><span class=${`run-status run-status-${runOutcome(run).key}`}>${runOutcome(run).label}</span></td>
        <td>${formatNumber(run.duration_seconds, 0, "s")}</td>
      </tr>`)}
    </tbody>
  </table>
</div>`);
```

<details class="pipeline-details">
<summary>Detailed run evidence</summary>

<p class="pipeline-section-note">Complete records are available here when more detail is needed.</p>

### Complete run records

```js
display(html`<div class="table-scroll">
  <table>
    <thead>
      <tr>
        <th scope="col">Full run ID</th>
        <th scope="col">Started</th>
        <th scope="col">Completed</th>
        <th scope="col">Status</th>
        <th scope="col">Duration</th>
        <th scope="col">Rows</th>
        <th scope="col">Snapshots</th>
      </tr>
    </thead>
    <tbody>
      ${sortedRuns.map((run) => html`<tr>
        <td><code>${run.run_id}</code></td>
        <td>${formatTimestamp(run.started_at, manifest.display_timezone)}</td>
        <td>${formatTimestamp(run.completed_at, manifest.display_timezone)}</td>
        <td>${runOutcome(run).label}</td>
        <td>${formatNumber(run.duration_seconds, 0, "s")}</td>
        <td>${formatNumber(run.rows_loaded, 0)}</td>
        <td>${formatNumber(run.snapshot_count, 0)}</td>
      </tr>`)}
    </tbody>
  </table>
</div>`);
```

### Recent source summary

```js
display(html`<div class="table-scroll">
  <table>
    <thead>
      <tr>
        <th scope="col">Source</th>
        <th scope="col">Successful</th>
        <th scope="col">Failed</th>
        <th scope="col">Missing</th>
        <th scope="col">Success rate</th>
      </tr>
    </thead>
    <tbody>
      ${sourceHealth.summary.map((row) => html`<tr>
        <th scope="row">${sourceLabel(row.source)}</th>
        <td>${formatNumber(row.success_count, 0)}</td>
        <td>${formatNumber(row.failure_count, 0)}</td>
        <td>${formatNumber(row.missing_count, 0)}</td>
        <td>${formatNumber(row.success_rate_percent, 1, "%")}</td>
      </tr>`)}
    </tbody>
  </table>
</div>`);
```

<p class="page-note">The public dashboard shows source status labels without raw error details.</p>

</details>
