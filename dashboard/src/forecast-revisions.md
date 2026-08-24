---
title: Forecast revisions
---

```js
import * as Inputs from "@observablehq/inputs";
import * as Plot from "@observablehq/plot";
import {html} from "npm:htl";

import {
  asDate,
  celsiusToFahrenheit,
  formatNumber,
  formatTimestamp,
  kilometersPerHourToMph,
  locationName,
  metersToFeet
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const history = await FileAttachment("./data/forecast-history.json").json();
const rows = history.map((row) => ({
  ...row,
  runDate: asDate(row.run_started_at)
}));
const metrics = [
  {field: "wind_speed_10m", label: "Wind speed", unit: "mph", digits: 1, convert: kilometersPerHourToMph},
  {field: "wave_height", label: "Wave height", unit: "ft", digits: 1, convert: metersToFeet},
  {field: "sea_surface_temperature", label: "Sea surface temperature", unit: "°F", digits: 0, convert: celsiusToFahrenheit},
  {field: "tide_predicted_range", label: "Predicted tide range", unit: "ft", digits: 1, convert: metersToFeet}
];
function measurementPicker(items) {
  const picker = html`
    <div class="revision-measurement-control">
      <span class="revision-measurement-label">Measurement</span>
      <div class="revision-measurement-picker" role="group" aria-label="Measurement">
        ${items.map((item) => html`
          <button
            type="button"
            class="revision-measurement-option"
            data-revision-measurement=${item.field}
            aria-pressed="false"
          >${item.label}</button>
        `)}
      </div>
    </div>
  `;
  const buttons = [...picker.querySelectorAll(".revision-measurement-option")];

  function selectMeasurement(field, notify = false) {
    picker.value = field;
    for (const button of buttons) {
      const selected = button.dataset.revisionMeasurement === field;
      button.setAttribute("aria-pressed", String(selected));
      button.dataset.selected = String(selected);
    }
    if (notify) picker.dispatchEvent(new Event("input", {bubbles: true}));
  }

  for (const button of buttons) {
    button.addEventListener("click", () =>
      selectMeasurement(button.dataset.revisionMeasurement, true)
    );
  }

  selectMeasurement(items[0]?.field);
  return picker;
}
const shortRunId = (value) => {
  if (!value) return "Unavailable";
  const text = String(value);
  return text.length <= 16 ? text : `${text.slice(0, 6)}…${text.slice(-6)}`;
};
const roundedValue = (value, digits) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return null;
  return Number(Number(value).toFixed(digits));
};
const presentationValue = (value, metric) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return null;
  return roundedValue(metric.convert(value), metric.digits);
};
const normalizedChange = (value, digits) => {
  const number = roundedValue(value, digits);
  if (number === null) return null;
  return Object.is(number, -0) ? 0 : number;
};
const formatSignedNumber = (value, digits, unit) => {
  const number = normalizedChange(value, digits);
  if (number === null) return "Unavailable";
  if (number === 0) return formatNumber(0, digits, unit);
  const sign = number > 0 ? "+" : "−";
  return `${sign}${formatNumber(Math.abs(number), digits, unit)}`;
};
const metricValueAvailable = (value) => value !== null
  && value !== undefined
  && !Number.isNaN(Number(value));
const chartTickFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: manifest.display_timezone,
  month: "short",
  day: "numeric",
  hour: "numeric"
});
const chartTimeZoneName = (value) => {
  const date = asDate(value) ?? new Date();
  const options = {
    timeZone: manifest.display_timezone,
    timeZoneName: "shortGeneric"
  };
  return new Intl.DateTimeFormat("en-US", options)
    .formatToParts(date)
    .find((part) => part.type === "timeZoneName")?.value ?? manifest.display_timezone;
};
```

# Forecast revisions

See how a forecast changed as newer updates were saved. Choose one location,
forecast time, and measurement to compare the available history.

```js
const locationId = view(Inputs.select(
  locations.map((location) => location.location_id),
  {
    label: "Location",
    format: (value) => locationName(value, locations),
    value: locations[0]?.location_id
  }
));
```

