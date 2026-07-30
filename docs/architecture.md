# Architecture

## Current system

ForecastOps is a local Python application with one supported pipeline command:

```powershell
forecast-ops
```

The pipeline:

1. loads the local YAML configuration
2. requests atmospheric, wave, sea-surface-temperature, and NOAA tide data
3. validates each source result
4. stores accepted raw responses as immutable JSON
5. normalizes accepted data into DuckDB
6. records run, quality, request, and provenance metadata

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
integrated hourly coastal-conditions result
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
coordinates, and NOAA station relationships. Fixed provider contracts are kept
in the source clients.

Source relationship details remain in configuration and accepted ADRs. They
should be loaded only when a task changes those contracts.

## Storage

Accepted raw responses are written unchanged as immutable JSON snapshots.

DuckDB stores pipeline runs, accepted source snapshots, source results,
normalized source rows, tide events, and hourly tide phase.

See [data-model.md](data-model.md) for the persisted model.

## MVP extension boundary

The integrated result should remain downstream from the existing ingestion
pipeline. It should use existing normalized tables, stable location identity,
and UTC forecast hours.

Do not redesign the ingestion control flow unless live validation proves a
change is required.
