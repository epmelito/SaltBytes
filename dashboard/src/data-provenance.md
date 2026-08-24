---
title: Forecast sources
---

```js
import * as Inputs from "@observablehq/inputs";
import {html} from "npm:htl";

import {
  formatNumber,
  formatTimestamp,
  kilometersToMiles,
  locationName,
  sourceName
} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const provenance = await FileAttachment("./data/provenance.json").json();

const sourceOrder = ["weather", "pressure", "wave", "sst", "tide"];
const expectedSources = sourceOrder.filter((source) =>
  provenance.some((row) => row.source === source)
);

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
    complete: "Available",
    incomplete: "Some details missing",
    missing: "Source record missing"
  }[state];
}

function traceabilityDetail(state) {
  return {
    complete: "Provider details and a saved source record are available.",
    incomplete: "A saved source record is linked, but some source details are missing.",
    missing: "No saved source record is linked to this forecast."
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

function formatCoordinatePair(latitude, longitude) {
  if (latitude === null || latitude === undefined || longitude === null || longitude === undefined) {
    return "Unavailable";
  }
  return `${formatNumber(latitude, 5)}, ${formatNumber(longitude, 5)}`;
}

function tideRelationshipLabel(value) {
  return {
    direct: "NOAA prediction used directly",
    transfer: "Nearby NOAA prediction used for this fishing location"
  }[value] ?? "Unavailable";
}

function waterLevelReferenceLabel(value) {
  if (value === "MLLW") return "Mean Lower Low Water (MLLW)";
  return value ?? "Unavailable";
}

function tideLimitationLabel(value) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  return {
    "Prediction behavior remains distinct from observed water levels":
      "Tide predictions are not observed water levels.",
    "Transfer does not authorize inlet-current interpretation":
      "This tide relationship does not describe inlet currents.",
    "It is not a prediction location at the park destination":
      "The NOAA prediction location is nearby, not at the park itself.",
    "The prediction relationship is materially north of the destination":
      "The NOAA prediction location is north of the fishing location."
  }[value] ?? String(value);
}

const disclosureState = {source: false, location: false};

function preserveDisclosureState(element, key) {
  if (!element) return element;
  element.open = disclosureState[key];
  element.querySelector("summary")?.addEventListener("click", () => {
    disclosureState[key] = !element.open;
  });
  element.addEventListener("toggle", () => {
    disclosureState[key] = element.open;
  });
  return element;
}

function sourcePicker(rows) {
  const picker = html`
    <div class="provenance-source-list" role="group" aria-label="Forecast source details">
      <div class="provenance-source-list-header" aria-hidden="true">
        <span>Source</span>
        <span>Provider</span>
        <span>Source record saved</span>
        <span>Details</span>
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
  See which providers support the latest published forecast. Open any source for
  its saved source record, identifiers, and request details.
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
  <p class="provenance-eyebrow">Source details</p>
  <h2>${traceabilityGaps.length === 0
    ? `Details are available for all ${expectedSources.length} forecast sources`
    : `${traceabilityGaps.length} forecast ${traceabilityGaps.length === 1 ? "source needs" : "sources need"} attention`}</h2>
  <p class="provenance-verdict-summary">
    ${traceabilityGaps.length === 0
      ? `Each source used for ${locationName(locationId, locations)} links to identified source data from the latest successful update.`
      : `${completeSourceCount} of ${expectedSources.length} forecast sources for ${locationName(locationId, locations)} have saved source details.`}
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
      <span>Published update</span>
      <strong>${formatTimestamp(latestRun?.started_at, manifest.display_timezone)}</strong>
    </div>
    <div>
      <span>Forecast window</span>
      <strong>${formatTimestamp(forecastStart, manifest.display_timezone)} to ${formatTimestamp(forecastEnd, manifest.display_timezone)}</strong>
    </div>
    <div>
      <span>Sources with details</span>
      <strong>${completeSourceCount} of ${expectedSources.length}</strong>
    </div>
  </div>
</section>
`);
```

## Source coverage

