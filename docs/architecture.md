# Architecture

## Current system

ForecastOps is a local Python application with pipeline and report commands:

```powershell
forecast-ops
forecast-ops report
```

The pipeline:

1. loads the local YAML configuration
2. requests atmospheric, wave, sea-surface-temperature, and NOAA tide data
3. validates each source result
4. stores accepted raw responses as immutable JSON
5. normalizes accepted data into DuckDB
6. records run, source-result, request, and provenance metadata
7. exposes the downstream `coastal_conditions_hourly` view

## Data flow

```text
YAML configuration
    ↓
source clients
    ↓
source-specific validation
    ↓
immutable raw JSON
    ↓
normalized DuckDB tables
```

The MVP adds:

```text
normalized DuckDB tables
    ↓
coastal_conditions_hourly view
    ↓
readable local output
```

## Source and failure boundaries

Each source is processed independently for each configured location.

A rejected source result records an outcome but does not write an
accepted snapshot or normalized rows for that result. Unrelated sources and
locations continue processing.

Operational failures such as storage or database errors abort the run.

## Configuration

`config/local.yml` defines local storage paths, logging, locations, source
coordinates, NOAA station relationships, and the report display timezone. Fixed
provider contracts are kept in the source clients.

Source relationship details remain in configuration and accepted ADRs. They
should be loaded only when a task changes those contracts.

## Storage

Accepted raw responses are written unchanged as immutable JSON snapshots.

DuckDB stores pipeline runs, accepted source snapshots, source results,
normalized source rows, tide events, and hourly tide phase.

See [data-model.md](data-model.md) for the persisted model.

## MVP extension boundary

The integrated view remains downstream from ingestion. It uses the distinct
union of normalized source keys and exact run, location, and UTC-hour joins.

Do not redesign the ingestion control flow unless live validation proves a
change is required.

The read-only `forecast-ops report` command selects the latest attempted run by
default, or a requested run ID. It renders the integrated hourly view and
source-result failures for the configured locations; it converts UTC timestamps
only while formatting output.
