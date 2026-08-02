---
title: Data provenance
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
const locationRows = provenance.filter((row) => row.location_id === locationId);
const source = view(Inputs.select(
  locationRows.map((row) => row.source),
  {
    label: "Source",
    format: sourceName,
    value: locationRows[0]?.source
  }
));
```

```js
const selected = locationRows.find((row) => row.source === source);
const isTide = source === "tide";
```

# Data provenance

Every public record is derived from metadata persisted with the latest successful
run. Coordinates describe forecast requests and provider grid responses. Tide
values are predictions. None of these fields are observations or measured catch
outcomes.

<div class="metric-grid">
  <div class="metric-card">
    <div class="metric-label">Location</div>
    <div class="metric-value">${locationName(locationId, locations)}</div>
    <div>${selected?.fishing_context ?? "Unavailable"}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Source</div>
    <div class="metric-value">${sourceName(source)}</div>
    <div>${selected?.model_selector ?? "No model selector"}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Snapshot</div>
    <div class="metric-value">${selected?.snapshot_id ?? "Unavailable"}</div>
    <div>${formatTimestamp(selected?.captured_at, manifest.display_timezone)}</div>
  </div>
</div>

## Forecast request and returned grid

<div class="detail-grid">
  <div class="detail-card">
    <div class="detail-label">Request latitude</div>
    <div class="detail-value">${formatNumber(selected?.request_latitude, 5)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Request longitude</div>
    <div class="detail-value">${formatNumber(selected?.request_longitude, 5)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Returned latitude</div>
    <div class="detail-value">${formatNumber(selected?.returned_latitude, 5)}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Returned longitude</div>
    <div class="detail-value">${formatNumber(selected?.returned_longitude, 5)}</div>
  </div>
</div>

## Persisted shoreline orientation

<div class="detail-grid">
  <div class="detail-card">
    <div class="detail-label">Shore normal</div>
    <div class="detail-value">${formatNumber(selected?.shore_normal_azimuth_degrees, 0, "degrees")}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Pier seaward axis</div>
    <div class="detail-value">${formatNumber(selected?.pier_seaward_azimuth_degrees, 0, "degrees")}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Reviewed</div>
    <div class="detail-value">${selected?.orientation_reviewed_at ?? "Unavailable"}</div>
  </div>
</div>

<div class="detail-card">
  <div class="detail-label">Method</div>
  <div class="detail-value">${selected?.orientation_method ?? "Unavailable"}</div>
</div>

<div class="detail-card">
  <div class="detail-label">Source</div>
  <div class="detail-value">${selected?.orientation_source ?? "Unavailable"}</div>
</div>

<div class="notice">
  <strong>Orientation limitation</strong>
  ${selected?.orientation_limitation ?? "Unavailable"}
</div>

## Tide prediction relationship

${isTide ? html`
<div class="detail-grid">
  <div class="detail-card">
    <div class="detail-label">Prediction location</div>
    <div class="detail-value">${selected.prediction_location ?? "Unavailable"}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Station</div>
    <div class="detail-value">${selected.station_id ?? "Unavailable"}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Relationship</div>
    <div class="detail-value">${selected.relationship_type ?? "Unavailable"}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Reference station</div>
    <div class="detail-value">${selected.reference_station ?? "Unavailable"}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Datum</div>
    <div class="detail-value">${selected.datum ?? "Unavailable"}</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">Distance</div>
    <div class="detail-value">${formatNumber(selected.distance_km, 3, "km")}</div>
  </div>
</div>
<div class="detail-card">
  <div class="detail-label">Coastal relationship</div>
  <div class="detail-value">${selected.coastal_relationship ?? "Unavailable"}</div>
</div>
<div class="notice">
  <strong>Known tide limitation</strong>
  ${selected.known_limitation ?? "Unavailable"}
</div>` : html`
<div class="notice">
  Tide relationship metadata is available when the Tide source is selected.
</div>`}

<p class="page-note">
  The public export excludes raw file paths, database paths, credentials,
  connection details, and private storage metadata.
</p>
