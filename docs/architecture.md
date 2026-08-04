# Architecture

## Current system

SaltBytes is a Python application with pipeline, report, and dashboard export
commands:

```powershell
saltbytes
saltbytes report conditions
saltbytes report operations
saltbytes dashboard export --output dashboard/src/data
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

The reporting layer adds:

```text
normalized DuckDB tables
    ↓
coastal_conditions_hourly view
    ├─→ deterministic text and HTML reports
    └─→ curated public JSON
            ↓
        Observable Framework build
            ↓
        static interactive dashboard
```

Python owns DuckDB access and the public export boundary. The browser receives
only generated JSON and static assets. It does not query DuckDB, Azure Blob
Storage, authenticated APIs, or a running application server.

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

## Reporting boundary

The integrated view remains downstream from ingestion. It uses the distinct
union of normalized source keys and exact run, location, and UTC-hour joins.

Do not redesign the ingestion control flow unless live validation proves a
change is required.

The read-only report commands require an explicit report type and select the
latest attempted run by default, or a requested run ID. The text conditions
report renders integrated forecast values across the selected window, while the
text operations report renders selected run metadata and source status. The HTML
conditions report adds forecast charts, and the HTML operations report adds run
history, revisions, source coverage, and provenance. All report outputs convert
UTC timestamps only while formatting.

The dashboard export opens DuckDB read only, validates the reporting schema, and
writes seven documented JSON files. Current conditions come from the latest
successful run, while monitoring retains recent failed and partial attempts.
Raw paths, credentials, connection details, and private storage metadata are not
part of the export contract.

The isolated `dashboard/` project contains deterministic fixture data for local
and pull request builds. Hosted publication replaces those fixtures with a fresh
curated export before building the static dashboard.

## Hosted ingestion

Hosted ingestion preserves canonical state before publication and keeps the
previous site available when publication fails. It builds reports and the
dashboard only after successful canonical publication. See
[hosted operation](hosted-operation.md) for setup, recovery, run, and
publication procedures.
