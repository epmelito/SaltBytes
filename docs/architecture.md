# Architecture

## Current system

SaltBytes is a local Python application with pipeline and report commands:

```powershell
saltbytes
saltbytes report conditions
saltbytes report operations
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

The read-only report commands require an explicit report type and select the
latest attempted run by default, or a requested run ID. The text conditions
report renders integrated forecast values across the selected window, while the
text operations report renders selected run metadata and source status. The HTML
conditions report adds forecast charts, and the HTML operations report adds run
history, revisions, source coverage, and provenance. All report outputs convert
UTC timestamps only while formatting.

## Hosted ingestion

GitHub Actions runs the unchanged `saltbytes` command on a hosted runner every
six hours or on manual dispatch from `main`. The workflow uses GitHub OpenID
Connect with Blob data permissions scoped to the `saltbytes-state` container.

Before ingestion, the runner restores only `state/saltbytes.duckdb`; it never
downloads the historical raw archive. It uploads new immutable raw snapshots
under `raw/` before validating and replacing the mutable database blob. A
failed restore, raw upload, database validation, or database upload leaves the
current cloud database canonical. A failed pipeline can still publish its
readable completed failure record when synchronization succeeds, but its nonzero
exit status prevents report generation and Pages deployment.

After successful ingestion and canonical state publication, the workflow builds
a static landing page plus separate conditions and operations reports, uploads
only the generated `site` directory, and deploys it through GitHub Pages. This
publication path has been verified by a successful manual run from `main`.
