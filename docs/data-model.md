# Data model

## Purpose

This document describes the persisted DuckDB model and the intended integrated
MVP result.

## Persisted entities

### `pipeline_runs`

One row per pipeline execution, including environment, status, timestamps, and
run-level counts.

### `forecast_snapshots`

Accepted atmospheric, wave, and sea-surface-temperature source responses.

Each snapshot preserves source identity, location identity, request and
returned-coordinate context, raw-file path, and provenance.

### `tide_snapshots`

Accepted NOAA tide responses, including the configured station relationship and
raw-file provenance.

### `quality_results`

Validation evidence for source attempts, including accepted and rejected
results.

Rejected results do not create accepted snapshots or normalized rows.

### Normalized hourly tables

- `forecast_hourly` stores atmospheric forecast values
- `wave_hourly` stores wave forecast values
- `sst_hourly` stores sea-surface-temperature values
- `tide_phase_hourly` stores deterministic hourly tide phase

Rows use stable location identity and UTC forecast time.

### `tide_events`

NOAA high and low tide predictions used to derive hourly tide phase.

### Revision views

Existing views expose changes in forecast values between accepted snapshots.
Revision analysis remains available but is not required in the first MVP output.

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

## Integrated MVP result

Create one downstream hourly result, provisionally named:

```text
coastal_conditions_hourly
```

It should include:

- location identifier
- location name
- fishing context
- UTC forecast hour
- selected atmospheric values
- selected wave values
- sea-surface temperature
- tide phase
- enough availability or quality context to explain missing values

Use atmospheric forecast hours as the initial time spine unless live validation
shows that this creates an incorrect result.

Join wave, SST, and tide phase by stable location identity and UTC forecast hour.
Use left joins so unavailable or rejected sources remain visible as null values.

Do not interpolate, carry values forward, substitute sources, or add fishing
scores or recommendations in the MVP.