```js
const locationRows = rows.filter((row) => row.location_id === locationId);
const validTimes = [...new Set(locationRows.map((row) => row.forecast_time))].sort();
const validTimeOptions = validTimes.length ? validTimes : [""];
const validTime = view(Inputs.select(validTimeOptions, {
  label: "Forecast for",
  format: (value) => value
    ? formatTimestamp(value, manifest.display_timezone)
    : "No forecast times",
  value: validTimeOptions[0],
  disabled: validTimes.length === 0
}));
```

```js
const metricField = view(measurementPicker(metrics));
```

```js
const metric = metrics.find((item) => item.field === metricField) ?? metrics[0];
const selectedRows = locationRows
  .filter((row) => row.forecast_time === validTime)
  .sort((left, right) => (left.runDate?.getTime() ?? 0) - (right.runDate?.getTime() ?? 0));
const chartRows = selectedRows
  .filter((row) => metricValueAvailable(row[metricField]))
  .map((row) => ({
    ...row,
    metricValue: presentationValue(row[metricField], metric)
  }));
const revisionRows = chartRows.map((row, index) => {
  const previous = chartRows[index - 1] ?? null;
  const change = previous ? row.metricValue - previous.metricValue : null;
  return {
    ...row,
    change,
    previousValue: previous?.metricValue ?? null,
    absoluteChange: change === null ? null : Math.abs(change)
  };
});
const earliestRow = chartRows[0] ?? null;
const latestRow = chartRows.at(-1) ?? null;
const totalChange = earliestRow && latestRow
  ? normalizedChange(latestRow.metricValue - earliestRow.metricValue, metric.digits)
  : null;
const metricValues = chartRows.map((row) => row.metricValue);
const lowestValue = metricValues.length ? Math.min(...metricValues) : null;
const highestValue = metricValues.length ? Math.max(...metricValues) : null;
const observedRange = lowestValue === null || highestValue === null
  ? null
  : normalizedChange(highestValue - lowestValue, metric.digits);
const changedUpdates = revisionRows.slice(1).filter(
  (row) => normalizedChange(row.change, metric.digits) !== 0
);
const largestChange = changedUpdates.reduce(
  (largest, row) => !largest || row.absoluteChange > largest.absoluteChange ? row : largest,
  null
);
const comparisonCount = Math.max(chartRows.length - 1, 0);
const revisionState = chartRows.length === 0
  ? "empty"
  : chartRows.length === 1
    ? "single"
    : "available";
const normalizedTotalChange = normalizedChange(totalChange, metric.digits);
const hasObservedVariation = observedRange !== null && observedRange !== 0;
const formatObservedRange = () => {
  if (lowestValue === null || highestValue === null) return "Unavailable";
  if (!hasObservedVariation) return formatNumber(lowestValue, metric.digits, metric.unit);
  return `${formatNumber(lowestValue, metric.digits)}–${formatNumber(highestValue, metric.digits, metric.unit)}`;
};
const summaryHeadline = revisionState === "empty"
  ? `No saved ${metric.label.toLowerCase()} values`
  : revisionState === "single"
    ? `${metric.label} has one saved value`
    : !hasObservedVariation
      ? `${metric.label} did not change`
      : normalizedTotalChange === 0
        ? `${metric.label} finished where it started`
        : `${metric.label} finished ${formatNumber(Math.abs(normalizedTotalChange), metric.digits, metric.unit)} ${normalizedTotalChange > 0 ? "higher" : "lower"}`;
const availabilityDescription = chartRows.length === selectedRows.length
  ? `${chartRows.length} saved forecast${chartRows.length === 1 ? "" : "s"}`
  : `${chartRows.length} available value${chartRows.length === 1 ? "" : "s"} from ${selectedRows.length} saved forecasts`;
const summaryDetail = revisionState === "empty"
  ? "Try another location, forecast time, or measurement."
  : revisionState === "single"
    ? "Another saved value is needed to calculate change."
    : !hasObservedVariation
      ? `All ${availabilityDescription} showed ${formatNumber(lowestValue, metric.digits, metric.unit)}.`
      : "";
const summaryContext = validTime
  ? `${locationName(locationId, locations)} · forecast for ${formatTimestamp(validTime, manifest.display_timezone)}`
  : `${locationName(locationId, locations)} · no forecast time available`;
const recentRows = revisionRows.slice().reverse().slice(0, 5);
const historyIsTruncated = revisionRows.length > recentRows.length;
const revisionByRun = new Map(revisionRows.map((row) => [row.run_id, row]));
const axisTimeZone = chartTimeZoneName(latestRow?.run_started_at ?? validTime);
```

