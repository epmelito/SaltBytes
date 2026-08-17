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
  sound_side_location_context: "Sound-side location context",
  wind_fishability: "Wind", wave_fishability: "Waves",
  local_baitfish_presence: "Local baitfish presence",
  current_spanish_mackerel_presence: "Current Spanish mackerel presence",
  schools_within_casting_range: "Schools within casting range",
  nearshore_sst_accuracy_and_site_representativeness: "Nearshore water temperature accuracy and local representativeness"
};
const factorSentenceLabels = {
  seasonal_alignment: "seasonal timing",
  thermal_context: "water temperature",
  sound_side_location_context: "sound-side location context",
  wind_fishability: "wind",
  wave_fishability: "waves"
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
const joinItems = (items) => {
  if (items.length < 2) return items[0] ?? "";
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")}, and ${items.at(-1)}`;
};
const assessmentSummary = (positiveFactors, limitingFactors) => {
  const positiveItems = positiveFactors?.map((factor) => factorSentenceLabels[factor] ?? factorLabels[factor] ?? factor) ?? [];
  const limitingItems = limitingFactors?.map((factor) => factorSentenceLabels[factor] ?? factorLabels[factor] ?? factor) ?? [];
  const positive = joinItems(positiveItems);
  const limiting = joinItems(limitingItems);
  const positiveLead = positive ? `${positive[0].toUpperCase()}${positive.slice(1)}` : "";
  const limitingLead = limiting ? `${limiting[0].toUpperCase()}${limiting.slice(1)}` : "";
  const positiveVerb = positiveFactors?.length === 1 && positiveFactors[0] !== "wave_fishability"
    ? "supports"
    : "support";
  const limitingVerb = limitingFactors?.length === 1 && limitingFactors[0] !== "wave_fishability"
    ? "limits"
    : "limit";
  if (positive && limiting) return `${positiveLead} ${positiveVerb} the assessment, while ${limiting} ${limitingVerb} it.`;
  if (positive) return `${positiveLead} ${positiveVerb} the assessment.`;
  if (limiting) return `${limitingLead} ${limitingVerb} the assessment.`;
  return "The available forecast factors do not support a more specific summary.";
};
const assessmentUnknownFactors = spanishMackerel?.unknown_factors?.filter(
  (factor) => factor !== "nearshore_sst_accuracy_and_site_representativeness"
) ?? [];
const factorHighlight = (factors) => {
  const items = factors?.map(
    (factor) => factorSentenceLabels[factor] ?? factorLabels[factor] ?? factor
  ).slice(0, 2) ?? [];
  if (!items.length) return "";
  const first = `${items[0][0].toUpperCase()}${items[0].slice(1)}`;
  return [first, ...items.slice(1)].join(", ");
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
const contextFreshness = manifest.latest_success_freshness_minutes === null || manifest.latest_success_freshness_minutes === undefined
  ? "Freshness is unavailable."
  : `Updated ${formatTimestamp(manifest.generated_at, manifest.display_timezone)}.`;
const selectedForecastDate = asDate(selected?.forecast_time);
const trendWindowHours = 12;
const firstForecastDate = locationRows[0]?.forecastDate;
const lastForecastDate = locationRows.at(-1)?.forecastDate;
const trendWindowStart = new Date(Math.max(
  firstForecastDate?.getTime() ?? selectedForecastDate?.getTime() ?? 0,
  (selectedForecastDate?.getTime() ?? 0) - trendWindowHours * 3600_000
));
const trendWindowEnd = new Date(Math.min(
  lastForecastDate?.getTime() ?? selectedForecastDate?.getTime() ?? 0,
  (selectedForecastDate?.getTime() ?? 0) + trendWindowHours * 3600_000
));
const trendRows = locationRows.filter((row) => row.forecastDate >= trendWindowStart && row.forecastDate <= trendWindowEnd);
const forecastDomain = [trendWindowStart, trendWindowEnd];
const trendHourLabel = new Intl.DateTimeFormat("en-US", {
  timeZone: manifest.display_timezone,
  hour: "numeric"
});
const trendDayLabel = new Intl.DateTimeFormat("en-US", {
  timeZone: manifest.display_timezone,
  month: "short",
  day: "numeric"
});
const trendHourKey = new Intl.DateTimeFormat("en-US", {
  timeZone: manifest.display_timezone,
  hour: "2-digit",
  hourCycle: "h23"
});
const trendShowsDate = trendWindowEnd - trendWindowStart >= 20 * 3600_000;
const trendTickLabel = (value) => trendShowsDate || trendHourKey.format(value) === "00"
  ? `${trendDayLabel.format(value)} · ${trendHourLabel.format(value)}`
  : trendHourLabel.format(value);
const trendTitle = (row, label, value) => `${label}: ${value}\nForecast time: ${formatTimestamp(row.forecast_time, manifest.display_timezone)}`;
const isFiniteNumber = (value) => Number.isFinite(Number(value));
const wind = trendRows
  .filter((row) => isFiniteNumber(row.wind_speed_10m))
  .map((row) => ({...row, metric: "Wind", value: Number(row.wind_speed_10m)}));
const gusts = trendRows
  .filter((row) => isFiniteNumber(row.wind_gusts_10m))
  .map((row) => ({...row, metric: "Gusts", value: Number(row.wind_gusts_10m)}));
const windBand = trendRows
  .filter((row) => isFiniteNumber(row.wind_speed_10m) && isFiniteNumber(row.wind_gusts_10m))
  .map((row) => ({
    ...row,
    wind: Number(row.wind_speed_10m),
    gust: Number(row.wind_gusts_10m)
  }));
const waveSeries = trendRows
  .filter((row) => isFiniteNumber(row.wave_height))
  .map((row) => ({...row, value: Number(row.wave_height)}));
const temperatureSeries = trendRows
  .filter((row) => isFiniteNumber(row.sea_surface_temperature))
  .map((row) => ({...row, value: Number(row.sea_surface_temperature)}));
const minimumSpanDomain = (series, minimumSpan) => {
  if (!series.length) return undefined;
  const values = series.map((row) => row.value);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const midpoint = (minimum + maximum) / 2;
  const span = Math.max(maximum - minimum, minimumSpan);
  const padding = Math.max(span * 0.08, 0.05);
  return [midpoint - span / 2 - padding, midpoint + span / 2 + padding];
};
const temperatureDomain = minimumSpanDomain(temperatureSeries, 1);
const temperatureBaseline = temperatureDomain?.[0] ?? 0;
const selectedSeries = (series) => series.filter((row) => row.forecast_time === selected?.forecast_time);
const previousTideTime = asDate(selected?.tide_previous_extremum_time);
const nextTideTime = asDate(selected?.tide_next_extremum_time);
const selectedTideTime = selectedForecastDate;
const tideTimingAvailable = [
  previousTideTime,
  nextTideTime,
  selectedTideTime,
  selected?.tide_previous_predicted_water_level,
  selected?.tide_next_predicted_water_level
].every((value) => value !== null && isFiniteNumber(value))
  && typeof selected?.tide_phase === "string"
  && previousTideTime < nextTideTime
  && previousTideTime <= selectedTideTime
  && selectedTideTime <= nextTideTime;
const tideLow = tideTimingAvailable
  ? Math.min(Number(selected.tide_previous_predicted_water_level), Number(selected.tide_next_predicted_water_level))
  : 0;
const tideRange = tideTimingAvailable
  ? Math.max(Math.abs(Number(selected.tide_previous_predicted_water_level) - Number(selected.tide_next_predicted_water_level)), 0.2)
  : 1;
const tideY = (level) => 114 - ((Number(level) - tideLow) / tideRange) * 66;
const tideProgress = tideTimingAvailable
  ? (selectedTideTime - previousTideTime) / (nextTideTime - previousTideTime)
  : 0;
const tideSelectedX = 40 + tideProgress * 560;
const tideSelectedAnchor = tideProgress < 0.16 ? "start" : tideProgress > 0.84 ? "end" : "middle";
const tideSelectedLabelX = tideProgress < 0.16
  ? tideSelectedX + 8
  : tideProgress > 0.84
    ? tideSelectedX - 8
    : tideSelectedX;
const tideDateKey = new Intl.DateTimeFormat("en-CA", {
  timeZone: manifest.display_timezone,
  year: "numeric",
  month: "2-digit",
  day: "2-digit"
});
const tideDateLabel = new Intl.DateTimeFormat("en-US", {
  timeZone: manifest.display_timezone,
  month: "short",
  day: "numeric"
});
const tideTimeLabel = new Intl.DateTimeFormat("en-US", {
  timeZone: manifest.display_timezone,
  hour: "numeric",
  minute: "2-digit",
  timeZoneName: "short"
});
const tideEventsShareDate = tideTimingAvailable
  && tideDateKey.format(previousTideTime) === tideDateKey.format(nextTideTime);
const tideEventTime = (value) => {
  const date = asDate(value);
  if (!date) return "Unavailable";
  return tideEventsShareDate
    ? tideTimeLabel.format(date)
    : `${tideDateLabel.format(date)} · ${tideTimeLabel.format(date)}`;
};
const shoreRelationship = (angle) => {
  if (!isFiniteNumber(angle)) return null;
  const absoluteAngle = Math.abs(Number(angle));
  if (absoluteAngle === 90) return "Alongshore";
  return absoluteAngle < 90 ? "Onshore component" : "Offshore component";
};
const directionArrow = (angle) => {
  const radians = Number(angle) * Math.PI / 180;
  const horizontal = Math.sin(radians) * 60;
  const vertical = Math.cos(radians) * 60;
  return {x1: 160 - horizontal, y1: 96 - vertical, x2: 160 + horizontal, y2: 96 + vertical};
};
const windDirection = isFiniteNumber(selected?.wind_to_shore_angle_degrees)
  && isFiniteNumber(selected?.wind_direction_10m)
  ? {label: "Wind", angle: selected.wind_to_shore_angle_degrees, compass: compassDirection(selected.wind_direction_10m), degrees: selected.wind_direction_10m}
  : null;
const waveDirection = isFiniteNumber(selected?.wave_to_shore_angle_degrees)
  && isFiniteNumber(selected?.wave_direction)
  ? {label: "Waves", angle: selected.wave_to_shore_angle_degrees, compass: compassDirection(selected.wave_direction), degrees: selected.wave_direction}
  : null;
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
    ${factorItems(spanishMackerel.positive_factors).length ? html`<div><span class="detail-label">Most helpful now</span><p>${factorHighlight(spanishMackerel.positive_factors)}</p></div>` : null}
    ${factorItems(spanishMackerel.limiting_factors).length ? html`<div><span class="detail-label">Main limitation</span><p>${factorItems(spanishMackerel.limiting_factors).slice(0, 1).join(", ")}</p></div>` : null}
  </div>` : null}
  ${assessmentUnknownFactors.length ? html`<section class="assessment-unknowns"><h4>What SaltBytes cannot observe</h4><ul>${factorList(assessmentUnknownFactors)}</ul></section>` : null}
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
  <div class="conditions-current-summary">
    <article><span class="detail-label">Wind</span><h3>${formatNumber(selected?.wind_speed_10m, 1, "km/h")} with gusts to ${formatNumber(selected?.wind_gusts_10m, 1, "km/h")}</h3><p>From the ${compassDirection(selected?.wind_direction_10m)} (${formatNumber(selected?.wind_direction_10m, 0)}°).</p></article>
    <article><span class="detail-label">Waves</span><h3>${formatNumber(selected?.wave_height, 1, "m")} every ${formatNumber(selected?.wave_period, 1, "s")}</h3><p>From the ${compassDirection(selected?.wave_direction)} (${formatNumber(selected?.wave_direction, 0)}°).</p></article>
    <article><span class="detail-label">Water temperature</span><h3>${formatNumber(selected?.sea_surface_temperature, 1, "°C")}</h3></article>
    <article><span class="detail-label">Precipitation</span><h3>${selected?.precipitation_probability === null || selected?.precipitation_probability === undefined ? "Unavailable" : `${formatNumber(selected?.precipitation_probability, 0, "%")} chance`}</h3><p>${selected?.precipitation === null || selected?.precipitation === undefined ? "Expected amount unavailable." : `${formatNumber(selected?.precipitation, 1, "mm")} expected.`}</p></article>
    <article class="conditions-tide"><span class="detail-label">Tide</span><h3>${selected?.tide_phase ?? "Unavailable"}</h3></article>
  </div>
  <details class="conditions-tide-details"><summary>Tide details</summary><div class="tide-events"><div><strong>Previous ${selected?.tide_previous_extremum_type ?? "tide"}</strong><span>${formatTimestamp(selected?.tide_previous_extremum_time, manifest.display_timezone)}</span><span>${formatNumber(selected?.tide_previous_predicted_water_level, 1, "m")}</span></div><div><strong>Next ${selected?.tide_next_extremum_type ?? "tide"}</strong><span>${formatTimestamp(selected?.tide_next_extremum_time, manifest.display_timezone)}</span><span>${formatNumber(selected?.tide_next_predicted_water_level, 1, "m")}</span></div></div></details>
</section>`);
~~~

## Upcoming changes

Forecast trends around the selected time.

~~~js
const selectedBandMark = () => Plot.ruleX([selectedForecastDate], {
  className: "selected-time-band",
  stroke: "var(--saltbytes-selected)",
  strokeOpacity: 0.1,
  strokeWidth: 18
});
const selectedRuleMark = () => Plot.ruleX([selectedForecastDate], {
  className: "selected-time-rule",
  stroke: "var(--saltbytes-selected)",
  strokeWidth: 2.5
});
const trendTickCount = (width) => width < 480 ? 3 : width < 760 ? 5 : 7;
const trendTickValues = (width) => {
  const dates = trendRows.map((row) => row.forecastDate).filter(Boolean);
  const count = Math.min(trendTickCount(width), dates.length);
  if (count <= 1) return dates.slice(0, 1);

  const indexes = Array.from({length: count}, (_, index) =>
    Math.round(index * (dates.length - 1) / (count - 1))
  );
  return [...new Set(indexes)].map((index) => dates[index]);
};
const trendPlot = ({width, height, marks, yDomain}) => Plot.plot({
  width,
  height,
  marginTop: 12,
  marginRight: 34,
  marginBottom: 38,
  marginLeft: 56,
  x: {
    type: "utc",
    domain: forecastDomain,
    ticks: trendTickValues(width),
    tickFormat: trendTickLabel,
    tickPadding: 8,
    label: null,
    nice: false
  },
  y: {
    domain: yDomain,
    grid: true,
    label: null,
    ticks: 4,
    nice: true
  },
  style: {background: "transparent"},
  marks
});
const line = (series, options = {}) => Plot.lineY(series, {
  x: "forecastDate",
  y: "value",
  stroke: options.stroke,
  strokeWidth: options.strokeWidth ?? 2.8,
  strokeDasharray: options.dashed ? "8,5" : null,
  clip: true,
  className: `forecast-line ${options.className ?? ""}`.trim()
});
const point = (series, title, options = {}) => Plot.dot(series, {
  x: "forecastDate",
  y: "value",
  r: options.r ?? 3.1,
  fill: options.fill,
  stroke: "var(--theme-background)",
  strokeWidth: options.strokeWidth ?? 1.15,
  title,
  tip: true,
  tabindex: 0,
  className: options.className
});
const chartSurface = ({title, unit, className, plot, legend, notice}) => html`<article class="forecast-surface ${className}">
  <header class="visual-surface-header">
    <div><h3>${title}</h3><span class="visual-unit">${unit}</span></div>
    ${legend ?? null}
  </header>
  <div class="trend-track">${plot}</div>
  ${notice ?? null}
</article>`;
const windLegend = html`<div class="series-legend" aria-label="Wind chart legend">
  <span class="legend-wind">Wind</span><span class="legend-gusts">Gusts</span>
</div>`;
const windPlot = resize((width) => trendPlot({
  width,
  height: 288,
  marks: [
    selectedBandMark(),
    Plot.areaY(windBand, {
      x: "forecastDate",
      y1: "wind",
      y2: "gust",
      fill: "var(--saltbytes-gust)",
      fillOpacity: 0.12,
      clip: true,
      className: "wind-gust-band"
    }),
    line(wind, {stroke: "var(--saltbytes-wind)", className: "wind-line"}),
    line(gusts, {stroke: "var(--saltbytes-gust)", dashed: true, className: "gust-line"}),
    point(wind, (row) => trendTitle(row, "Wind", formatNumber(row.value, 1, "km/h")), {fill: "var(--saltbytes-wind)", className: "wind-points"}),
    point(gusts, (row) => trendTitle(row, "Gusts", formatNumber(row.value, 1, "km/h")), {fill: "var(--saltbytes-gust)", className: "gust-points"}),
    selectedRuleMark(),
    point(selectedSeries(wind), (row) => trendTitle(row, "Wind", formatNumber(row.value, 1, "km/h")), {r: 5.6, fill: "var(--saltbytes-wind)", strokeWidth: 2, className: "selected-wind-point"}),
    point(selectedSeries(gusts), (row) => trendTitle(row, "Gusts", formatNumber(row.value, 1, "km/h")), {r: 5.6, fill: "var(--saltbytes-gust)", strokeWidth: 2, className: "selected-gust-point"})
  ]
}));
const wavePlot = resize((width) => trendPlot({
  width,
  height: 240,
  marks: [
    selectedBandMark(),
    Plot.areaY(waveSeries, {
      x: "forecastDate",
      y1: 0,
      y2: "value",
      fill: "var(--saltbytes-wave)",
      fillOpacity: 0.14,
      clip: true,
      className: "wave-area"
    }),
    line(waveSeries, {stroke: "var(--saltbytes-wave)", className: "wave-line"}),
    point(waveSeries, (row) => trendTitle(row, "Wave height", formatNumber(row.value, 1, "m")), {fill: "var(--saltbytes-wave)", className: "wave-points"}),
    selectedRuleMark(),
    point(selectedSeries(waveSeries), (row) => trendTitle(row, "Wave height", formatNumber(row.value, 1, "m")), {r: 5.6, fill: "var(--saltbytes-wave)", strokeWidth: 2, className: "selected-wave-point"})
  ]
}));
const temperaturePlot = resize((width) => trendPlot({
  width,
  height: 240,
  yDomain: temperatureDomain,
  marks: [
    selectedBandMark(),
    Plot.areaY(temperatureSeries, {
      x: "forecastDate",
      y1: temperatureBaseline,
      y2: "value",
      fill: "var(--saltbytes-temperature)",
      fillOpacity: 0.14,
      clip: true,
      className: "temperature-area"
    }),
    line(temperatureSeries, {stroke: "var(--saltbytes-temperature)", className: "temperature-line"}),
    point(temperatureSeries, (row) => trendTitle(row, "Water temperature", formatNumber(row.value, 1, "°C")), {fill: "var(--saltbytes-temperature)", className: "temperature-points"}),
    selectedRuleMark(),
    point(selectedSeries(temperatureSeries), (row) => trendTitle(row, "Water temperature", formatNumber(row.value, 1, "°C")), {r: 5.6, fill: "var(--saltbytes-temperature)", strokeWidth: 2, className: "selected-temperature-point"})
  ]
}));
const tideSurface = tideTimingAvailable ? html`<article class="tide-timing">
  <header class="visual-surface-header">
    <div><h3>Tide timing</h3><span class="visual-unit">${confidenceState(selected.tide_phase)} at the selected time</span></div>
    <span class="visual-time">${tideTimeLabel.format(selectedTideTime)}</span>
  </header>
  <div class="tide-graphic">
    <svg viewBox="0 0 640 150" role="img" aria-label="Straight timing guide between the previous and next tide predictions">
      <line class="tide-guide" x1="40" y1="${tideY(selected.tide_previous_predicted_water_level)}" x2="600" y2="${tideY(selected.tide_next_predicted_water_level)}"></line>
      <line class="tide-selected" x1="${tideSelectedX}" y1="24" x2="${tideSelectedX}" y2="128"></line>
      <circle class="tide-endpoint" cx="40" cy="${tideY(selected.tide_previous_predicted_water_level)}" r="6"></circle>
      <circle class="tide-endpoint" cx="600" cy="${tideY(selected.tide_next_predicted_water_level)}" r="6"></circle>
      <text class="tide-selected-label" x="${tideSelectedLabelX}" y="18" text-anchor="${tideSelectedAnchor}">Selected time · ${selected.tide_phase}</text>
    </svg>
  </div>
  <div class="tide-event-row">
    <div><strong>Previous ${selected.tide_previous_extremum_type}: ${formatNumber(selected.tide_previous_predicted_water_level, 1, "m")}</strong><span>${tideEventTime(selected.tide_previous_extremum_time)}</span></div>
    <div><strong>Next ${selected.tide_next_extremum_type}: ${formatNumber(selected.tide_next_predicted_water_level, 1, "m")}</strong><span>${tideEventTime(selected.tide_next_extremum_time)}</span></div>
  </div>
  <p class="tide-limitation">The line shows timing between tide predictions, not an exact water level.</p>
</article>` : html`<article class="visual-unavailable"><h3>Tide timing</h3><strong>Tide timing unavailable</strong><p>Required tide-event timing or predicted levels are unavailable.</p></article>`;
const directionPanel = (direction, panelClass, markerId) => {
  const label = panelClass === "direction-wind" ? "Wind" : "Waves";
  if (!direction) return html`<section class="direction-panel ${panelClass}"><h4>${label}</h4><p>Direction unavailable</p></section>`;
  const arrow = directionArrow(direction.angle);
  return html`<section class="direction-panel ${panelClass}"><h4>${direction.label}</h4>
    <svg viewBox="0 0 320 200" role="img" aria-label="${direction.label} direction relative to open water, shoreline, and land">
      <defs><marker id="${markerId}" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z"></path></marker></defs>
      <text x="160" y="24" text-anchor="middle">Open water</text>
      <line class="shoreline" x1="28" y1="144" x2="292" y2="144"></line>
      <text x="160" y="165" text-anchor="middle">Shoreline</text>
      <text x="160" y="193" text-anchor="middle">Land</text>
      <line class="direction-arrow" x1="${arrow.x1}" y1="${arrow.y1}" x2="${arrow.x2}" y2="${arrow.y2}" marker-end="url(#${markerId})"></line>
    </svg>
    <p><strong>${shoreRelationship(direction.angle)}</strong><br>From the ${direction.compass} (${formatNumber(direction.degrees, 0)}°)</p>
  </section>`;
};
const directionSurface = html`<article class="shore-direction">
  <header class="visual-surface-header">
    <div><h3>Wind and wave direction</h3><span class="visual-unit">Relative to the shoreline</span></div>
    <span class="visual-time">${formatTimestamp(selected?.forecast_time, manifest.display_timezone)}</span>
  </header>
  <div class="direction-panels">${directionPanel(windDirection, "direction-wind", "wind-arrowhead")}${directionPanel(waveDirection, "direction-wave", "wave-arrowhead")}</div>
</article>`;
const temperatureNotice = selected?.sea_surface_temperature === null || selected?.sea_surface_temperature === undefined
  ? html`<p class="visual-data-unavailable">Water temperature is unavailable at the selected time.</p>`
  : null;
display(html`<section class="forecast-context" aria-label="Forecast trend context">
  <p><strong>Selected time:</strong> ${formatTimestamp(selected?.forecast_time, manifest.display_timezone)}</p>
  ${trendRows.length < 12 ? html`<p class="trend-availability">Only ${trendRows.length} forecast hours are available in this preview.</p>` : null}
</section>`);
display(html`<section class="conditions-visual-grid">
  ${chartSurface({title: "Wind and gusts", unit: "km/h", className: "forecast-wind", plot: windPlot, legend: windLegend})}
  ${chartSurface({title: "Wave height", unit: "m", className: "forecast-wave", plot: wavePlot})}
  ${chartSurface({title: "Water temperature", unit: "°C", className: "forecast-temperature", plot: temperaturePlot, notice: temperatureNotice})}
  ${tideSurface}
  ${directionSurface}
</section>`);
~~~


## Supporting evidence and limitations

<details>
  <summary>Sources and forecast limitations</summary>

  <div class="forecast-limitations">
    <div><strong>Tide times</strong><p>Tide times are predictions for the selected location.</p></div>
    <div><strong>Water temperature</strong><p>Water temperature comes from a regional marine forecast grid, so conditions at the exact fishing location may differ.</p></div>
  </div>
</details>
