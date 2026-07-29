# Data model

ForecastOps stores run metadata, source-specific snapshot provenance,
normalized atmospheric, wave, sea-surface-temperature, and tide data, and
quality results in DuckDB.

The implementation retains nine tables:

- `pipeline_runs`
- `forecast_snapshots`
- `forecast_hourly`
- `wave_hourly`
- `sst_hourly`
- `tide_snapshots`
- `tide_events`
- `tide_phase_hourly`
- `quality_results`

Existing local databases are upgraded idempotently by adding nullable columns,
creating missing wave, SST, and tide tables, and recreating affected revision
views. Existing rows are preserved.

## `pipeline_runs`

| Column | Purpose |
| --- | --- |
| `run_id` | Unique pipeline-run identifier |
| `environment` | Selected local environment |
| `started_at` | Run start timestamp |
| `completed_at` | Run completion timestamp |
| `status` | Running, success, or failed state |
| `rows_loaded` | Actual normalized rows loaded |
| `error_message` | Failure details |

## `forecast_snapshots`

One row describes each quality-passing raw response.

| Column | Purpose |
| --- | --- |
| `snapshot_id` | Unique captured-response identifier |
| `run_id` | Pipeline run that captured the response |
| `location_id` | Stable configured location identifier |
| `captured_at` | UTC capture timestamp |
| `raw_file_path` | Path to the immutable raw JSON |
| `model_selector` | Configured request model |
| `request_latitude` | Configured source-request latitude |
| `request_longitude` | Configured source-request longitude |
| `returned_latitude` | Latitude returned by the source |
| `returned_longitude` | Longitude returned by the source |
| `response_timezone` | Source response timezone |
| `response_utc_offset_seconds` | Source response UTC offset |

The seven Open-Meteo provenance columns are nullable so legacy and NOAA tide
rows remain valid. New Open-Meteo snapshot inserts provide all seven values;
NOAA-specific provenance remains in `tide_snapshots`.

## `forecast_hourly`

One passing seven-day result produces 168 rows.

| Column | Purpose |
| --- | --- |
| `snapshot_id` | Snapshot that produced the row |
| `location_id` | Stable configured location identifier |
| `forecast_time` | Forecast valid time normalized to UTC |
| `wind_speed_10m` | Ten-metre wind speed |
| `wind_direction_10m` | Ten-metre wind direction |
| `wind_gusts_10m` | Ten-metre wind gust |
| `precipitation_probability` | Precipitation probability |
| `precipitation` | Precipitation amount |
| `temperature_2m` | Nullable legacy compatibility column; not populated by new coastal loads |

The business key is:

`snapshot_id + location_id + forecast_time`

## `quality_results`

| Column | Purpose |
| --- | --- |
| `run_id` | Run being checked |
| `check_name` | Location- and source-qualified quality-check name |
| `status` | Pass or fail |
| `observed_value` | Observed result |
| `expected_value` | Expected contract |
| `checked_at` | UTC check timestamp |

Passing and failing source results both retain their quality evidence.

## `wave_hourly`

One passing seven-day wave result produces 168 rows.

| Column | Purpose |
| --- | --- |
| `snapshot_id` | Wave snapshot that produced the row |
| `location_id` | Stable configured location identifier |
| `forecast_time` | Forecast valid time normalized to UTC |
| `wave_height` | Wave height |
| `wave_direction` | Wave direction |
| `wave_period` | Wave period |

The business key is:

`snapshot_id + location_id + forecast_time`

## `sst_hourly`

One passing seven-day SST result produces 168 rows.

| Column | Purpose |
| --- | --- |
| `snapshot_id` | SST snapshot that produced the row |
| `location_id` | Stable configured location identifier |
| `forecast_time` | Forecast valid time normalized to UTC |
| `sea_surface_temperature` | Sea-surface temperature |

The business key is:

`snapshot_id + location_id + forecast_time`

## `tide_snapshots`

One row retains the NOAA request and accepted relationship provenance for a
passing tide snapshot.

| Column group | Purpose |
| --- | --- |
| `snapshot_id` | Links to the immutable raw response and capture metadata |
| Station and request fields | NOAA identifier, product, interval, datum, time zone, units, response format, and request window |
| Relationship fields | Prediction location, direct or transfer classification, reference station, published offsets and multipliers, distance, coastal relationship, and limitation |

## `tide_events`

One row stores each quality-passing NOAA high or low event.

| Column | Purpose |
| --- | --- |
| `snapshot_id` | Tide snapshot that produced the event |
| `location_id` | Stable configured location identifier |
| `event_time` | NOAA GMT event time normalized to UTC |
| `event_type` | `high` or `low` |
| `predicted_water_level` | NOAA predicted water level in metres relative to `MLLW` |

## `tide_phase_hourly`

One passing tide result produces exactly 168 hourly rows.

| Column | Purpose |
| --- | --- |
| `snapshot_id` | Tide snapshot whose events produced the phase |
| `location_id` | Stable configured location identifier |
| `forecast_time` | Hourly valid time in UTC |
| `phase` | Accepted binary `rising` or `falling` phase |

## `forecast_revision_changes`

The view matches consecutive snapshots by stable `location_id` and normalized
`forecast_time`.

It exposes current and previous values for:

- `wind_speed_10m`
- `wind_direction_10m`
- `wind_gusts_10m`
- `precipitation_probability`
- `precipitation`

It calculates differences for every listed scalar field except wind direction.
No directional-delta semantics are defined.

## `wave_revision_changes`

The view matches consecutive `meteofrance_wave` snapshots by stable
`location_id` and normalized `forecast_time`.

It exposes current and previous values for wave height, direction, and period.
Height and period include differences. Wave direction does not.

## `sst_revision_changes`

The view matches consecutive `meteofrance_currents` snapshots by stable
`location_id` and normalized `forecast_time`.

It exposes current and previous sea-surface-temperature values and their scalar
difference.

## `tide_revision_changes`

The view matches consecutive tide snapshots by stable `location_id`, NOAA
identifier, product, datum, and normalized `forecast_time`. It exposes current
and previous binary phases without defining a numeric phase delta.

## Relationships

- One pipeline run can produce multiple snapshots and quality results.
- One passing Open-Meteo snapshot produces atmospheric, wave, or SST normalized
  hourly rows.
- One passing tide snapshot has NOAA relationship provenance, normalized high
  and low events, and 168 hourly binary phase rows.
- A rejected source result produces quality results but no snapshot or
  normalized rows for that source.
- A failed run may retain successful results from other sources and unrelated
  locations, together with its actual loaded-row count.
