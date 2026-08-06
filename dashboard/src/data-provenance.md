---
title: Forecast sources
---

```js
import * as Inputs from "@observablehq/inputs";
import {html} from "npm:htl";

import {
  formatNumber,
  formatTimestamp,
  locationName,
  sourceName
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const provenance = await FileAttachment("./data/provenance.json").json();

const expectedSources = ["weather", "wave", "sst", "tide"];

function providerName(source) {
  return source === "tide" ? "NOAA Tides and Currents" : "Open-Meteo";
}

function sourceIdentity(row) {
  return row?.source === "tide" ? row?.station_id : row?.model_selector;
}

function traceabilityState(row) {
  if (!row?.snapshot_id) return "missing";
  if (!row?.captured_at || !sourceIdentity(row)) return "incomplete";
  return "complete";
}

function traceabilityLabel(state) {
  return {
    complete: "Traceable",
    incomplete: "Incomplete evidence",
    missing: "Missing snapshot"
  }[state];
}

function traceabilityDetail(state) {
  return {
    complete: "Source identity and preserved snapshot are available.",
    incomplete: "A snapshot is linked, but source details are incomplete.",
    missing: "No preserved source snapshot is linked to this published scope."
  }[state];
}

function directionLabel(value) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return "Unavailable";

  const labels = [
    "North",
    "North northeast",
    "Northeast",
    "East northeast",
    "East",
    "East southeast",
    "Southeast",
    "South southeast",
    "South",
    "South southwest",
    "Southwest",
    "West southwest",
    "West",
    "West northwest",
    "Northwest",
    "North northwest"
  ];
  const normalized = ((numeric % 360) + 360) % 360;
  const label = labels[Math.floor((normalized + 11.25) / 22.5) % 16];
  return `${label} (${normalized.toFixed(0)}°)`;
}

function orientationMethodLabel(value) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  if (value === "Manual review of local shoreline tangent in north up satellite imagery; seaward normal rounded to nearest 5 degrees") {
    return "Estimated from satellite imagery and rounded to the nearest 5 degrees";
  }
  return String(value);
}

function orientationSourceLabel(value) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  const match = String(value).match(
    /^User provided Google Maps satellite screenshot reviewed (\d{4}-\d{2}-\d{2})$/
  );
  return match
    ? `Google Maps satellite imagery reviewed ${match[1]}`
    : String(value);
}

function orientationLimitationLabel(value) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  return {
    "Local shoreline is mildly curved; the pier axis differs from the shore normal and the values are not survey grade":
      "The shoreline curves slightly, and the pier points in a slightly different direction from straight offshore. These directions are approximate, not survey measurements.",
    "Applies to the pier beach segment and pier axis, not Bogue Inlet or nearby channel geometry":
      "This review covers the beach and pier, not Bogue Inlet or nearby channels."
  }[value] ?? String(value);
}

function sourcePicker(rows) {
  const picker = html`
    <div class="provenance-source-list" role="group" aria-label="Source traceability coverage">
      <div class="provenance-source-list-header" aria-hidden="true">
        <span>Source</span>
        <span>Provider</span>
        <span>Snapshot captured</span>
        <span>Status</span>
        <span></span>
      </div>
      ${rows.map((row) => html`
        <button
          type="button"
          class="provenance-source-option"
          data-provenance-source=${row.source}
          data-traceability-state=${row.state}
          aria-pressed="false"
        >
          <strong data-provenance-column="source">${sourceName(row.source)}</strong>
          <span data-provenance-column="provider">${row.provider}</span>
          <span data-provenance-column="captured">${row.captured_at
            ? formatTimestamp(row.captured_at, manifest.display_timezone)
            : "Unavailable"}</span>
          <span class=${`provenance-status provenance-status-${row.state}`}>
            ${traceabilityLabel(row.state)}
          </span>
          <span class="provenance-source-action">View details</span>
        </button>
      `)}
    </div>
  `;

  const buttons = [...picker.querySelectorAll(".provenance-source-option")];

  function selectSource(source, notify = false) {
    picker.value = source;
    for (const button of buttons) {
      const selected = button.dataset.provenanceSource === source;
      button.setAttribute("aria-pressed", String(selected));
      button.dataset.selected = String(selected);
      button.querySelector(".provenance-source-action").textContent =
        selected ? "Selected" : "View details";
    }
    if (notify) picker.dispatchEvent(new Event("input", {bubbles: true}));
  }

  for (const button of buttons) {
    button.addEventListener("click", () =>
      selectSource(button.dataset.provenanceSource, true)
    );
  }

  selectSource(rows[0]?.source ?? expectedSources[0]);
  return picker;
}
```

