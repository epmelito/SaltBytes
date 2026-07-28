# Current handoff

## Handoff metadata

- Current branch: `feature/coastal-atmospheric-ingestion`
- Resulting branch: `main`
- Issue: #30
- Work package: stage 4 coastal atmospheric ingestion
- Roadmap state: stage 4 authorized and in progress

Issue #30 and its future pull request are not complete. Marine,
sea-surface-temperature, and tide ingestion remain unstarted.

## Objective

Implement the first coastal ingestion slice for the five approved locations
using the accepted Open-Meteo atmospheric model, spatial relationships, field
contract, validity rules, provenance, normalized storage, and revision history.

## Implementation completed

- configured the five approved coastal locations with display, request, and
  expected returned weather coordinates
- configured `ncep_nbm_conus`, seven forecast days, and the five atmospheric
  fields
- constructed requests from the weather-request coordinates
- implemented model-contract, field, coordinate, timezone, and 168-hour UTC
  quality checks
- added idempotent DuckDB upgrades and bounded snapshot provenance
- normalized passing atmospheric results to UTC
- expanded atmospheric forecast revision history
- retained nullable legacy `temperature_2m` storage
- continued after location quality rejection while preserving successful
  unrelated results
- retained immediate abort behavior for API, raw-storage, and database failures
- updated the affected manual database and revision scripts
- reconciled current technical documentation and governance state

No marine, sea-surface-temperature, tide, scoring, scheduling, publication,
cloud, or agent implementation is included.

## Files changed for issue #30

- `config/dev.yml`
- `config/prod.yml`
- `config/test.yml`
- `scripts/check_database.py`
- `scripts/check_forecast_revisions.py`
- `src/forecast_ops/api.py`
- `src/forecast_ops/config.py`
- `src/forecast_ops/database.py`
- `src/forecast_ops/pipeline.py`
- `src/forecast_ops/quality.py`
- `tests/test_api.py`
- `tests/test_config.py`
- `tests/test_database.py`
- `tests/test_pipeline.py`
- `tests/test_pipeline_fixtures.py`
- `tests/test_quality.py`
- `readme.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/environments.md`
- `docs/scope-register.md`
- `docs/roadmap.md`
- `docs/handoffs/current.md`

`AGENTS.md` is separately modified by a pre-existing governance change. It is
not part of issue #30.

## Validation

Completed checkpoint validation:

- configuration and API tests: 38 passed
- quality tests: 23 passed
- database tests: 13 passed
- pipeline tests: 5 passed
- all targeted Ruff checks passed
- all checkpoint diff checks passed with only nonblocking LF-to-CRLF
  normalization warnings

Completed final validation:

- full test suite: 94 passed in 15.33s
- repository-wide Ruff: `All checks passed!`
- `git diff --check`: passed with only nonblocking LF-to-CRLF normalization
  warnings
- the complete issue #30 diff was reviewed
- exactly the 23 issue #30 files listed above are changed, with `AGENTS.md`
  remaining a separate pre-existing governance change

## Remaining stage 4 work

- Open-Meteo wave ingestion
- Open-Meteo sea-surface-temperature ingestion
- NOAA tide prediction ingestion and phase calculation
- observation-station relationships
- accuracy and bias validation
- source fallback and precedence rules
- warning and forecast-zone mappings
- marine run-history reconstruction

Deferred scoring, retention, scheduling, publication, API, dashboard, Azure,
inlet, vessel, offshore, and species-specific work remains unchanged.

## Next checkpoint

Complete the final review checkpoint, then stage the issue #30 files and
prepare the commit. Keep the separate `AGENTS.md` governance change out of the
issue #30 staging set.
