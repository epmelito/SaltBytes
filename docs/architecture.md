# Architecture

## Purpose
This document describes the current local weather forecast foundation.
ForecastOps captures forecast snapshots and preserves how those forecasts
change over time.

The current implementation runs locally and uses the same application code
across dev, test, and prod. The
[project charter](project-charter.md) defines the approved future North
Carolina coastal fishing conditions platform, which is not yet implemented.

## High level flow
1. Read the selected environment configuration.
2. Request forecast data from the source API.
3. Run and persist payload quality checks.
4. Stop processing the affected payload when a quality check fails.
5. Write a passing payload as an immutable raw JSON snapshot.
6. Store snapshot metadata and normalized hourly forecast records in DuckDB.
7. Record the final pipeline status.
8. Expose changes between consecutive snapshots through a SQL view.

## Environments

| Environment | Input | Output | Purpose |
|---|---|---|---|
| dev | live API with limited scope | local dev paths | development and debugging |
| test | live API from configuration; fixtures in automated tests | local test paths; temporary paths in tests | local test configuration and repeatable tests |
| prod | live API with full configured scope | local prod paths | production style execution |

The project promotes the same code between environments. It does not maintain separate dev, test, and prod branches.

The YAML configurations do not select input implementations or quality
thresholds. Automated tests replace forecast fetching with fixtures and use
temporary storage in the test harness.

## Main components

### Configuration
Defines the environment name, locations, API endpoint, requested hourly fields,
forecast horizon, storage paths, and logging level.

### Ingestion
Calls the API, runs payload quality checks, and writes a passing payload to
immutable local raw storage.

### Loading
Creates pipeline and forecast records in DuckDB.

### SQL transformations
The `forecast_revision_changes` view compares consecutive snapshots for the
same location and forecast hour.

### Data quality
Checks that the hourly mapping exists, the hourly timestamp list is not empty,
and each configured hourly field has the same number of values as the timestamp
list.

### Operational metadata
Records the run identifier, environment, start time, end time, status, row counts, and failure details.

## Environment promotion
Code moves through this workflow:

feature branch > local dev run > pull request > automated test run > merge to main > manual production style run
