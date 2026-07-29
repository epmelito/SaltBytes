# ForecastOps

ForecastOps is evolving into a North Carolina coastal fishing conditions data
platform. The current repository implements local atmospheric, wave, and
sea-surface-temperature forecast ingestion for five approved coastal fishing
locations.

The implementation demonstrates configuration-driven API ingestion, spatial
source relationships, immutable raw storage, normalized DuckDB models,
forecast revision history, deterministic data quality checks, run metadata,
structured logging, and automated testing. The
[project charter](docs/project-charter.md) defines the durable product
direction. The [roadmap](docs/roadmap.md) and
[scope register](docs/scope-register.md) distinguish current implementation
from approved future and deferred work.

## Current source scope

Every environment configures:

- Jennette's Pier
- Beach Access Ramp 72, Ocracoke Island
- Fort Macon State Park, ocean side
- Bogue Inlet Pier
- Fort Fisher State Recreation Area

Each location retains a display coordinate, source-specific request and
expected returned grid coordinates, its fishing context, and a static
coastal-regime classification.

The Open-Meteo Weather API request uses:

- model selector `ncep_nbm_conus`
- seven forecast days
- `timezone=auto`
- `wind_speed_10m`
- `wind_direction_10m`
- `wind_gusts_10m`
- `precipitation_probability`
- `precipitation`

The Open-Meteo Marine API request uses:

- model selector `meteofrance_wave`
- seven forecast days
- `timezone=auto`
- `wave_height`
- `wave_direction`
- `wave_period`

A separate Open-Meteo Marine API request uses:

- model selector `meteofrance_currents`
- seven forecast days
- `timezone=auto`
- `sea_surface_temperature` only

Ocean-current, sea-level-height, and tide ingestion are not implemented.

## Data flow

1. Load and validate the selected local environment configuration.
2. Initialize DuckDB and record the running pipeline execution.
3. Request independent atmospheric, wave, and SST results for each configured
   location.
4. Validate and persist source-qualified quality checks for each result.
5. Reject an invalid source result without writing its raw or normalized data.
6. Continue after a quality rejection so the other sources and later locations
   can succeed.
7. Write each passing response unchanged as a separate immutable raw JSON
   snapshot.
8. Store source-specific request and response provenance with each snapshot.
9. Normalize 168 hourly valid times to UTC and store atmospheric, wave, and SST
   values in separate DuckDB tables.
10. Record the final run status and actual number of rows loaded.
11. Expose atmospheric, wave, and SST forecast changes through separate SQL
    views.

API, raw-storage, and database failures abort the run immediately. If one or
more source results fail quality validation, the run is failed after all
locations have been evaluated. Passing results from other sources and unrelated
locations remain stored.

## Repository structure

```text
forecast-ops/
|-- .github/workflows/
|-- config/
|-- docs/
|   |-- decisions/
|   |-- handoffs/
|   |-- requirements/
|   `-- research/
|-- scripts/
|-- skills/forecast-failure-review/
|-- src/forecast_ops/
|-- tests/
|-- AGENTS.md
|-- pyproject.toml
`-- readme.md
```

## Data model

ForecastOps uses six DuckDB tables:

- `pipeline_runs` records execution status, row counts, and failure details.
- `forecast_snapshots` relates passing raw responses to their run, location,
  request provenance, returned coordinates, and response timezone metadata.
- `forecast_hourly` stores normalized UTC forecast rows for the five
  atmospheric fields. Its nullable `temperature_2m` column is retained only
  for compatibility with existing local history.
- `wave_hourly` stores normalized UTC wave height, direction, and period.
- `sst_hourly` stores normalized UTC sea-surface temperature.
- `quality_results` stores location- and source-qualified validation results.

The `forecast_revision_changes` view compares consecutive snapshots for the
same stable location and normalized forecast time. It provides current,
previous, and difference values for scalar atmospheric fields. Wind direction
retains current and previous values without defining a directional delta.

The `wave_revision_changes` view provides equivalent revision history for wave
height, direction, and period. Wave direction also has no directional delta.

The `sst_revision_changes` view compares consecutive
`meteofrance_currents` captures and exposes current, previous, and scalar
sea-surface-temperature changes.

See [Data model](docs/data-model.md) for the column-level contract.

## Data quality

Before raw or normalized storage, the pipeline checks:

- usable SST request and expected returned relationships and a nonempty static
  coastal regime before requesting SST
- configured model selector
- returned coordinate equality against the configured expected grid
- recognized response timezone
- parseable valid times and UTC normalization
- exactly 168 unique, strictly ascending UTC instants
- exactly one hour between consecutive UTC instants
- presence, length, null status, and numeric values for every required field

Coordinate comparison uses parsed numeric equality. No tolerance, fallback
coordinate, or replacement model is implemented.

## Environments

The same application code and atmospheric, wave, and SST contracts run in
`dev`, `test`, and `prod`. These are local configurations, not deployed cloud
environments. Configuration varies only in storage paths and logging level.

Automated tests replace live forecast fetching with deterministic responses and
use temporary storage. The YAML configurations do not select a fixture mode.

See [Environments](docs/environments.md) for details.

## Installation

The project requires Python 3.11 or later.

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

Run the production-style local configuration:

```powershell
forecast-ops --environment prod
```

A fully passing run writes 15 snapshots and 2,520 normalized rows: 840 each for
atmospheric, wave, and SST results.

## Manual validation

The manual scripts are hardcoded to `dev`; they do not accept an environment
argument.

Check the live API without writing runtime data:

```powershell
python scripts/check_api_connection.py
```

Make a live request and write a raw development snapshot:

```powershell
python scripts/check_raw_snapshot.py
```

Make a live request, write a raw snapshot, and insert development DuckDB
records:

```powershell
python scripts/check_database.py
```

Read recent development revision rows:

```powershell
python scripts/check_forecast_revisions.py
```

## Automated validation

```powershell
python -m pytest
python -m ruff check .
```

GitHub Actions runs both commands for pull requests and pushes to `main`.

## Current implementation boundary

The repository does not currently implement:

- ocean-current, sea-level-height, or tide ingestion
- fishing-condition scoring or window ranking
- scheduled or cloud execution
- publication, API, or dashboard features
- Azure infrastructure
- automated model or agent product behavior

These implementation boundaries do not replace the product boundaries and
approved future direction in the project charter.

## Forecast failure review

The repository includes a bounded diagnostic forecast-failure review skill. It
uses pipeline metadata, quality results, logs, and configuration evidence. It
does not modify data, rerun pipelines, change configuration, or make deployment
decisions.