# Forecast sources

<p class="provenance-intro">
  See which providers and preserved snapshots support the latest published
  forecast. Open any source for its exact identifiers and request details.
</p>

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
const locationRows = provenance.filter((row) => row.location_id === locationId);
const sourceRows = expectedSources.map((source) =>
  locationRows.find((row) => row.source === source) ?? {location_id: locationId, source}
);
const traceabilityRows = sourceRows.map((row) => ({
  ...row,
  provider: providerName(row.source),
  state: traceabilityState(row)
}));
const traceabilityGaps = traceabilityRows.filter((row) => row.state !== "complete");
const completeSourceCount = traceabilityRows.length - traceabilityGaps.length;
const latestRun = manifest.latest_success;
const forecastStart = manifest.forecast_window?.start;
const forecastEnd = manifest.forecast_window?.end;
const locationMetadata = sourceRows.find((row) => [
  row.shore_normal_azimuth_degrees,
  row.pier_seaward_azimuth_degrees,
  row.orientation_reviewed_at,
  row.orientation_method,
  row.orientation_source,
  row.orientation_limitation
].some((value) => value != null)) ?? sourceRows[0];
```

```js
display(html`
<section
  class="provenance-verdict"
  data-traceability-state=${traceabilityGaps.length === 0 ? "complete" : "attention"}
>
  <p class="provenance-eyebrow">Traceability status</p>
  <h2>${traceabilityGaps.length === 0
    ? "All four data sources are traceable"
    : `${traceabilityGaps.length} data ${traceabilityGaps.length === 1 ? "source needs" : "sources need"} attention`}</h2>
  <p class="provenance-verdict-summary">
    ${traceabilityGaps.length === 0
      ? `Each published source for ${locationName(locationId, locations)} links to identified source data from the latest successful run.`
      : `${completeSourceCount} of 4 published sources for ${locationName(locationId, locations)} have complete traceability evidence.`}
  </p>
  ${traceabilityGaps.length === 0 ? null : html`
    <ul class="provenance-exception-list">
      ${traceabilityGaps.map((row) => html`
        <li><strong>${sourceName(row.source)}</strong>: ${traceabilityDetail(row.state)}</li>
      `)}
    </ul>
  `}
  <div class="provenance-scope" aria-label="Published forecast scope">
    <div>
      <span>Published run</span>
      <strong>${formatTimestamp(latestRun?.started_at, manifest.display_timezone)}</strong>
    </div>
    <div>
      <span>Forecast window</span>
      <strong>${formatTimestamp(forecastStart, manifest.display_timezone)} to ${formatTimestamp(forecastEnd, manifest.display_timezone)}</strong>
    </div>
    <div>
      <span>Sources traced</span>
      <strong>${completeSourceCount} of 4</strong>
    </div>
  </div>
</section>
`);
```

## Source coverage

Select a source to inspect the evidence retained for this location and run.

```js
const source = view(sourcePicker(traceabilityRows));
```

## Source details

The selected source remains highlighted in the coverage list above.

```js
const selected = sourceRows.find((row) => row.source === source);
const selectedState = traceabilityState(selected);
const isTide = source === "tide";
const hasCoordinates = [
  selected?.request_latitude,
  selected?.request_longitude,
  selected?.returned_latitude,
  selected?.returned_longitude
].some((value) => value != null);
```

```js
display(html`
<section class="provenance-source-inspector" data-selected-source=${source}>
  <details class="provenance-details">
    <summary>Technical evidence for ${sourceName(source)}</summary>
    <p>
      ${providerName(source)} · ${traceabilityDetail(selectedState)}
      Missing values are shown explicitly.
    </p>

    <div class="provenance-technical-grid">
      <div>
        <span>Published run identifier</span>
        <code class="provenance-identifier">${latestRun?.run_id ?? "Unavailable"}</code>
      </div>
      <div>
        <span>Source snapshot identifier</span>
        <code class="provenance-identifier" data-provenance-identifier="snapshot">${selected?.snapshot_id ?? "Unavailable"}</code>
      </div>
      <div>
        <span>Snapshot captured</span>
        <strong>${selected?.captured_at
          ? formatTimestamp(selected.captured_at, manifest.display_timezone)
          : "Unavailable"}</strong>
      </div>
      <div>
        <span>Provider</span>
        <strong>${providerName(source)}</strong>
      </div>
      <div>
        <span>${isTide ? "Tide station" : "Provider model"}</span>
        <code class="provenance-identifier">${sourceIdentity(selected) ?? "Unavailable"}</code>
      </div>
    </div>

    ${hasCoordinates ? html`
      <h4>Forecast request and returned grid</h4>
      <div class="provenance-technical-grid">
        <div><span>Requested latitude</span><strong>${formatNumber(selected?.request_latitude, 5)}</strong></div>
        <div><span>Requested longitude</span><strong>${formatNumber(selected?.request_longitude, 5)}</strong></div>
        <div><span>Returned latitude</span><strong>${formatNumber(selected?.returned_latitude, 5)}</strong></div>
        <div><span>Returned longitude</span><strong>${formatNumber(selected?.returned_longitude, 5)}</strong></div>
      </div>
    ` : null}

    ${isTide ? html`
      <h4>Tide prediction relationship</h4>
      <div class="provenance-technical-grid">
        <div><span>Prediction location</span><strong>${selected?.prediction_location ?? "Unavailable"}</strong></div>
        <div><span>Relationship</span><strong>${selected?.relationship_type ?? "Unavailable"}</strong></div>
        <div><span>Coastal relationship</span><strong>${selected?.coastal_relationship ?? "Unavailable"}</strong></div>
        <div><span>Reference station</span><strong>${selected?.reference_station ?? "Unavailable"}</strong></div>
        <div><span>Datum</span><strong>${selected?.datum ?? "Unavailable"}</strong></div>
        <div><span>Distance</span><strong>${formatNumber(selected?.distance_km, 3, "km")}</strong></div>
      </div>
      <div class="provenance-limitation">
        <strong>Known tide limitation</strong>
        <p>${selected?.known_limitation ?? "Unavailable"}</p>
      </div>
    ` : null}
  </details>
</section>
`);
```

## How the forecast is traced

```js
display(html`
<ol class="provenance-lineage" aria-label="Source lineage stages">
  <li data-lineage-stage="provider">
    <span>1</span>
    <div>
      <h3>Provider response</h3>
      <p>Weather, wave, water temperature, and tide data come from their identified providers.</p>
    </div>
  </li>
  <li data-lineage-stage="snapshot">
    <span>2</span>
    <div>
      <h3>Preserved snapshot</h3>
      <p>${traceabilityGaps.length === 0
        ? "Each provider response has an immutable snapshot linked to this published run."
        : `${traceabilityGaps.length} source ${traceabilityGaps.length === 1 ? "has" : "have"} missing or incomplete snapshot evidence.`}</p>
    </div>
  </li>
  <li data-lineage-stage="normalized">
    <span>3</span>
    <div>
      <h3>Forecast records</h3>
      <p>SaltBytes standardizes available values for the selected run and location.</p>
    </div>
  </li>
  <li data-lineage-stage="published">
    <span>4</span>
    <div>
      <h3>Published forecast</h3>
      <p>The dashboard presents the forecast while keeping its supporting evidence available here.</p>
    </div>
  </li>
</ol>
`);
```

<details class="provenance-location-details">
  <summary>Location directions</summary>
  <p>
    These approximate directions describe the selected shoreline and pier.
  </p>
  <div class="provenance-technical-grid">
    <div><span>Direction straight out from shore</span><strong>${directionLabel(locationMetadata?.shore_normal_azimuth_degrees)}</strong></div>
    <div><span>Direction the pier points offshore</span><strong>${directionLabel(locationMetadata?.pier_seaward_azimuth_degrees)}</strong></div>
    <div><span>Reviewed</span><strong>${locationMetadata?.orientation_reviewed_at ?? "Unavailable"}</strong></div>
    <div><span>Review method</span><strong>${orientationMethodLabel(locationMetadata?.orientation_method)}</strong></div>
    <div><span>Review source</span><strong>${orientationSourceLabel(locationMetadata?.orientation_source)}</strong></div>
  </div>
  <div class="provenance-limitation">
    <strong>Direction limitation</strong>
    <p>${orientationLimitationLabel(locationMetadata?.orientation_limitation)}</p>
  </div>
</details>
