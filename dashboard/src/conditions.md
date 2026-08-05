---
title: Conditions
---

~~~js
import * as Inputs from "@observablehq/inputs";
import * as Plot from "@observablehq/plot";
import {html} from "npm:htl";

import {
  asDate,
  compassDirection,
  formatNumber,
  formatTimestamp,
  locationName
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const conditions = await FileAttachment("./data/conditions.json").json();
const rows = conditions.map((row) => ({...row, forecastDate: asDate(row.forecast_time)}));
~~~

# Conditions

Choose a location and forecast time to see the current coastal outlook. Forecast
values are predictions, not observations.

~~~js
const locationId = view(Inputs.select(
  locations.map((location) => location.location_id),
  {label: "Location", format: (value) => locationName(value, locations), value: locations[0].location_id}
));
~~~

~~~js
const locationRows = rows.filter((row) => row.location_id === locationId);
const forecastTime = view(Inputs.select(
  locationRows.map((row) => row.forecast_time),
  {label: "Forecast time", format: (value) => formatTimestamp(value, manifest.display_timezone), value: locationRows[0]?.forecast_time}
));
~~~

~~~js
const selected = locationRows.find((row) => row.forecast_time === forecastTime);
const spanishMackerel = selected?.spanish_mackerel_conditions;
const scoreIsAvailable = spanishMackerel?.state === "available";
const scoreBandPresentation = {
  very_limited_alignment: "Very limited forecast alignment",
  limited_alignment: "Limited forecast alignment",
  mixed_conditions: "Mixed forecast conditions",
  favorable_alignment: "Favorable forecast alignment",
  strong_alignment: "Strong forecast alignment"
};
const factorLabels = {
  seasonal_alignment: "Seasonal timing", thermal_context: "Water temperature",
  wind_fishability: "Wind", wave_fishability: "Waves",
  local_baitfish_presence: "Local baitfish presence",
  current_spanish_mackerel_presence: "Current Spanish mackerel presence",
  schools_within_casting_range: "Schools within casting range",
  nearshore_sst_accuracy_and_site_representativeness: "Nearshore water temperature accuracy and local representativeness"
};
const confidenceLabels = {
  location_applicability_confidence: "Fit for this location",
  environmental_source_confidence: "Forecast data",
  seasonal_evidence_confidence: "Seasonal evidence",
  habitat_data_confidence: "Habitat information",
  fishability_data_confidence: "Fishing condition data",
  overall_interpretation_confidence: "Overall confidence"
};
const confidenceState = (value) => value ? `${value[0].toUpperCase()}${value.slice(1)}` : "Unavailable";
const factorItems = (factors) => factors?.map((factor) => factorLabels[factor] ?? factor) ?? [];
const factorList = (factors) => factorItems(factors).map((factor) => html`<li>${factor}</li>`);
const joinFactors = (factors) => {
  const items = factorItems(factors);
  if (items.length < 2) return items[0] ?? "";
  return `${items.slice(0, -1).join(", ")} and ${items.at(-1)}`;
};
const assessmentSummary = (positiveFactors, limitingFactors) => {
  const positive = joinFactors(positiveFactors);
  const limiting = joinFactors(limitingFactors);
  if (positive && limiting) return `${positive} support the assessment, while ${limiting.toLowerCase()} limit it.`;
  if (positive) return `${positive} support the assessment.`;
  if (limiting) return `${limiting} limit the assessment.`;
  return "The available forecast factors do not support a more specific summary.";
};
const overallConfidence = spanishMackerel?.confidence?.find((item) => item.identifier === "overall_interpretation_confidence");
const confidenceDetails = [
  "overall_interpretation_confidence",
  "seasonal_evidence_confidence",
  "location_applicability_confidence",
  "environmental_source_confidence",
  "fishability_data_confidence",
  "habitat_data_confidence"
].map((identifier) => spanishMackerel?.confidence?.find((item) => item.identifier === identifier)).filter(Boolean);
const unavailableMessageGroups = [
  {reasons: ["location_not_applicable"], message: "This assessment is not available for this location and fishing context."},
  {reasons: ["forecast_time_invalid", "display_timezone_missing", "display_timezone_invalid", "local_forecast_date_unavailable"], message: "Required forecast timing information is unavailable."},
  {reasons: ["weather_source_missing", "weather_source_not_success", "wind_speed_10m_missing", "wind_speed_10m_invalid", "wind_gusts_10m_missing", "wind_gusts_10m_invalid"], message: "Required wind forecast data is unavailable."},
  {reasons: ["wave_source_missing", "wave_source_not_success", "wave_height_missing", "wave_height_invalid"], message: "Required wave forecast data is unavailable."},
  {reasons: ["sst_source_missing", "sst_source_not_success", "sea_surface_temperature_missing", "sea_surface_temperature_invalid"], message: "Required water temperature forecast data is unavailable."}
];
const unavailableMessages = unavailableMessageGroups.filter((group) => spanishMackerel?.unavailable_reasons?.some((reason) => group.reasons.includes(reason))).map((group) => group.message);
const windSeries = locationRows.flatMap((row) => [{forecastDate: row.forecastDate, metric: "Wind", value: row.wind_speed_10m}, {forecastDate: row.forecastDate, metric: "Gust", value: row.wind_gusts_10m}]);
const directionSeries = locationRows.flatMap((row) => [{forecastDate: row.forecastDate, metric: "Wind", value: row.wind_to_shore_angle_degrees}, {forecastDate: row.forecastDate, metric: "Wave", value: row.wave_to_shore_angle_degrees}]);
const contextFreshness = manifest.latest_success_freshness_minutes === null || manifest.latest_success_freshness_minutes === undefined
  ? "Freshness is unavailable."
  : `Updated ${formatTimestamp(manifest.generated_at, manifest.display_timezone)}.`;
~~~

~~~js
display(html`<section class="conditions-context" aria-label="Forecast context">
  <p class="conditions-eyebrow">Coastal forecast</p>
  <h2>${locationName(locationId, locations)}</h2>
  <p><strong>Selected time:</strong> ${formatTimestamp(forecastTime, manifest.display_timezone)}</p>
  <p class="page-note">${contextFreshness}</p>
</section>`);
~~~

## Spanish mackerel assessment

~~~js
display(scoreIsAvailable ? html`<section class="conditions-assessment">
  <div><p class="conditions-eyebrow">Spanish mackerel forecast</p><h3>${scoreBandPresentation[spanishMackerel.score_band] ?? "Forecast assessment available"}</h3><p class="assessment-summary">${assessmentSummary(spanishMackerel.positive_factors, spanishMackerel.limiting_factors)}</p></div>
  <div class="assessment-support"><div><span class="detail-label">Score</span><strong class="assessment-score">${spanishMackerel.score} / 100</strong></div><div><span class="detail-label">Overall confidence</span><strong>${confidenceState(overallConfidence?.state)}</strong></div></div>
  <p class="assessment-limitation">This assessment does not estimate fish presence, catch likelihood, or safety.</p>
  ${factorItems(spanishMackerel.positive_factors).length || factorItems(spanishMackerel.limiting_factors).length ? html`<div class="assessment-highlights">
    ${factorItems(spanishMackerel.positive_factors).length ? html`<div><span class="detail-label">Most helpful now</span><p>${factorItems(spanishMackerel.positive_factors).slice(0, 2).join(", ")}</p></div>` : null}
    ${factorItems(spanishMackerel.limiting_factors).length ? html`<div><span class="detail-label">Main limitation</span><p>${factorItems(spanishMackerel.limiting_factors).slice(0, 1).join(", ")}</p></div>` : null}
  </div>` : null}
  ${factorItems(spanishMackerel.unknown_factors).length ? html`<section class="assessment-unknowns"><h4>What SaltBytes cannot observe</h4><ul>${factorList(spanishMackerel.unknown_factors)}</ul></section>` : null}
  <details><summary>Assessment factors and confidence</summary><div class="assessment-details">
    ${factorItems(spanishMackerel.positive_factors).length ? html`<div><h4>Supporting conditions</h4><ul>${factorList(spanishMackerel.positive_factors)}</ul></div>` : null}
    ${factorItems(spanishMackerel.limiting_factors).length ? html`<div><h4>Limiting conditions</h4><ul>${factorList(spanishMackerel.limiting_factors)}</ul></div>` : null}
    <div><h4>Confidence in this assessment</h4><dl class="confidence-values">${confidenceDetails.map((item) => html`<div><dt>${confidenceLabels[item.identifier]}</dt><dd>${confidenceState(item.state)}</dd></div>`)}</dl></div>
  </div></details>
</section>` : html`<section class="conditions-assessment conditions-assessment-unavailable">
  <p class="conditions-eyebrow">Spanish mackerel forecast</p><h3>Assessment unavailable</h3>
  ${unavailableMessages.map((message) => html`<p>${message}</p>`)}
  <p class="assessment-limitation">This assessment does not estimate fish presence, catch likelihood, or safety.</p>
</section>`);
~~~

## Current coastal conditions

~~~js
display(html`<section class="conditions-current">
  <article><span class="detail-label">Wind</span><h3>${formatNumber(selected?.wind_speed_10m, 1, "km/h")} with gusts to ${formatNumber(selected?.wind_gusts_10m, 1, "km/h")}</h3><p>From the ${compassDirection(selected?.wind_direction_10m)} (${formatNumber(selected?.wind_direction_10m, 0)}°).</p></article>
  <article><span class="detail-label">Waves</span><h3>${formatNumber(selected?.wave_height, 1, "m")} every ${formatNumber(selected?.wave_period, 1, "s")}</h3><p>From the ${compassDirection(selected?.wave_direction)} (${formatNumber(selected?.wave_direction, 0)}°).</p></article>
  <article><span class="detail-label">Water temperature</span><h3>${formatNumber(selected?.sea_surface_temperature, 1, "°C")}</h3></article>
  <article><span class="detail-label">Precipitation</span><h3>${selected?.precipitation_probability === null || selected?.precipitation_probability === undefined ? "Unavailable" : `${formatNumber(selected?.precipitation_probability, 0, "%")} chance`}</h3><p>${selected?.precipitation === null || selected?.precipitation === undefined ? "Expected amount unavailable." : `${formatNumber(selected?.precipitation, 1, "mm")} expected.`}</p></article>
  <article class="conditions-tide"><span class="detail-label">Tide</span><h3>${selected?.tide_phase ?? "Unavailable"}</h3><details><summary>Tide details</summary><div class="tide-events"><div><strong>Previous ${selected?.tide_previous_extremum_type ?? "tide"}</strong><span>${formatTimestamp(selected?.tide_previous_extremum_time, manifest.display_timezone)}</span><span>${formatNumber(selected?.tide_previous_predicted_water_level, 1, "m")}</span></div><div><strong>Next ${selected?.tide_next_extremum_type ?? "tide"}</strong><span>${formatTimestamp(selected?.tide_next_extremum_time, manifest.display_timezone)}</span><span>${formatNumber(selected?.tide_next_predicted_water_level, 1, "m")}</span></div></div></details></article>
</section>`);
~~~

## Upcoming changes

Charts show the complete exported forecast window for the selected location.
Unavailable values remain visible as gaps.

<div class="chart-grid">
  <div class="chart-card">

### Wind and gust

~~~js
Plot.plot({height: 300, x: {type: "utc", label: "Forecast time"}, y: {grid: true, label: "km/h"}, color: {legend: true}, marks: [Plot.lineY(windSeries, {x: "forecastDate", y: "value", stroke: "metric", marker: true, tip: true}), Plot.ruleY([0])]})
~~~

  </div>
  <div class="chart-card">

### Wave height

~~~js
Plot.plot({height: 300, x: {type: "utc", label: "Forecast time"}, y: {grid: true, label: "metres"}, marks: [Plot.lineY(locationRows, {x: "forecastDate", y: "wave_height", marker: true, tip: true}), Plot.ruleY([0])]})
~~~

  </div>
  <div class="chart-card">

### Water temperature

~~~js
Plot.plot({height: 300, x: {type: "utc", label: "Forecast time"}, y: {grid: true, label: "°C"}, marks: [Plot.lineY(locationRows, {x: "forecastDate", y: "sea_surface_temperature", marker: true, tip: true})]})
~~~

  </div>
  <div class="chart-card">

### Direction relative to shore

~~~js
Plot.plot({height: 300, x: {type: "utc", label: "Forecast time"}, y: {domain: [-180, 180], grid: true, label: "degrees from seaward shore normal"}, color: {legend: true}, marks: [Plot.lineY(directionSeries, {x: "forecastDate", y: "value", stroke: "metric", marker: true, tip: true}), Plot.ruleY([-90, 0, 90])]})
~~~

  </div>
</div>

## Supporting evidence and limitations

<details>
  <summary>Sources and forecast limitations</summary>

  <div class="forecast-limitations">
    <div><strong>Tide times</strong><p>Tide times are predictions for the selected location.</p></div>
    <div><strong>Water temperature</strong><p>Water temperature comes from a regional marine forecast grid.</p></div>
  </div>
</details>
