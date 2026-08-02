---
title: Overview
---

```js
import * as Plot from "@observablehq/plot";

import {
  asDate,
  formatMinutes,
  formatTimestamp,
  locationName,
  sourceName,
  statusLabel
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const conditions = await FileAttachment("./data/conditions.json").json();
const sourceHealth = await FileAttachment("./data/source-health.json").json();

const conditionsWithDates = conditions.map((row) => ({
  ...row,
  forecastDate: asDate(row.forecast_time),
  locationName: locationName(row.location_id, locations)
}));
const firstForecastTime = manifest.forecast_window.start;
const locationComparison = conditionsWithDates.filter(
  (row) => row.forecast_time === firstForecastTime
);
const forecastHours = new Set(conditions.map((row) => row.forecast_time)).size;
```

<div class="hero">
  <h1>SaltBytes coastal dashboard</h1>
  <p>
    A static view of upcoming atmospheric, wave, sea surface temperature, and
    tide conditions at five North Carolina fishing locations. The data is
    forecast and prediction output, not observed conditions or fishing advice.
  </p>
</div>

<div class="metric-grid">
  <div class="metric-card">
    <div class="metric-label">Latest successful run</div>
    <div class="metric-value">${manifest.latest_success.run_id}</div>
    <div>${formatTimestamp(manifest.latest_success.completed_at, manifest.display_timezone)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Data freshness</div>
    <div class="metric-value">${formatMinutes(manifest.latest_success_freshness_minutes)}</div>
    <div>at dashboard generation time</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Latest attempted run</div>
    <div class="metric-value">
      <span class="status">${statusLabel(manifest.latest_attempt.status)}</span>
    </div>
    <div>${manifest.latest_attempt.run_id}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Forecast coverage</div>
    <div class="metric-value">${forecastHours} hours</div>
    <div>${manifest.location_count} locations · ${manifest.source_count} sources</div>
  </div>
</div>

## Current source health

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

Success rates use the expected run, location, and source combinations from the
20 most recent runs. Missing source records stay separate from recorded failures.

## Location comparison

The comparison uses the first valid hour in the latest successful forecast window:
**${formatTimestamp(firstForecastTime, manifest.display_timezone)}**.

<div class="chart-grid">
  <div class="chart-card">

### Wind speed

```js
Plot.plot({
  height: 300,
  marginBottom: 100,
  x: {label: null, tickRotate: -35},
  y: {label: "km/h", grid: true},
  marks: [
    Plot.barY(locationComparison, {
      x: "locationName",
      y: "wind_speed_10m",
      tip: true
    }),
    Plot.ruleY([0])
  ]
})
```

  </div>
  <div class="chart-card">

### Wave height

```js
Plot.plot({
  height: 300,
  marginBottom: 100,
  x: {label: null, tickRotate: -35},
  y: {label: "metres", grid: true},
  marks: [
    Plot.barY(locationComparison, {
      x: "locationName",
      y: "wave_height",
      tip: true
    }),
    Plot.ruleY([0])
  ]
})
```

  </div>
</div>

## Forecast window

<div class="detail-grid">
  <div class="detail-card">
    <div class="detail-label">Starts</div>
    <div class="detail-value">${formatTimestamp(manifest.forecast_window.start, manifest.display_timezone)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Ends</div>
    <div class="detail-value">${formatTimestamp(manifest.forecast_window.end, manifest.display_timezone)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Generated</div>
    <div class="detail-value">${formatTimestamp(manifest.generated_at, manifest.display_timezone)}</div>
  </div>
</div>

## Deterministic audit reports

<div class="link-grid">
  <a class="report-link" rel="external" href="../conditions/">
    <strong>Conditions report</strong>
    <span>Fixed HTML rendering of the current forecast conditions.</span>
  </a>
  <a class="report-link" rel="external" href="../operations/">
    <strong>Operations report</strong>
    <span>Fixed HTML rendering of pipeline health, revisions, and provenance.</span>
  </a>
</div>

<p class="page-note">
  Missing values remain unavailable throughout the dashboard. They are never
  converted to zero.
</p>