```js
display(html`<section
  class=${`revision-summary revision-summary-${revisionState}`}
  data-revision-state=${revisionState}
>
  <p class="revision-summary-context">${summaryContext}</p>
  <div class="revision-summary-main">
    <div class="revision-summary-story">
      <p class="revision-eyebrow">How the forecast changed</p>
      <h2>${summaryHeadline}</h2>
      ${summaryDetail ? html`<p>${summaryDetail}</p>` : null}
    </div>
    <div class="revision-primary-value" data-revision-metric="latest">
      <span>Latest forecast</span>
      <strong>${latestRow ? formatNumber(latestRow.metricValue, metric.digits, metric.unit) : "Unavailable"}</strong>
      <small>${latestRow ? `Saved ${formatTimestamp(latestRow.run_started_at, manifest.display_timezone)}` : "No saved value"}</small>
    </div>
  </div>
  <div class="revision-supporting-facts">
    <div data-revision-metric="earliest">
      <span>Started at</span>
      <strong>${earliestRow ? formatNumber(earliestRow.metricValue, metric.digits, metric.unit) : "Unavailable"}</strong>
      <small>${earliestRow ? `Saved ${formatTimestamp(earliestRow.run_started_at, manifest.display_timezone)}` : "No saved value"}</small>
    </div>
    <div data-revision-metric="range">
      <span>Lowest to highest</span>
      <strong>${formatObservedRange()}</strong>
      <small>${chartRows.length ? `Across ${chartRows.length} available value${chartRows.length === 1 ? "" : "s"}` : "No saved values"}</small>
    </div>
    <div data-revision-metric="largest-update">
      <span>Largest update</span>
      <strong>${largestChange ? formatSignedNumber(largestChange.change, metric.digits, metric.unit) : revisionState === "available" ? "No change" : "Unavailable"}</strong>
      <small>${largestChange
        ? `Saved ${formatTimestamp(largestChange.run_started_at, manifest.display_timezone)}`
        : revisionState === "available"
          ? "No comparison changed the value"
          : "Needs at least two values"}</small>
    </div>
    <div data-revision-metric="changed-updates">
      <span>Changed updates</span>
      <strong>${changedUpdates.length} of ${comparisonCount}</strong>
      <small>${comparisonCount === 0 ? "No comparisons available" : "Comparisons that changed the value"}</small>
    </div>
  </div>
</section>`);
```

## Revision history

