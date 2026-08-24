# Architecture

## Current system

SaltBytes is a Python application with pipeline, report, and dashboard export
commands:

```powershell
saltbytes
saltbytes report conditions
saltbytes report operations
saltbytes dashboard export --output dashboard/src/data
saltbytes observations ingest-current
saltbytes observations review-candidates
```

The pipeline:

1. loads the local YAML configuration
2. requests atmospheric, wave, sea-surface-temperature, and NOAA tide data
3. validates each source result
4. stores accepted raw responses as immutable JSON
5. normalizes accepted data into DuckDB
6. records run, source-result, request, and provenance metadata
7. exposes the downstream `coastal_conditions_hourly` view

Fishing observation ingestion is a separate data domain. It retrieves approved
fishing reports, preserves versioned report and retrieval provenance, and
derives only deterministic factual assertions supported by a report. Segments
selected as potentially useful by deterministic candidate logic become review
candidates rather than assertions; their persistent patterns and human review
dispositions support later parser review.

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

Fishing observations follow a separate path:

```text
approved fishing report sources
    ↓
source-specific retrieval and parsing
    ↓
versioned reports, retrievals, and factual assertions
    └─→ review candidates and persistent review patterns
            ↓
        separate manual review workflow
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

Each forecast source is processed independently for each configured location.

A rejected source result records an outcome but does not write an
accepted snapshot or normalized rows for that result. Unrelated sources and
locations continue processing.

Required forecast-source fetch and validation failures are isolated. A required
source persistence failure is recorded as `persistence_failed` and aborts the
pipeline run because canonical environmental state cannot be completed safely.
Supplemental GFS pressure persistence failure is recorded but does not abort an
otherwise valid run; pressure remains unavailable for that run.

Fishing observation sources are isolated from forecast ingestion and from each
other. A fetch, parse, or observation-persistence failure preserves existing
observation history and records a failed source attempt when possible; it does
not prevent another observation source or an otherwise valid forecast canonical
publication. New review candidates are normal source evolution, not failures.

## Configuration

`config/local.yml` defines local storage paths, logging, locations, source
coordinates, NOAA station relationships, and the report display timezone. Fixed
provider contracts are kept in the source clients.

Source relationship details remain in configuration and accepted ADRs. They
should be loaded only when a task changes those contracts.

## Storage

Accepted raw responses are written unchanged as immutable JSON snapshots.

DuckDB stores pipeline runs, accepted source snapshots, source results,
normalized source rows, tide events, hourly tide phase, and the separate fishing
observation domain: reports, retrievals, assertions, review candidates and
patterns, candidate-pattern links, dispositions, and ingestion attempts.

See [data-model.md](data-model.md) for the persisted model.

## Reporting boundary

NBM remains the required weather source. GFS pressure is separately retained
supplemental context: its failures are recorded without failing an otherwise
successful pipeline run. See [ADR 0015](decisions/0015-supplemental-gfs-pressure-context.md).

The integrated view remains downstream from ingestion. It uses the distinct
union of normalized source keys and exact run, location, and UTC-hour joins.

Do not redesign the ingestion control flow unless live validation proves a
change is required.

The read-only report commands require an explicit report type and select the
latest attempted run by default, or a requested run ID. The text conditions
report renders integrated forecast values across the selected window, while the
text operations report renders selected run metadata and source status. The HTML
conditions report adds forecast charts, and the HTML operations report adds run
history, revisions, source coverage, and provenance. Report outputs convert
UTC timestamps and user-facing physical measurements only while formatting;
stored forecast values and assessment calculations remain metric.

The dashboard export opens DuckDB read only, validates the reporting schema, and
writes seven documented JSON files. Current conditions come from the latest
successful run, while monitoring retains recent failed and partial attempts.
Raw paths, credentials, connection details, and private storage metadata are not
part of the export contract.

The isolated `dashboard/` project contains compact deterministic fixture data
for local and pull request correctness checks. When presentation depends on data
volume, a frozen representative dataset can temporarily replace those fixtures
for visual review and browser checks. That preview data is independent of hosted
state and must be restored after review. Hosted publication replaces local
dashboard data with a fresh curated export before building the static dashboard.

## Hosted ingestion

Hosted ingestion restores, updates, validates, and publishes canonical state;
it runs environmental ingestion and independent fishing observation ingestion
before publication. It preserves canonical state before publication and keeps
the previous site available when publication fails. It builds reports and the
dashboard only after successful canonical publication.

The only authorized canonical-state writers are the hosted ingestion workflow
and the manual fishing observation review workflow. They share the
`saltbytes-hosted-ingestion` GitHub Actions concurrency group with cancellation
disabled, which serializes canonical writes. Manual review takes a pattern ID
and an approved disposition, restores the latest canonical database, applies
and validates the decision, and publishes only on success.

See [hosted operation](hosted-operation.md) for setup, recovery, run, and
publication procedures.
