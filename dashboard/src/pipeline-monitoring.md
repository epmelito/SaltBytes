---
title: Pipeline monitoring
---

```js
import * as Inputs from "@observablehq/inputs";
import * as Plot from "@observablehq/plot";
import {html} from "npm:htl";

import {
  asDate,
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
const runRows = runs.map((run) => ({
  ...run,
  startedDate: asDate(run.started_at),
  statusLabel: run.partial_data ? `${statusLabel(run.status)} · partial data` : statusLabel(run.status)
}));
const successfulRuns = runs.filter((run) => run.status === "success").length;
const failedRuns = runs.filter((run) => run.status === "failed").length;
const partialRuns = runs.filter((run) => run.partial_data).length;
const coverageRunIds = [...new Set(sourceHealth.coverage.map((row) => row.run_id))];
```

```js
const coverageRunId = view(Inputs.select(coverageRunIds, {
  label: "Source coverage run",
  format: (value) => {
    const run = runs.find((item) => item.run_id === value);
    return `${value} · ${formatTimestamp(run?.started_at, manifest.display_timezone)}`;
  },
  value: coverageRunIds[0]
}));
```

```js
const coverageRows = sourceHealth.coverage.filter((row) => row.run_id === coverageRunId);
```

# Pipeline monitoring

Recent run history remains visible even when ingestion fails or produces partial
data. Source failures show public-safe status metadata only; raw exception detail
is deliberately excluded from the published dataset.

<div class="metric-grid">
  <div class="metric-card">
    <div class="metric-label">Displayed runs</div>
    <div class="metric-value">${runs.length}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Successful</div>
    <div class="metric-value">${successfulRuns}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Failed</div>
    <div class="metric-value">${failedRuns}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Failed with partial data</div>
    <div class="metric-value">${partialRuns}</div>
  </div>
</div>

<div class="chart-grid">
  <div class="chart-card">

## Run status timeline

```js
Plot.plot({
  height: 250,
  x: {type: "utc", label: "Pipeline run started"},
  y: {label: null},
  color: {legend: true},
  marks: [
    Plot.dot(runRows, {
      x: "startedDate",
      y: () => "run",
      fill: "statusLabel",
      r: 8,
      tip: true
    })
  ]
})
```

  </div>
  <div class="chart-card">

## Run duration

```js
Plot.plot({
  height: 250,
  x: {type: "utc", label: "Pipeline run started"},
  y: {grid: true, label: "seconds"},
  marks: [
    Plot.lineY(runRows, {
      x: "startedDate",
      y: "duration_seconds",
      marker: true,
      tip: true
    }),
    Plot.ruleY([0])
  ]
})
```

  </div>
  <div class="chart-card">

## Rows loaded

```js
Plot.plot({
  height: 250,
  x: {type: "utc", label: "Pipeline run started"},
  y: {grid: true, label: "rows"},
  marks: [
    Plot.lineY(runRows, {
      x: "startedDate",
      y: "rows_loaded",
      marker: true,
      tip: true
    }),
    Plot.ruleY([0])
  ]
})
```

  </div>
  <div class="chart-card">

## Snapshot counts

```js
Plot.plot({
  height: 250,
  x: {type: "utc", label: "Pipeline run started"},
  y: {grid: true, label: "snapshots"},
  marks: [
    Plot.lineY(runRows, {
      x: "startedDate",
      y: "snapshot_count",
      marker: true,
      tip: true
    }),
    Plot.ruleY([0])
  ]
})
```

  </div>
</div>

## Recent runs

```js
Inputs.table(
  runs.map((run) => ({
    run_id: run.run_id,
    started: formatTimestamp(run.started_at, manifest.display_timezone),
    completed: formatTimestamp(run.completed_at, manifest.display_timezone),
    status: `${statusLabel(run.status)}${run.partial_data ? " · partial" : ""}`,
    duration: formatNumber(run.duration_seconds, 0, "s"),
    rows_loaded: run.rows_loaded,
    snapshots: run.snapshot_count
  })),
  {
    columns: [
      "run_id",
      "started",
      "completed",
      "status",
      "duration",
      "rows_loaded",
      "snapshots"
    ],
    header: {
      run_id: "Run ID",
      started: "Started",
      completed: "Completed",
      status: "Status",
      duration: "Duration",
      rows_loaded: "Rows",
      snapshots: "Snapshots"
    },
    rows: 20,
    select: false
  }
)
```

## Source success rates

```js
Plot.plot({
  marginLeft: 155,
  height: 220,
  x: {domain: [0, 100], grid: true, label: "Success rate (%)"},
  y: {label: null},
  marks: [
    Plot.barX(sourceHealth.summary, {
      x: "success_rate_percent",
      y: (row) => sourceName(row.source),
      tip: true
    }),
    Plot.ruleX([0])
  ]
})
```

```js
Inputs.table(
  sourceHealth.summary.map((row) => ({
    source: sourceName(row.source),
    success: row.success_count,
    failed: row.failure_count,
    missing: row.missing_count,
    success_rate: formatNumber(row.success_rate_percent, 1, "%")
  })),
  {
    columns: ["source", "success", "failed", "missing", "success_rate"],
    header: {
      source: "Source",
      success: "Success",
      failed: "Failed",
      missing: "Missing",
      success_rate: "Success rate"
    },
    rows: 10,
    select: false
  }
)
```

## Run and location coverage

```js
Inputs.table(
  coverageRows.map((row) => ({
    location: locationName(row.location_id, locations),
    source: sourceName(row.source),
    status: statusLabel(row.status)
  })),
  {
    columns: ["location", "source", "status"],
    header: {location: "Location", source: "Source", status: "Status"},
    rows: 20,
    select: false
  }
)
```

## Recent source failures

```js
sourceHealth.failures.length === 0
  ? html`<div class="notice">No recent source failures.</div>`
  : Inputs.table(
      sourceHealth.failures.map((row) => ({
        run_id: row.run_id,
        location: locationName(row.location_id, locations),
        source: sourceName(row.source),
        status: statusLabel(row.status),
        recorded: formatTimestamp(row.recorded_at, manifest.display_timezone)
      })),
      {
        columns: ["run_id", "location", "source", "status", "recorded"],
        header: {
          run_id: "Run ID",
          location: "Location",
          source: "Source",
          status: "Status",
          recorded: "Recorded"
        },
        rows: 20,
        select: false
      }
    )
```
