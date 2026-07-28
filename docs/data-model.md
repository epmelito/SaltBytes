# Data model
ForecastOps stores pipeline metadata, raw forecast snapshots, normalized hourly forecasts, and data quality results in DuckDB.

The first release uses four core tables:
- `pipeline_runs`
- `forecast_snapshots`
- `forecast_hourly`
- `quality_results`

## pipeline_runs
Stores one record for each pipeline execution.

| Column | Purpose |
|---|---|
| `run_id` | Unique identifier for the pipeline run |
| `environment` | Selected environment: dev, test, or prod |
| `started_at` | Pipeline start timestamp |
| `completed_at` | Pipeline completion timestamp |
| `status` | Final run status |
| `rows_loaded` | Number of normalized forecast rows loaded |
| `error_message` | Failure details when the run does not complete |

## forecast_snapshots
Stores metadata for each quality-passing API payload captured by the pipeline.

| Column | Purpose |
|---|---|
| `snapshot_id` | Unique identifier for the captured response |
| `run_id` | Pipeline run that created the snapshot |
| `location_id` | Configured location identifier |
| `captured_at` | Timestamp when the API response was received |
| `raw_file_path` | Local path to the preserved raw response |

## forecast_hourly
Stores normalized hourly forecast records.

| Column | Purpose |
|---|---|
| `snapshot_id` | Snapshot that produced the record |
| `location_id` | Configured location identifier |
| `forecast_time` | Timestamp the forecast applies to |
| `temperature_2m` | Forecast air temperature |
| `precipitation_probability` | Forecast probability of precipitation |
| `wind_speed_10m` | Forecast wind speed |

Expected business key:
`snapshot_id + location_id + forecast_time`

## quality_results
Stores the outcome of each data quality check.

The table does not have a separate location column. During pipeline execution,
the location ID is prefixed to `check_name`.

| Column | Purpose |
|---|---|
| `run_id` | Pipeline run being checked |
| `check_name` | Name of the validation |
| `status` | Pass or fail |
| `observed_value` | Value returned by the check |
| `expected_value` | Expected value or threshold |
| `checked_at` | Timestamp when the check ran |

## Relationships
- One pipeline run can create multiple forecast snapshots.
- One forecast snapshot can contain multiple hourly forecast records.
- One pipeline run can produce multiple data quality results.

## Current assumptions
- Each payload that passes pipeline quality checks produces one snapshot for
  its configured location.
- Hourly forecast timestamps are unique within a snapshot and location.
- Passing payload snapshots are preserved outside DuckDB and referenced by
  path.
- The first release does not model daily forecasts or historical observations.
