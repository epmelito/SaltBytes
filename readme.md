# ForecastOps

ForecastOps is a local Python data pipeline for exploring upcoming coastal
conditions at five North Carolina fishing locations.

It currently collects:

- atmospheric forecasts
- wave forecasts
- sea-surface temperature
- NOAA tide predictions and hourly tide phase

The current milestone is a lightweight MVP that combines those sources into one
readable hourly result.

ForecastOps is a portfolio project. It does not guarantee fishing success,
replace official marine guidance, or operate as a production service.

## Current status

The ingestion pipeline is implemented. It loads YAML configuration, requests
each source independently, validates results, preserves accepted raw responses,
and stores normalized UTC data in DuckDB. The downstream
`coastal_conditions_hourly` view aligns available source values by exact run,
location, and UTC hour.

The MVP provides a local readable output over the integrated hourly view.

See [the roadmap](docs/roadmap.md) for the delivery sequence.

## Locations

The current configuration covers:

- Jennette's Pier
- Beach Access Ramp 72, Ocracoke Island
- Fort Macon State Park, ocean side
- Bogue Inlet Pier
- Fort Fisher State Recreation Area

## Installation

ForecastOps requires Python 3.11 or later.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the pipeline

```powershell
forecast-ops
```

The local configuration is `config/local.yml`. Runtime data is written beneath
its configured `data/` paths and is not committed to Git.

## Read the latest report

```powershell
forecast-ops report
```

The report selects the latest attempted run, including a failed or partial run,
and displays the first 24 forecast hours at or after its start time. Use
`--run-id`, `--location`, or `--hours` to select a specific run, configured
location, or forecast window. Stored timestamps remain UTC; output uses the
configured local display timezone.

## Validation

```powershell
python -m pytest
python -m ruff check .
```

Use focused tests while developing and run the full checks once after a
meaningful code change is stable.

## Repository structure

```text
forecast-ops/
|-- .agents/skills/
|-- .github/workflows/
|-- config/
|-- docs/
|-- src/forecast_ops/
|-- tests/
|-- AGENTS.md
|-- pyproject.toml
`-- readme.md
```

## Documentation

- [Project charter](docs/project-charter.md) defines durable product intent.
- [Roadmap](docs/roadmap.md) defines the active MVP sequence.
- [Architecture](docs/architecture.md) describes the current system.
- [Data model](docs/data-model.md) describes persisted data and the planned
  integrated result.
- [Agent guidance](AGENTS.md) defines repository working rules.

Documents under `docs/decisions`, `docs/research`, and `docs/requirements`
preserve supporting history and evidence. Read them only when a task depends on
the specific content.
