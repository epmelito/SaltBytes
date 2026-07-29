# Current handoff

## Handoff metadata

- Current branch: `feature/coastal-sst-ingestion`
- Active issue: #41
- Work package: coastal sea-surface-temperature ingestion

## Objective

Implement the accepted `meteofrance_currents` SST contract for the five
approved coastal locations.

## Current checkpoint

- SST configuration, requests, independent validation, immutable raw storage,
  provenance, normalization, and revision history are implemented.
- Missing or unusable SST relationships and coastal regimes produce
  source-qualified preflight rejection without fetching or storing SST.
- The prior blocking conformance defect was corrected.
- Independent re-review passed, and issue #41 conforms to its authorized work
  package.
- Atmospheric and wave behavior remains covered.
- Stage 4 remains in progress; tide and other excluded capabilities remain
  unimplemented.

## Files changed

- `config/dev.yml`
- `config/prod.yml`
- `config/test.yml`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/environments.md`
- `docs/roadmap.md`
- `docs/scope-register.md`
- `docs/handoffs/current.md`
- `readme.md`
- `scripts/check_forecast_revisions.py`
- `src/forecast_ops/api.py`
- `src/forecast_ops/config.py`
- `src/forecast_ops/database.py`
- `src/forecast_ops/pipeline.py`
- `src/forecast_ops/quality.py`
- `tests/test_api.py`
- `tests/test_cli.py`
- `tests/test_config.py`
- `tests/test_database.py`
- `tests/test_pipeline.py`
- `tests/test_pipeline_fixtures.py`
- `tests/test_quality.py`

## Validation

- Focused SST preflight, configuration, CLI, and integration checks: 133
  passed.
- Targeted correction check: 58 passed.
- Full pytest suite: 189 passed.
- Focused and full Ruff: passed.
- `git diff --check`: passed; LF-to-CRLF notices are nonblocking.
- Live provider and pipeline runs were not performed.
- Deferred validation: none.

## Known issues and decisions

- Known issues: none.
- No deferred product or architecture decision was resolved.

## Next checkpoint

Pull-request review and required checks.
