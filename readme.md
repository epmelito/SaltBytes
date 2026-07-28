# ForecastOps

ForecastOps is evolving into a North Carolina coastal fishing conditions data
platform. The current repository implements the local weather forecast
foundation: a configuration-driven pipeline that captures hourly forecasts and
tracks how they change between runs.

The current implementation demonstrates practical data engineering patterns
such as API ingestion, environment configuration, immutable raw storage, SQL
modeling, data quality validation, operational metadata, structured logging,
and automated testing. The [project charter](docs/project-charter.md) defines
the approved future product direction, while the
[roadmap](docs/roadmap.md) and [scope register](docs/scope-register.md)
separate future stages from current capability.

## What the project demonstrates

- ingestion from the Open-Meteo forecast API
- one reusable pipeline across dev, test, and prod
- environment-specific configuration and storage paths
- immutable raw JSON snapshots
- normalized forecast data in DuckDB
- SQL-based forecast revision analysis
- data quality checks before data is published
- pipeline run metadata and failure tracking
- structured operational logging
- automated validation with GitHub Actions

## Architecture

```text
Open-Meteo API
      |
      v
Configuration validation
      |
      v
Forecast ingestion
      |
      v
Payload quality checks
      |
      +----------------------+
      |                      |
      v                      v
Raw JSON snapshots      Quality results
      |                      |
      +----------+-----------+
                 |
                 v
          DuckDB tables
                 |
                 v
      Forecast revision view
```

## Data flow

ForecastOps:

1. loads and validates the selected environment configuration
2. initializes DuckDB and records the running pipeline execution
3. requests hourly forecast data from Open-Meteo for each configured location
4. runs and persists payload quality checks
5. stops the run if a quality check fails
6. writes an immutable raw JSON snapshot for a passing payload
7. stores snapshot metadata and normalized hourly values in DuckDB
8. records the final pipeline status
9. exposes forecast changes between consecutive snapshots through a SQL view

A failed quality check prevents the affected payload from reaching raw snapshot
storage or the normalized forecast tables.

## Environments

The same application code runs in all environments. Configuration controls
locations, API request settings, storage paths, and logging level.

| Environment | Forecast input | Forecast scope | Primary purpose |
| --- | --- | --- | --- |
| dev | Live API | 2 days | Local development and manual validation |
| test | Live API from configuration; fixtures in automated tests | 2 days | Local test configuration and deterministic tests |
| prod | Live API | 7 days | Full local production-style execution |

Automated tests replace forecast fetching with fixed fixtures or controlled
responses and use temporary storage. The configuration files do not select a
fixture input mode.

The prod environment demonstrates environment promotion and production-style
isolation. It is not a deployed cloud production service.

## Repository structure

```text
forecast-ops/
├── .github/
│   └── workflows/
├── config/
│   ├── dev.yml
│   ├── prod.yml
│   └── test.yml
├── docs/
│   ├── decisions/
│   ├── handoffs/
│   ├── architecture.md
│   ├── data-model.md
│   ├── environments.md
│   ├── project-charter.md
│   ├── roadmap.md
│   └── scope-register.md
├── scripts/
├── skills/
│   └── forecast-failure-review/
│       ├── examples/
│       └── SKILL.md
├── src/
│   └── forecast_ops/
├── tests/
│   └── fixtures/
├── AGENTS.md
├── pyproject.toml
└── readme.md
```

## Data model

ForecastOps stores operational and forecast data in DuckDB.

### `pipeline_runs`

Records the outcome of each pipeline execution, including:

- run ID
- environment
- start and completion timestamps
- status
- rows loaded
- error message

### `forecast_snapshots`

Stores metadata for each quality-passing API payload, including:

- snapshot ID
- run ID
- location ID
- capture timestamp
- raw file path

### `forecast_hourly`

Stores normalized hourly forecast values:

- forecast timestamp
- temperature
- precipitation probability
- wind speed
- location ID
- snapshot ID

### `quality_results`

Stores quality-check results for each run. During pipeline execution, location
context is encoded by prefixing `check_name` with the location ID.

### `forecast_revision_changes`

A SQL view compares consecutive snapshots for the same location and forecast
hour. It uses `lag` to calculate changes in:

- temperature
- precipitation probability
- wind speed

The view identifies when and how a forecast changed between pipeline runs.

## Data quality

The pipeline validates each payload before storing a raw snapshot or forecast
records.

Current checks confirm that:

- the hourly mapping exists
- the timestamp list is not empty
- each configured hourly field contains the same number of values as the
  timestamp list

Quality results are persisted in DuckDB for operational review. A failed check
records the run as failed and prevents the invalid payload from reaching raw
snapshot storage or the normalized forecast tables.

## Configuration validation

ForecastOps validates configuration before pipeline execution.

Validation includes:

- supported environment names
- required configuration sections
- HTTPS API endpoints
- supported forecast ranges
- required hourly fields
- valid logging levels
- nonempty location lists
- unique location IDs
- valid latitude and longitude ranges
- required storage paths

This allows configuration errors to fail early with a clear message.

## Logging and run metadata

Pipeline logs include:

- run ID
- environment
- location
- quality check count
- rows loaded
- snapshot count
- success or failure status

Application logging follows the selected environment configuration. Low-level
HTTP client messages are suppressed so output remains focused on pipeline
operations.

Run metadata is also stored in DuckDB, which makes execution history available
after terminal logs are gone.

## Installation

The project requires Python 3.11 or later.

Create and activate a virtual environment, then install the project with its
development dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Running the pipeline

Run the development environment:

```powershell
forecast-ops --environment dev
```

Run the production configuration:

```powershell
forecast-ops --environment prod
```

A successful execution prints the run ID, environment, status, snapshot count,
and loaded row count.

## Manual validation

The current manual validation scripts are hardcoded to `dev`; they do not
accept an environment argument.

Check access to the live API without writing runtime data:

```powershell
python scripts/check_api_connection.py
```

Make a live API request and write a raw development snapshot:

```powershell
python scripts/check_raw_snapshot.py
```

Make a live API request, write a raw development snapshot, and write
development DuckDB records:

```powershell
python scripts/check_database.py
```

Initialize the development database if needed, then read recent revision rows:

```powershell
python scripts/check_forecast_revisions.py
```

## Automated validation

Run the tests:

```powershell
python -m pytest
```

Run static checks:

```powershell
python -m ruff check .
```

GitHub Actions runs both commands for pull requests and pushes to `main`.

The test suite includes:

- configuration loading and validation
- API request behavior
- immutable raw snapshot storage
- DuckDB schema and inserts
- payload quality checks
- pipeline success and failure paths
- fixture-based pipeline execution
- CLI behavior
- logging configuration
- forecast revision calculations

## Current implementation boundary

The current repository is a local weather pipeline. It does not yet implement:

- cloud infrastructure
- scheduled execution
- container deployment
- Airflow or another external orchestrator
- dbt
- dashboards
- automated language model calls

These are current implementation boundaries, not replacements for the product
boundaries and future direction in the project charter.

## Forecast failure review

The repository includes a bounded, diagnostic forecast failure review skill. It
uses available pipeline metadata, quality results, logs, and configuration
evidence to produce a concise review. It does not modify data, rerun pipelines,
change configuration, or make deployment decisions.
