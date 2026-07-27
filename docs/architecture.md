# Architecture

## Purpose
ForecastOps captures weather forecast snapshots and preserves how those forecasts change over time.

The minimum viable product (MVP) runs locally and uses the same application code across dev, test, and prod. Each environment changes configuration, input source, output path, and validation behavior.

## High level flow
1. Read the selected environment configuration.
2. Request forecast data from the source API.
3. Store the raw response without modification.
4. Normalize hourly forecast records.
5. Load pipeline metadata and forecast data into DuckDB.
6. Run SQL transformations and data quality checks.
7. Record the final pipeline status.

## Environments

| Environment | Input | Output | Purpose |
|---|---|---|---|
| dev | live API with limited scope | local dev paths | development and debugging |
| test | fixed JSON fixtures | temporary test database | repeatable automated testing |
| prod | live API with full configured scope | local prod paths | production style execution |

The project promotes the same code between environments. It does not maintain separate dev, test, and prod branches.

## Main components

### Configuration
Defines locations, requested forecast fields, forecast horizon, and environment specific paths.

### Ingestion
Calls the API, validates the response, and writes the raw payload to local storage.

### Loading
Creates pipeline and forecast records in DuckDB.

### SQL transformations
Builds current forecast views, previous snapshot comparisons, and pipeline summaries.

### Data quality
Checks required fields, duplicate keys, expected locations, timestamps, and minimum row counts.

### Operational metadata
Records the run identifier, environment, start time, end time, status, row counts, and failure details.

## Environment promotion
Code moves through this workflow:

feature branch > local dev run > pull request > automated test run > merge to main > manual production style run