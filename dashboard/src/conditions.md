---
title: Conditions
---

```js
import * as Inputs from "@observablehq/inputs";
import * as Plot from "@observablehq/plot";
import {html} from "npm:htl";

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
```

```js
const locationId = view(Inputs.select(
  locations.map((location) => location.location_id),
  {
    label: "Location",
    format: (value) => locationName(value, locations),
    value: locations[0].location_id
  }
));
```

```js
const locationRows = rows.filter((row) => row.location_id === locationId);
const forecastTime = view(Inputs.select(
  locationRows.map((row) => row.forecast_time),
  {
    label: "Forecast valid time",
    format: (value) => formatTimestamp(value, manifest.display_timezone),
    value: locationRows[0]?.forecast_time
  }
));
```

```js
const selected = locationRows.find((row) => row.forecast_time === forecastTime);
const spanishMackerel = selected?.spanish_mackerel_conditions;
const scoreIsAvailable = spanishMackerel?.state === "available";
const scoreBandLabels = {
  very_limited_alignment: "Very limited alignment",
  limited_alignment: "Limited alignment",
  mixed_conditions: "Mixed conditions",
  favorable_alignment: "Favorable alignment",
  strong_alignment: "Strong alignment"
};
const factorLabels = {
  seasonal_alignment: "Seasonal timing",
  thermal_context: "Sea temperature context",
  wind_fishability: "Wind conditions",
  wave_fishability: "Wave conditions",
  local_baitfish_presence: "Local baitfish presence",
  current_spanish_mackerel_presence: "Current Spanish mackerel presence",
  schools_within_casting_range: "Schools within casting range",
  nearshore_sst_accuracy_and_site_representativeness:
    "Nearshore temperature accuracy and local representativeness"
};
const confidenceLabels = {
  species_identity_confidence: "Species identification",
  location_applicability_confidence: "Location applicability",
  environmental_source_confidence: "Environmental source data",
  seasonal_evidence_confidence: "Seasonal evidence",
  habitat_data_confidence: "Habitat data",
  biological_observation_confidence: "Biological observations",
  fishability_data_confidence: "Fishability data",
  overall_interpretation_confidence: "Interpretation confidence"
};
const confidenceState = (value) => value ? `${value[0].toUpperCase()}${value.slice(1)}` : "Unavailable";
const factorText = (factors) => factors?.map((factor) => factorLabels[factor] ?? factor).join(", ") || "None";
const overallConfidence = spanishMackerel?.confidence?.find(
  (item) => item.identifier === "overall_interpretation_confidence"
);
const confidenceDetails = spanishMackerel?.confidence
  ?.filter((item) => item.identifier !== "overall_interpretation_confidence")
  .map((item) => `${confidenceLabels[item.identifier] ?? item.identifier}: ${confidenceState(item.state)}`)
  .join(" · ");
const unavailableMessageGroups = [
  {
    reasons: ["location_not_applicable"],
    message: "This score is not available for this location and fishing context."
  },
  {
    reasons: [
      "forecast_time_invalid",
      "display_timezone_missing",
      "display_timezone_invalid",
      "local_forecast_date_unavailable"
    ],
    message: "Required forecast timing information is unavailable."
  },
  {
    reasons: [
      "weather_source_missing",
      "weather_source_not_success",
      "wind_speed_10m_missing",
      "wind_speed_10m_invalid",
      "wind_gusts_10m_missing",
      "wind_gusts_10m_invalid"
    ],
    message: "Required wind forecast data is unavailable."
  },
  {
    reasons: [
      "wave_source_missing",
      "wave_source_not_success",
      "wave_height_missing",
      "wave_height_invalid"
    ],
    message: "Required wave forecast data is unavailable."
  },
  {
    reasons: [
      "sst_source_missing",
      "sst_source_not_success",
      "sea_surface_temperature_missing",
      "sea_surface_temperature_invalid"
    ],
    message: "Required sea surface temperature data is unavailable."
  }
];
const unavailableMessages = unavailableMessageGroups
  .filter((group) => spanishMackerel?.unavailable_reasons?.some(
    (reason) => group.reasons.includes(reason)
  ))
  .map((group) => group.message);
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

## Spanish mackerel conditions

```js
display(scoreIsAvailable ? html`<section>
  <div class="metric-grid">
    <div class="metric-card">
      <div class="metric-label">Conditions alignment score</div>
      <div class="metric-value">${spanishMackerel.score} / 100</div>
      <div>${scoreBandLabels[spanishMackerel.score_band]}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Interpretation confidence</div>
      <div class="metric-value">Interpretation confidence: ${confidenceState(overallConfidence?.state)}</div>
      <div>${confidenceDetails}</div>
    </div>
  </div>
  <div class="detail-grid">
    <div class="detail-card">
      <div class="detail-label">Supporting conditions</div>
      <div>${factorText(spanishMackerel.positive_factors)}</div>
    </div>
    <div class="detail-card">
      <div class="detail-label">Limiting conditions</div>
      <div>${factorText(spanishMackerel.limiting_factors)}</div>
    </div>
    <div class="detail-card">
      <div class="detail-label">Important unknowns</div>
      <div>${factorText(spanishMackerel.unknown_factors)}</div>
    </div>
  </div>
</section>` : html`<section>
  <div class="metric-card">
    <div class="metric-label">Conditions alignment score</div>
    <div class="metric-value">Score unavailable</div>
    ${unavailableMessages.map((message) => html`<p>${message}</p>`)}
  </div>
</section>`);
```

> This score describes how forecast conditions align with the approved Spanish
> mackerel model. It does not estimate fish presence, catch likelihood, or
> safety.

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
