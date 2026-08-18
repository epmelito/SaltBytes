# Data model

## Purpose

This document describes the persisted DuckDB model and its integrated hourly
view.

## Persisted entities

### `pipeline_runs`

One row per pipeline execution, including status, timestamps, and run-level
counts.

### `run_locations`

One immutable row per configured location and pipeline run.

Each row preserves the fishing context, reviewed shore normal, optional pier
alignment, review method, source, date, and stated limitation that were active
when the run began. Historical forecasts therefore remain tied to the
orientation used for that run even if the configuration changes later.

### `run_location_solar_context`

One immutable display-coordinate, IANA-timezone, and Astral calculation
provenance record per new run location. Legacy runs have no record and are not
backfilled from current configuration.

### `forecast_snapshots`

Accepted atmospheric, wave, and sea-surface-temperature source responses.

Each snapshot preserves source identity, location identity, request and
returned-coordinate context, raw-file path, and provenance.

### `tide_snapshots`

Accepted NOAA tide responses, including the configured station relationship and
raw-file provenance.

### `source_results`

One outcome per attempted location and source: `success`, `fetch_failed`,
`validation_failed`, or `persistence_failed`. Failed outcomes retain concise
details.

Fetch and validation failures do not create accepted snapshots or normalized
rows, but do not prevent independent source attempts from continuing. A
`persistence_failed` outcome records that accepted environmental data could not
be persisted and the pipeline run fails.

### Fishing observations

`fishing_observation_reports` stores one bounded source-entry content version:
its source, URL, content hash, raw source date and title text, first-retrieval
time, and supported location scope. `fishing_observation_retrievals` records
every retrieval of that unchanged version.

`fishing_observation_assertions` links each deterministic classified statement
to its specific report version, including assertion kind, raw subject wording,
source-supported temporal text, granularity, evidence basis, and assertion
text. Assertions are distinct from review work and preserve only what the
source supports.

`fishing_observation_review_candidates` is separate from factual assertions. It
stores only a version-linked raw segment and deterministic reason when an
otherwise-unclassified segment may be useful for later review. Candidates are
not observations and do not supply assessment input.

`fishing_observation_review_patterns` groups equivalent candidate wording by
source, reason, and raw segment. It holds the optional human disposition and
disposition time. `fishing_observation_review_candidate_patterns` links each
candidate to its pattern, preserving the relationship between a specific report
version and the review decision context.

`fishing_observation_ingestion_attempts` records each source attempt, its
timestamp and `success` or `failed` status, and counts for new,
previously-seen, and outstanding review patterns. These attempts are separate
from environmental `pipeline_runs` and `source_results`.

These entities are independent of pipeline runs and forecast-hour tables. They
do not turn report text into forecast data, normalized species, quantities,
measurements, dispositions, or fishing assessments when the source does not
support those values.

### Normalized hourly tables

- `forecast_hourly` stores atmospheric forecast values
- `wave_hourly` stores wave forecast values
- `sst_hourly` stores sea-surface-temperature values
- `tide_phase_hourly` stores deterministic hourly tide phase
- `cloud_cover_hourly` stores optional source-attributable cloud-cover percent
- `atmospheric_context_hourly` stores optional NBM air temperature and apparent
  temperature
- `pressure_context_hourly` stores optional GFS mean sea level barometric
  pressure with its own source snapshot
- `solar_context_hourly` stores deterministic morning-twilight start and
  evening-twilight end at the civil-twilight boundary (sun six degrees below
  the horizon), sunrise, sunset, solar state, and signed relative solar minutes

Rows use stable location identity and UTC forecast time.

### `tide_events`

NOAA high and low tide predictions used to derive hourly tide phase and
bracketing-extrema context.

### `tide_state_hourly`

A derived DuckDB view that combines each accepted hourly tide-phase row with
the preceding and following extrema from the same snapshot and location.

It exposes:

- previous and next extremum times and types
- previous and next predicted water levels
- minutes since and until the adjacent extrema
- the absolute predicted range between those extrema
- the existing rising or falling phase

Rows remain null for the derived extremum fields when a valid bracketing pair is
not available.

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
- persisted shore normal for the run
- UTC forecast hour
- selected atmospheric values
- selected wave values
- signed wind and wave angles relative to the persisted shore normal
- sea-surface temperature
- tide phase, adjacent extrema timing, and predicted tidal range
- source status and source snapshot provenance for each source family

Failure detail remains in `source_results`; it is not repeated in the hourly
view. Missing normalized values and unavailable bracketing tide context remain
null. The views do not interpolate, carry values forward, round, tolerate, or
generate timestamps.

Cloud cover and NBM atmospheric context are optional. Missing, malformed, null,
nonfinite, or incomplete values remain null and do not change weather
availability or technical eligibility. GFS pressure is independently optional:
its visible source failure leaves pressure unavailable without failing the run
or changing eligibility. Solar values remain null for legacy or unavailable
display context. These values are informational only and do not add fishing
scores, recommendations, or interpretations.

Solar events use the forecast hour's local calendar date in the persisted IANA
timezone. `minutes_from_sunrise` and `minutes_from_sunset` are signed elapsed
minutes between UTC-normalized instants: negative is before the event, zero is
during the event minute, and positive is after the event. `night` is before
`morning_twilight_start` and at or after `evening_twilight_end`;
`morning_twilight` runs from `morning_twilight_start` until sunrise; `daylight`
runs from sunrise until sunset; and `evening_twilight` runs from sunset until
`evening_twilight_end`. The twilight boundaries use civil twilight, when the
sun is six degrees below the horizon.

Site relative angles subtract the persisted seaward shore normal from the
incoming compass direction and normalize the result to `[-180, 180)`. Zero is
directly onshore, negative values are counterclockwise from the shore normal,
positive values are clockwise, and `-180` is directly offshore. Source
direction `360` is equivalent to `0`.

Runs created before `run_locations` existed retain their integrated rows with
null orientation and null site relative angles. A missing weather or wave row
also leaves only that source's derived angle null.

Do not interpolate, carry values forward, substitute sources, or add fishing
scores or recommendations to this integrated view. Scoring remains outside the
integrated and analysis-ready views; this does not prohibit separately approved
product scoring.

## Analysis-ready feature view

`analysis_ready_features_hourly` is a companion DuckDB view over
`coastal_conditions_hourly` at the same `run_id`, `location_id`, and UTC
`forecast_time` grain. It preserves the integrated view's source status and
snapshot provenance.

It adds `weather_available`, `wave_available`, `sst_available`, and
`tide_available`, which require a successful source result plus its normalized
hourly row and required values. `tide_context_available` independently requires
the tide phase and complete adjacent-extrema fields.

`precipitation_6h` and `precipitation_24h` sum the target hour and preceding 5
or 23 exact hourly atmospheric values from the same snapshot. Their matching
`*_complete` fields are true only when every expected timestamp and
precipitation value exists; otherwise totals are null. `technically_eligible`
requires all four source availability fields, both site-relative angles, tide
derived context, and both complete precipitation windows. It expresses input
completeness only, never fishing quality or safety.
