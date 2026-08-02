---
title: Forecast revisions
---

```js
import * as Inputs from "@observablehq/inputs";
import * as Plot from "@observablehq/plot";
import {html} from "htl";

import {
  asDate,
  formatNumber,
  formatTimestamp,
  locationName
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const history = await FileAttachment("./data/forecast-history.json").json();
const rows = history.map((row) => ({
  ...row,
  runDate: asDate(row.run_started_at),
  validDate: asDate(row.forecast_time)
}));
const metrics = [
  {field: "wind_speed_10m", label: "Wind speed", unit: "km/h", digits: 1},
  {field: "wave_height", label: "Wave height", unit: "m", digits: 1},
  {field: "sea_surface_temperature", label: "Sea surface temperature", unit: "°C", digits: 1},
  {field: "tide_predicted_range", label: "Predicted tide range", unit: "m", digits: 2}
];

const locationId = view(Inputs.select(
  locations.map((location) => location.location_id),
  {
    label: "Location",
    format: (value) => locationName(value, locations),
    value: locations[0].location_id
  }
));
const locationRows = rows.filter((row) => row.location_id === locationId);
const validTimes = [...new Set(locationRows.map((row) => row.forecast_time))].sort();
const validTime = view(Inputs.select(validTimes, {
  label: "Forecast valid time",
  format: (value) => formatTimestamp(value, manifest.display_timezone),
  value: validTimes[0]
}));
const metricField = view(Inputs.select(metrics.map((metric) => metric.field), {
  label: "Metric",
  format: (value) => metrics.find((metric) => metric.field === value)?.label ?? value,
  value: metrics[0].field
}));
const metric = metrics.find((item) => item.field === metricField);
const selectedRows = locationRows
  .filter((row) => row.forecast_time === validTime)
  .sort((left, right) => left.runDate - right.runDate);
const chartRows = selectedRows
  .filter((row) => row[metricField] !== null && row[metricField] !== undefined)
  .map((row) => ({...row, metricValue: row[metricField]}));
```

# Forecast revisions

A forecast vintage is identified by its pipeline run start time. The selected
forecast valid time is a separate timestamp. This page never treats those two
times as interchangeable.

<div class="detail-grid">
  <div class="detail-card">
    <div class="detail-label">Location</div>
    <div class="detail-value">${locationName(locationId, locations)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Forecast valid time</div>
    <div class="detail-value">${formatTimestamp(validTime, manifest.display_timezone)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Persisted vintages</div>
    <div class="detail-value">${selectedRows.length}</div>
  </div>
</div>

```js
if (chartRows.length < 2) {
  display(html`<div class="notice">
    <strong>Insufficient history</strong>
    Fewer than two persisted, non-null vintages are available for this metric,
    location, and valid hour.
  </div>`);
} else {
  display(Plot.plot({
    height: 340,
    x: {type: "utc", label: "Pipeline run started"},
    y: {grid: true, label: `${metric.label} (${metric.unit})`},
    marks: [
      Plot.lineY(chartRows, {
        x: "runDate",
        y: "metricValue",
        marker: true,
        tip: true
      })
    ]
  }));
}
```

## Persisted values

```js
Inputs.table(
  selectedRows.map((row) => ({
    run_id: row.run_id,
    run_started: formatTimestamp(row.run_started_at, manifest.display_timezone),
    forecast_valid: formatTimestamp(row.forecast_time, manifest.display_timezone),
    value: formatNumber(row[metricField], metric.digits, metric.unit)
  })),
  {
    columns: ["run_id", "run_started", "forecast_valid", "value"],
    header: {
      run_id: "Run ID",
      run_started: "Run started",
      forecast_valid: "Forecast valid",
      value: metric.label
    },
    rows: 10,
    select: false
  }
)
```
