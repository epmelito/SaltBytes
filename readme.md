# SaltBytes

SaltBytes is a local Python data pipeline for exploring upcoming coastal
conditions at five North Carolina fishing locations.

It currently collects:

- atmospheric forecasts
- wave forecasts
- sea-surface temperature
- NOAA tide predictions and hourly tide phase

The current milestone is a lightweight MVP that combines those sources into one
readable hourly result.

SaltBytes is a portfolio project. It does not guarantee fishing success,
replace official marine guidance, or operate as a production service.

## Current status

The ingestion pipeline is implemented. It loads YAML configuration, requests
each source independently, validates results, preserves accepted raw responses,
and stores normalized UTC data in DuckDB. The downstream
`coastal_conditions_hourly` view aligns available source values by exact run,
location, and UTC hour.

The MVP provides local text and HTML reports over the retained DuckDB state.

View the committed [sample report site](docs/sample-report/index.html) to open
separate coastal conditions and pipeline operations snapshots without installing
or running the project. The hosted workflow is configured to publish the same
three-page site after successful scheduled or manual ingestion. This publication
path remains pending hosted verification, and the stable Pages URL will be added
only after that verification succeeds.

See [the roadmap](docs/roadmap.md) for the delivery sequence.

## Locations

The current configuration covers:

- Jennette's Pier
- Beach Access Ramp 72, Ocracoke Island
- Fort Macon State Park, ocean side
- Bogue Inlet Pier
- Fort Fisher State Recreation Area

## Installation

SaltBytes requires Python 3.11 or later.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the pipeline

```powershell
saltbytes
```

The local configuration is `config/local.yml`. Runtime data is written beneath
its configured `data/` paths and is not committed to Git.

Hosted ingestion runs from `main` every six hours and can also be started
manually. See [hosted operation](docs/hosted-operation.md) for the required
Azure setup, recovery behavior, and manual-run procedure.

## Read the latest report

```powershell
saltbytes report conditions
saltbytes report operations
```

Generate self contained HTML reports:

```powershell
saltbytes report conditions --format html --output conditions.html
saltbytes report operations --format html --output operations.html
```

Both report types select the latest attempted run by default, including a failed
or partial run. The text conditions report displays the first 24 forecast hours
at or after the run start, while the text operations report summarizes the
selected run and source status. The HTML conditions report adds forecast charts,
and the HTML operations report adds retained pipeline history, source coverage,
revisions, and provenance. Use `--run-id`, `--location`, or `--hours` to select a
specific run, configured location, or forecast window. Stored timestamps remain
UTC; output uses the configured local display timezone.

## Validation

```powershell
python -m pytest
python -m ruff check .
```

Use focused tests while developing and run the full checks once after a
meaningful code change is stable.

## Repository structure

```text
saltbytes/
|-- .agents/skills/
|-- .github/workflows/
|-- config/
|-- docs/
|-- src/saltbytes/
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
