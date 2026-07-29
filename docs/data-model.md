# Data model

ForecastOps stores run metadata, source-specific snapshot provenance,
normalized atmospheric and wave forecasts, and quality results in DuckDB.

The implementation retains five tables:

- `pipeline_runs`
- `forecast_snapshots`
- `forecast_hourly`
- `wave_hourly`
- `quality_results`

Existing local databases are upgraded idempotently by adding nullable columns,
creating the wave table, and recreating affected revision views. Existing rows
are preserved.

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

The seven provenance columns are nullable so legacy rows remain valid. New
coastal snapshot inserts provide all seven values.

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

## Relationships

- One pipeline run can produce multiple snapshots and quality results.
- One passing snapshot produces atmospheric or wave normalized hourly rows.
- A rejected source result produces quality results but no snapshot or
  normalized rows for that source.
- A failed run may retain successful results from the other source and
  unrelated locations, together with its actual loaded-row count.
