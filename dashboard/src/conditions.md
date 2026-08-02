---
title: Conditions
---

```js
import * as Inputs from "@observablehq/inputs";
import * as Plot from "@observablehq/plot";

import {
  asDate,
  compassDirection,
  formatNumber,
  formatTimestamp,
  locationName,
  statusLabel
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const conditions = await FileAttachment("./data/conditions.json").json();
const rows = conditions.map((row) => ({...row, forecastDate: asDate(row.forecast_time)}));

const locationId = view(Inputs.select(
  locations.map((location) => location.location_id),
  {
    label: "Location",
    format: (value) => locationName(value, locations),
    value: locations[0].location_id
  }
));
const locationRows = rows.filter((row) => row.location_id === locationId);
const forecastTime = view(Inputs.select(
  locationRows.map((row) => row.forecast_time),
  {
    label: "Forecast valid time",
    format: (value) => formatTimestamp(value, manifest.display_timezone),
    value: locationRows[0]?.forecast_time
  }
));
const selected = locationRows.find((row) => row.forecast_time === forecastTime);
const windSeries = locationRows.flatMap((row) => [
  {forecastDate: row.forecastDate, metric: "Wind", value: row.wind_speed_10m},
  {forecastDate: row.forecastDate, metric: "Gust", value: row.wind_gusts_10m}
]);
const directionSeries = locationRows.flatMap((row) => [
  {forecastDate: row.forecastDate, metric: "Wind", value: row.wind_to_shore_angle_degrees},
  {forecastDate: row.forecastDate, metric: "Wave", value: row.wave_to_shore_angle_degrees}
]);
```

# Conditions

Select a location and valid forecast hour. Charts show the complete exported
window for the selected location. Null values remain visible as gaps or
**Unavailable**.

<div class="metric-grid">
  <div class="metric-card">
    <div class="metric-label">Wind</div>
    <div class="metric-value">${formatNumber(selected?.wind_speed_10m, 1, "km/h")}</div>
    <div>${formatNumber(selected?.wind_direction_10m, 0, "degrees")} ${compassDirection(selected?.wind_direction_10m)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Wind gust</div>
    <div class="metric-value">${formatNumber(selected?.wind_gusts_10m, 1, "km/h")}</div>
    <div>to shore: ${formatNumber(selected?.wind_to_shore_angle_degrees, 0, "degrees")}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Wave</div>
    <div class="metric-value">${formatNumber(selected?.wave_height, 1, "m")}</div>
    <div>${formatNumber(selected?.wave_period, 1, "s")} · ${compassDirection(selected?.wave_direction)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Sea surface temperature</div>
    <div class="metric-value">${formatNumber(selected?.sea_surface_temperature, 1, "°C")}</div>
    <div><span class="status">${statusLabel(selected?.sst_status)}</span></div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Tide phase</div>
    <div class="metric-value">${selected?.tide_phase ?? "Unavailable"}</div>
    <div>range: ${formatNumber(selected?.tide_predicted_range, 2, "m")}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Precipitation</div>
    <div class="metric-value">${formatNumber(selected?.precipitation_probability, 0, "%")}</div>
    <div>${formatNumber(selected?.precipitation, 1, "mm")}</div>
  </div>
</div>

<div class="chart-grid">
  <div class="chart-card">

## Wind and gust

```js
Plot.plot({
  height: 300,
  x: {type: "utc", label: "Forecast valid time"},
  y: {grid: true, label: "km/h"},
  color: {legend: true},
  marks: [
    Plot.lineY(windSeries, {
      x: "forecastDate",
      y: "value",
      stroke: "metric",
      marker: true,
      tip: true
    }),
    Plot.ruleY([0])
  ]
})
```

  </div>
  <div class="chart-card">

## Wave height

```js
Plot.plot({
  height: 300,
  x: {type: "utc", label: "Forecast valid time"},
  y: {grid: true, label: "metres"},
  marks: [
    Plot.lineY(locationRows, {
      x: "forecastDate",
      y: "wave_height",
      marker: true,
      tip: true
    }),
    Plot.ruleY([0])
  ]
})
```

  </div>
  <div class="chart-card">

## Sea surface temperature

```js
Plot.plot({
  height: 300,
  x: {type: "utc", label: "Forecast valid time"},
  y: {grid: true, label: "°C"},
  marks: [
    Plot.lineY(locationRows, {
      x: "forecastDate",
      y: "sea_surface_temperature",
      marker: true,
      tip: true
    })
  ]
})
```

  </div>
  <div class="chart-card">

## Direction relative to shore

```js
Plot.plot({
  height: 300,
  x: {type: "utc", label: "Forecast valid time"},
  y: {domain: [-180, 180], grid: true, label: "degrees from seaward shore normal"},
  color: {legend: true},
  marks: [
    Plot.lineY(directionSeries, {
      x: "forecastDate",
      y: "value",
      stroke: "metric",
      marker: true,
      tip: true
    }),
    Plot.ruleY([-90, 0, 90])
  ]
})
```

  </div>
</div>

## Tide context at the selected hour

<div class="detail-grid">
  <div class="detail-card">
    <div class="detail-label">Previous extremum</div>
    <div class="detail-value">${selected?.tide_previous_extremum_type ?? "Unavailable"}</div>
    <div>${formatTimestamp(selected?.tide_previous_extremum_time, manifest.display_timezone)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Next extremum</div>
    <div class="detail-value">${selected?.tide_next_extremum_type ?? "Unavailable"}</div>
    <div>${formatTimestamp(selected?.tide_next_extremum_time, manifest.display_timezone)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Source status</div>
    <div class="detail-value"><span class="status">${statusLabel(selected?.tide_status)}</span></div>
  </div>
</div>
