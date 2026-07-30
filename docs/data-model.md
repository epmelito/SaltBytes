# Data model

## Purpose

This document describes the persisted DuckDB model and its integrated hourly
view.

## Persisted entities

### `pipeline_runs`

One row per pipeline execution, including status, timestamps, and run-level
counts.

### `forecast_snapshots`

Accepted atmospheric, wave, and sea-surface-temperature source responses.

Each snapshot preserves source identity, location identity, request and
returned-coordinate context, raw-file path, and provenance.

### `tide_snapshots`

Accepted NOAA tide responses, including the configured station relationship and
raw-file provenance.

### `source_results`

One outcome per attempted location and source: `success`, `fetch_failed`, or
`validation_failed`. Failed outcomes retain concise details.

Fetch and validation failures do not create accepted snapshots or normalized
rows, but do not prevent independent source attempts from continuing.

### Normalized hourly tables

- `forecast_hourly` stores atmospheric forecast values
- `wave_hourly` stores wave forecast values
- `sst_hourly` stores sea-surface-temperature values
- `tide_phase_hourly` stores deterministic hourly tide phase

Rows use stable location identity and UTC forecast time.

### `tide_events`

NOAA high and low tide predictions used to derive hourly tide phase.

## Relationships

```text
pipeline_runs
    ↓
accepted source snapshots
    ↓
normalized source rows

stable location identity
    ↓
all normalized source tables
```

Normalized rows retain the snapshot that produced them.

Source-specific coordinates and NOAA station identifiers are provenance and
configuration details. Cross-source integration should use the stable location
identifier rather than comparing raw coordinates.

## Integrated hourly view

```text
coastal_conditions_hourly
```

`coastal_conditions_hourly` is a DuckDB view at grain `run_id`, `location_id`,
and UTC `forecast_time`. Its spine is the distinct union of normalized weather,
wave, SST, and tide-phase keys. It joins each source only on that exact grain,
so it retains all runs without cross-run mixing or latest-snapshot selection.

It includes:

- location identifier
- UTC forecast hour
- selected atmospheric values
- selected wave values
- sea-surface temperature
- tide phase
- source status and source snapshot provenance for each source family

Failure detail remains in `source_results`; it is not repeated in the hourly
view. Missing normalized values remain null. The view does not interpolate,
round, tolerate, or generate timestamps.

Do not interpolate, carry values forward, substitute sources, or add fishing
scores or recommendations in the MVP.