```js
if (chartRows.length === 0) {
  display(html`<div class="notice revision-notice">
    <strong>No saved values</strong>
    Try another location, forecast time, or measurement.
  </div>`);
} else if (chartRows.length === 1) {
  display(html`<div class="notice revision-notice">
    <strong>One saved value</strong>
    Another saved forecast is needed to show change over time.
  </div>`);
} else if (!hasObservedVariation) {
  display(html`<div class="notice revision-notice">
    <strong>No changes to plot</strong>
    All ${availabilityDescription} showed ${formatNumber(lowestValue, metric.digits, metric.unit)}.
  </div>`);
} else {
  display(html`<div class="revision-chart">
    <p class="revision-chart-measure">${metric.label} (${metric.unit})</p>
    ${Plot.plot({
      width: Math.max(Math.min(width - 32, 1280), 320),
      height: 300,
      marginTop: 18,
      marginLeft: 64,
      marginRight: 24,
      marginBottom: 48,
      x: {
        type: "utc",
        label: `Saved at (${axisTimeZone})`,
        ticks: 6,
        tickFormat: (value) => chartTickFormatter.format(value)
      },
      y: {
        grid: true,
        label: null,
        ticks: 5,
        tickFormat: (value) => formatNumber(value, metric.digits)
      },
      marks: [
        Plot.lineY(chartRows, {
          x: "runDate",
          y: "metricValue",
          curve: "step-after",
          className: "revision-history-line"
        }),
        largestChange ? Plot.ruleX([largestChange], {
          x: "runDate",
          y1: "previousValue",
          y2: "metricValue",
          stroke: "var(--saltbytes-selected)",
          strokeWidth: 5,
          className: "revision-largest-segment"
        }) : null,
        Plot.dot(chartRows, {
          x: "runDate",
          y: "metricValue",
          r: 3.5,
          tip: {
            lineWidth: 32,
            format: {
              x: (value) => formatTimestamp(value, manifest.display_timezone),
              y: (value) => formatNumber(value, metric.digits)
            }
          }
        }),
        latestRow ? Plot.dot([latestRow], {
          x: "runDate",
          y: "metricValue",
          r: 7,
          strokeWidth: 2.5,
          fill: "var(--saltbytes-surface)",
          className: "revision-latest-dot"
        }) : null
      ].filter(Boolean)
    })}
    <div class="revision-chart-footer">
      <span>${largestChange
        ? `Largest update ${formatSignedNumber(largestChange.change, metric.digits, metric.unit)} is highlighted.`
        : "The stepped line holds each saved value until the next update."}</span>
      <span>Times are shown in ${axisTimeZone}.</span>
    </div>
  </div>`);
}
```

## Saved forecast history

```js
if (recentRows.length === 0) {
  display(html`<p class="page-note revision-empty-history">No saved forecasts with ${metric.label.toLowerCase()} values are available for this selection.</p>`);
} else {
  display(html`<div class="table-scroll revision-recent-table">
    <table>
      <thead>
        <tr>
          <th>Saved at</th>
          <th>${metric.label}</th>
          <th>Change from prior available value</th>
          <th>Run ID</th>
        </tr>
      </thead>
      <tbody>
        ${recentRows.map((row) => {
          const revision = revisionByRun.get(row.run_id);
          return html`<tr>
            <td>${formatTimestamp(row.run_started_at, manifest.display_timezone)}</td>
            <td>${formatNumber(revision?.metricValue, metric.digits, metric.unit)}</td>
            <td>${revision?.change === null || revision?.change === undefined
              ? "First available value"
              : formatSignedNumber(revision.change, metric.digits, metric.unit)}</td>
            <td><code title=${row.run_id}>${historyIsTruncated ? shortRunId(row.run_id) : row.run_id}</code></td>
          </tr>`;
        })}
      </tbody>
    </table>
  </div>`);
}
```

```js
if (historyIsTruncated) {
  display(html`<details class="revision-details">
    <summary>Complete available history and exact run identifiers</summary>
    <p>
      The table above shows the five most recent saved forecasts with an
      available value for the selected measurement. This table includes every
      saved forecast with an available value for that measurement in the selected context.
    </p>
    <div class="table-scroll revision-complete-table">
      <table>
        <thead>
          <tr>
            <th>Full run ID</th>
            <th>Saved at</th>
            <th>Forecast for</th>
            <th>${metric.label}</th>
            <th>Change from prior available value</th>
          </tr>
        </thead>
        <tbody>
          ${revisionRows.map((row) => {
            const revision = revisionByRun.get(row.run_id);
            return html`<tr>
              <td><code>${row.run_id}</code></td>
              <td>${formatTimestamp(row.run_started_at, manifest.display_timezone)}</td>
              <td>${formatTimestamp(row.forecast_time, manifest.display_timezone)}</td>
              <td>${formatNumber(revision?.metricValue, metric.digits, metric.unit)}</td>
              <td>${revision?.change === null || revision?.change === undefined
                ? "First available value"
                : formatSignedNumber(revision.change, metric.digits, metric.unit)}</td>
            </tr>`;
          })}
        </tbody>
      </table>
    </div>
  </details>`);
}
```
