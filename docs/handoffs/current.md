# Current handoff

## Handoff metadata

- Current branch: `docs/complete-coastal-requirements-stage`
- Resulting branch: `main`
- Issue: #22
- Completed stage 3 issue: #20
- Completed stage 3 pull request: #21
- Work package: record completion of roadmap stage 3
- Roadmap state: stage 3 complete; stage 4 next but unauthorized and unstarted

This handoff records the lifecycle correction for the completed roadmap stage 3
work package. It does not mark issue #22 or its pull request complete.

## Objective

Align the lifecycle records with the post-merge `main` state after issue #20
and pull request #21 completed roadmap stage 3.

## Completed stage 3 work

- the coastal location and fishing-condition requirements are present on `main`
- ADRs 0001, 0002, and 0003 are accepted and indexed
- the representative location set and environmental baseline are documented
  with reviewed evidence
- remaining provider, spatial-relationship, scoring, operational, and
  architecture topics remain deferred
- issue #20 and pull request #21 completed the stage 3 work package
- no product implementation was included

## Files changed

- `docs/roadmap.md`
- `docs/scope-register.md`
- `docs/handoffs/current.md`

## Validation

Validation for issue #22 completed successfully:

- `git status --short`: exactly the three authorized files changed
- `git diff --name-only`: exactly the three authorized files changed
- complete diff: reviewed against issue #22
- accepted requirements and ADRs: unchanged
- deferred-topic review: all deferred topics remain deferred
- heading and relative-link review: passed
- `git diff --check`: passed with LF-to-CRLF normalization warnings
- `.\.venv\Scripts\python.exe -m pytest`: 49 tests passed
- `.\.venv\Scripts\python.exe -m ruff check .`: all checks passed

## Deferred work

The following remain deferred:

- provider selection and source-authority rules
- display or destination and weather-request coordinates
- marine sampling coordinates
- tide and water-level reference relationships
- observation-station relationships
- warning and forecast-zone mappings
- scoring variables, formulas, thresholds, and weights
- retention
- scheduling
- publication
- API and dashboard design
- Azure and deployment architecture
- shore-accessed inlet use cases
- vessel-based nearshore use cases
- offshore use cases
- species-specific use cases and recommendations

## Next checkpoint

Review the validated lifecycle-only diff and deliver issue #22 through its pull
request. Roadmap stage 4 remains unauthorized and unstarted.