Select a source to see the details saved for this location and update.

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
const sourceInspector = html`
<section class="provenance-source-inspector" data-selected-source=${source}>
  <details class="provenance-details">
    <summary>${sourceName(source)} source details</summary>
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
        <span>Source record saved</span>
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
      <h4>Forecast grid location</h4>
      <p class="provenance-detail-note">
        SaltBytes sends a coordinate with the request. Open-Meteo returns the
        grid coordinate represented by the forecast.
      </p>
      <div class="provenance-technical-grid">
        <div><span>Point SaltBytes requested</span><strong>${formatCoordinatePair(selected?.request_latitude, selected?.request_longitude)}</strong></div>
        <div><span>Provider grid point returned</span><strong>${formatCoordinatePair(selected?.returned_latitude, selected?.returned_longitude)}</strong></div>
      </div>
    ` : null}

    ${isTide ? html`
      <h4>Tide prediction location</h4>
      <p class="provenance-detail-note">
        NOAA predictions come from the location below. SaltBytes shows how
        that prediction location relates to the selected fishing location.
      </p>
      <div class="provenance-technical-grid">
        <div><span>NOAA prediction location</span><strong>${selected?.prediction_location ?? "Unavailable"}</strong></div>
        <div><span>How the prediction is used</span><strong>${tideRelationshipLabel(selected?.relationship_type)}</strong></div>
        <div><span>How it applies here</span><strong>${selected?.coastal_relationship ?? "Unavailable"}</strong></div>
        <div><span>NOAA reference station</span><strong>${selected?.reference_station ?? "Unavailable"}</strong></div>
        <div><span>Water level reference</span><strong>${waterLevelReferenceLabel(selected?.datum)}</strong></div>
        <div><span>Distance to fishing location</span><strong>${formatNumber(kilometersToMiles(selected?.distance_km), 1, "mi")}</strong></div>
      </div>
      <div class="provenance-limitation">
        <strong>Tide limitation</strong>
        <p>${tideLimitationLabel(selected?.known_limitation)}</p>
      </div>
    ` : null}
  </details>
</section>
`;
preserveDisclosureState(sourceInspector.querySelector(".provenance-details"), "source");
display(sourceInspector);
```

## How source data becomes the forecast

```js
display(html`
<ol class="provenance-lineage" aria-label="Source data stages">
  <li data-lineage-stage="provider">
    <span>1</span>
    <div>
      <h3>Source data</h3>
      <p>${expectedSources.includes("pressure")
        ? "Weather, pressure, wave, water temperature, and tide data come from the providers listed above."
        : "Weather, wave, water temperature, and tide data come from the providers listed above."}</p>
    </div>
  </li>
  <li data-lineage-stage="snapshot">
    <span>2</span>
    <div>
      <h3>Saved source record</h3>
      <p>${traceabilityGaps.length === 0
        ? "Each provider response is saved and linked to this forecast update."
        : `${traceabilityGaps.length} forecast ${traceabilityGaps.length === 1 ? "source has" : "sources have"} missing or incomplete saved source details.`}</p>
    </div>
  </li>
  <li data-lineage-stage="normalized">
    <span>3</span>
    <div>
      <h3>Forecast data</h3>
      <p>SaltBytes standardizes the available values for the selected update and location.</p>
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

```js
const locationDetails = html`<details class="provenance-location-details">
  <summary>Location directions</summary>
  <p>
    These approximate directions describe the selected shoreline and pier.
  </p>
  <div class="provenance-technical-grid">
    <div><span>Direction straight out from shore</span><strong>${directionLabel(locationMetadata?.shore_normal_azimuth_degrees)}</strong></div>
    <div><span>Direction the pier points offshore</span><strong>${directionLabel(locationMetadata?.pier_seaward_azimuth_degrees)}</strong></div>
    <div class="provenance-secondary-detail"><span>Reviewed</span><strong>${locationMetadata?.orientation_reviewed_at ?? "Unavailable"}</strong></div>
    <div class="provenance-secondary-detail"><span>How directions were estimated</span><strong>${orientationMethodLabel(locationMetadata?.orientation_method)}</strong></div>
    <div class="provenance-secondary-detail"><span>Reference imagery</span><strong>${orientationSourceLabel(locationMetadata?.orientation_source)}</strong></div>
  </div>
  <div class="provenance-limitation">
    <strong>Direction note</strong>
    <p>${orientationLimitationLabel(locationMetadata?.orientation_limitation)}</p>
  </div>
</details>`;
preserveDisclosureState(locationDetails, "location");
display(locationDetails);
```
