# SaltBytes

SaltBytes is a Python data pipeline and static reporting project for exploring
upcoming coastal conditions at five North Carolina fishing locations.

It currently collects:

- atmospheric forecasts
- wave forecasts
- sea-surface temperature
- NOAA tide predictions and hourly tide phase

The current platform combines those sources into readable hourly reports and an
interactive dashboard. The approved next milestone is implementing an
explainable 0 to 100 Spanish mackerel conditions score from existing SaltBytes
inputs.

The methodology is approved, but the score is not implemented. It will assess
how favorable the available conditions are for targeting Spanish mackerel
without claiming catch probability, bite likelihood, or fish presence.

SaltBytes is a portfolio project. It does not guarantee fishing success,
replace official marine guidance, or operate as a production service.

## Current status

The ingestion pipeline is implemented. It loads YAML configuration, requests
each source independently, validates results, preserves accepted raw responses,
and stores normalized UTC data in DuckDB. The downstream
`coastal_conditions_hourly` view aligns available source values by exact run,
location, and UTC hour.

The MVP provides local text and HTML reports, a curated public JSON export, and
an interactive Observable dashboard over the retained DuckDB state.

View the [public site](https://epmelito.github.io/SaltBytes/) for the latest
successfully published dashboard, coastal conditions report, and pipeline
operations report. The site refreshes after successful scheduled or manual
ingestion. View the committed [sample report site](docs/sample-report/index.html)
for a fixed reviewed snapshot that does not change with hosted runs.

See [the roadmap](docs/roadmap.md) for the delivery sequence,
[decision 0010](docs/decisions/0010-research-backed-fishing-score-direction.md)
for the product direction, and
[species conditions scoring requirements](docs/requirements/species-condition-scoring.md)
for the shared boundary, and the
[Spanish mackerel methodology](docs/requirements/spanish-mackerel-conditions-score.md)
for the approved first calculation.

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

The Observable dashboard requires Node.js 24 for local builds. Install its
locked dependencies from `dashboard/package-lock.json`:

```powershell
Push-Location dashboard
npm ci
Pop-Location
```

## Run the pipeline

```powershell
saltbytes
```

The local configuration is `config/local.yml`. Runtime data is written beneath
its configured `data/` paths and is not committed to Git.

Hosted ingestion runs from `main` every six hours and can also be started
manually. See [hosted operation](docs/hosted-operation.md) for the required
Azure setup, publication path, recovery behavior, and manual-run procedure.

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

## Build the dashboard

Export curated public data from the configured DuckDB database, then build the
static Observable site:

```powershell
saltbytes dashboard export --output dashboard/src/data
Push-Location dashboard
npm run build
Pop-Location
```

The browser reads only the generated JSON and static dashboard assets. It does
not connect to DuckDB, Azure Blob Storage, authenticated APIs, or a running
application server.

## Validation

```powershell
python -m pytest
python -m ruff check .
Push-Location dashboard
npm ci
npm run build
Pop-Location
```

Use focused tests while developing and run the full checks once after a
meaningful code change is stable.

## Repository structure

```text
saltbytes/
|-- .agents/skills/
|-- .github/workflows/
|-- config/
|-- dashboard/
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
- [Species conditions scoring requirements](docs/requirements/species-condition-scoring.md)
  define the approved scoring boundary.
- [Spanish mackerel conditions score methodology](docs/requirements/spanish-mackerel-conditions-score.md)
  defines the approved first score calculation.
- [Agent guidance](AGENTS.md) defines repository working rules.

Documents under `docs/decisions`, `docs/research`, and `docs/requirements`
preserve supporting history and evidence. Read them only when a task depends on
the specific content.
