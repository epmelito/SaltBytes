# Current handoff

## Handoff metadata

- Current branch: `feature/coastal-tide-ingestion`
- Active issue: #45
- Work package: NOAA coastal tide ingestion

## Objective

Implement the five accepted NOAA CO-OPS prediction relationships, normalized
high and low events, and binary hourly tide phase as an independent source.

## Current checkpoint

- Tide configuration, requests, validation, raw retention, provenance,
  normalized events, hourly phase, and revision history are implemented.
- Tide quality rejection preserves atmospheric, wave, and SST results and
  continues later locations.
- Operational API and persistence failures retain immediate-abort behavior.
- Stage 4 remains in progress; integrated coastal modeling is not implemented.
- No live provider or production-style pipeline run was performed.

## Files changed

- `config/dev.yml`, `config/test.yml`, and `config/prod.yml`
- `src/forecast_ops/api.py`, `config.py`, `database.py`, `pipeline.py`, and
  `quality.py`
- `tests/test_api.py`, `test_cli.py`, `test_config.py`, `test_database.py`,
  `test_pipeline.py`, `test_pipeline_fixtures.py`, and `test_quality.py`
- `readme.md`
- `docs/architecture.md`, `data-model.md`, `environments.md`, `roadmap.md`,
  and `scope-register.md`
- `docs/handoffs/current.md`

## Validation

- Focused configuration, API, quality, persistence, pipeline, fixture, and CLI
  suite: 229 passed.
- Final quality, persistence, and full fixture check: 102 passed.
- Focused Ruff on `src`: passed.
- Full suite: 245 passed.
- Full Ruff: passed.
- `git diff --check`: passed with only LF-to-CRLF notices.
- Deferred validation: none.

## Known issues and decisions

- Known issues: none.
- No deferred provider, fallback, observation, scoring, scheduling,
  publication, or deployment decision was resolved.

## Next checkpoint

Perform the independent work-package review.
