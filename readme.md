# ForecastOps
ForecastOps is a configuration driven data pipeline that captures hourly weather forecasts and tracks how those forecasts change between runs.

The project uses a small weather use case to demonstrate practical data engineering patterns such as API ingestion, environment configuration, immutable raw storage, SQL modeling, data quality validation, operational metadata, structured logging, and automated testing.

## What the project demonstrates
- ingestion from the Open Meteo forecast API
- one reusable pipeline across dev, test, and prod
- environment specific configuration and storage paths
- immutable raw JSON snapshots
- normalized forecast data in DuckDB
- SQL based forecast revision analysis
- data quality checks before data is published
- pipeline run metadata and failure tracking
- structured operational logging
- automated validation with GitHub Actions

## Architecture
Open Meteo API
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

## Data flow
For each configured location, ForecastOps:

1. loads and validates the selected environment configuration
2. requests hourly forecast data from Open Meteo
3. validates the structure and record counts in the response
4. writes an immutable raw JSON snapshot
5. stores snapshot metadata in DuckDB
6. normalizes hourly forecast values into relational rows
7. records quality results and pipeline run metadata
8. calculates forecast changes between consecutive snapshots

A failed quality check stops the pipeline before the affected payload is published to the forecast tables.

## Environments
The same application code runs in all environments. Configuration controls the forecast scope, storage paths, database location, and logging level.

| Environment | Forecast source | Forecast scope | Primary purpose |
| --- | --- | --- | --- |
| dev | Live API | 2 days | Local development and manual validation |
| test | Fixed fixtures | 2 days | Deterministic automated testing |
| prod | Live API | 7 days | Full local production style execution |

The prod environment demonstrates environment promotion and production style isolation. It is not a deployed cloud production service.

## Repository structure
forecast-ops/
├── .github/
│   └── workflows/
├── config/
│   ├── dev.yml
│   ├── prod.yml
│   └── test.yml
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   └── environments.md
├── scripts/
├── src/
│   └── forecast_ops/
├── tests/
│   └── fixtures/
├── pyproject.toml
└── readme.md

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
Stores metadata for each captured API response, including:
- snapshot ID
- run ID
- location
- capture timestamp
- raw file path
- source timezone

### `forecast_hourly`
Stores normalized hourly forecast values:
- forecast timestamp
- temperature
- precipitation probability
- wind speed
- location ID
- snapshot ID

### `quality_results`
Stores the result of each quality check for each location and run.

### `forecast_revision_changes`
A SQL view that compares consecutive snapshots for the same location and forecast hour.

It uses `lag` to calculate changes in:
- temperature
- precipitation probability
- wind speed

This gives the SQL transformation a clear operational purpose: identifying when and how a forecast changed between pipeline runs.

## Data quality
The pipeline validates each payload before storing forecast records.

Current checks confirm that:
- the hourly section exists
- the timestamp list is not empty
- each configured hourly field exists
- each hourly field contains the same number of values as the timestamp list

Quality results are persisted in DuckDB for operational review. A failed check records the run as failed and prevents the invalid payload from reaching the normalized forecast tables.

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

This allows configuration errors to fail early with a clear message rather than causing an unclear runtime failure later in the pipeline.

## Logging and run metadata
Pipeline logs include:
- run ID
- environment
- location
- quality check count
- rows loaded
- snapshot count
- success or failure status

Application logging follows the selected environment configuration. Low level HTTP client messages are suppressed so the output remains focused on pipeline operations.

Run metadata is also stored in DuckDB, which makes execution history available after terminal logs are gone.

## Installation
The project requires Python 3.11 or later.

Create and activate a virtual environment, then install the project with its development dependencies:
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

## Running the pipeline
Run the development environment:
forecast-ops --environment dev

Run the production configuration:
forecast-ops --environment prod

A successful execution prints the run ID, environment, status, snapshot count, and loaded row count.

## Manual validation
Check access to the live API:
python scripts/check_api_connection.py


Inspect a raw snapshot:
python scripts/check_raw_snapshot.py


Inspect the DuckDB data:
python scripts/check_database.py --environment dev


Review forecast revision rows:
python scripts/check_forecast_revisions.py --environment dev


Replace `dev` with `prod` to inspect the production data paths.

## Automated validation
Run the tests:
python -m pytest

Run static checks:
python -m ruff check .

GitHub Actions runs both commands for pull requests and pushes to `main`.

The test suite includes:
- configuration loading and validation
- API request behavior
- immutable raw snapshot storage
- DuckDB schema and inserts
- payload quality checks
- pipeline success and failure paths
- fixture based pipeline execution
- CLI behavior
- logging configuration
- forecast revision calculations

## Current scope
The current version is a local pipeline MVP. It intentionally excludes:

- cloud infrastructure
- scheduled execution
- container deployment
- Airflow or another external orchestrator
- dbt
- dashboards
- automated language model calls

These exclusions keep the first version focused on the core pipeline, operational design, test coverage, and promotion workflow.

## Planned extension
A later extension will add a bounded AI assisted failure review skill.

The skill will use pipeline metadata, failed quality results, and structured logs to produce a concise run summary. It will not modify data, rerun pipelines, or make deployment decisions.