# Current handoff

## Handoff metadata

- Current branch: `docs/finalize-coastal-source-relationships`
- Resulting branch: `main`
- Issue: #26
- Work package: stage 4 coastal source-relationship finalization
- Roadmap state: stage 4 authorized and in progress

This handoff records the edited documentation state for issue #26. It does not
mark roadmap stage 4, issue #26, or a future pull request complete.
Issue #26 remains open.

## Objective

Finalize the minimum first-release location-to-source, NOAA tide, phase, and
source-result validity decisions required before coastal ingestion
implementation.

## Documentation completed

- updated the source evaluation with the accepted field contracts, repeated
  seven-day empirical results, UTC-normalized valid-time rule, NOAA request
  settings, tide phase, provenance, and independent source-result validity
  boundary
- updated the spatial evidence with the final display, weather, wave, SST,
  returned-grid, and NOAA tide relationships for all five locations
- retained the evidence type, source date, displacement, coastal regime, and
  representativeness limitation for each spatial relationship
- recorded the tested NOAA request units as `metric`

The evidence is documented in:

- [Coastal source evaluation](../research/coastal-source-evaluation.md)
- [Coastal spatial relationships](../research/coastal-spatial-relationships.md)

## Accepted decisions

- [ADR 0007](../decisions/0007-final-location-source-relationships.md)
  accepts the final first-release display, request, and product-specific
  expected returned-grid relationships.
- [ADR 0008](../decisions/0008-noaa-tide-relationships-and-phase.md)
  accepts the five NOAA prediction relationships, `MLLW`, `gmt`, `metric`,
  direct-use or transfer classifications, and binary rising or falling phase.
- [ADR 0009](../decisions/0009-coastal-source-result-validity-rules.md)
  accepts the minimum independent whole-source-result rejection, normalized UTC
  valid-time, spatial, field, and provenance rules.

ADRs 0004 through 0006 remain unchanged. No fallback coordinates, fallback
stations, geographic tolerances, runtime geographic inference, project tide
interpolation, or correction factors are authorized.

## Files changed

- `docs/research/coastal-source-evaluation.md`
- `docs/research/coastal-spatial-relationships.md`
- `docs/decisions/0007-final-location-source-relationships.md`
- `docs/decisions/0008-noaa-tide-relationships-and-phase.md`
- `docs/decisions/0009-coastal-source-result-validity-rules.md`
- `docs/decisions/README.md`
- `docs/scope-register.md`
- `docs/roadmap.md`
- `docs/handoffs/current.md`

Exactly nine documentation files are intended to change. No requirements,
existing ADRs, source code, configuration, database models, tests, scripts, CI,
skills, or technical architecture documents are included.

No coastal ingestion implementation has started.

## Validation

Validation for this documentation-only change completed successfully:

- `.\.venv\Scripts\python.exe -m pytest`: 49 passed in 3.86s
- `.\.venv\Scripts\python.exe -m ruff check .`: All checks passed!
- `git diff --check`: passed with nonblocking LF-to-CRLF normalization
  warnings
- changed-path review: exactly nine authorized documentation files changed
- focused diff review: PASS
- exact problems: none
- review conclusion: the diff was ready for this handoff validation update

## Unresolved relationships

- observation-station relationships
- accuracy and bias validation
- source fallback and precedence rules
- alternative marine-model adoption
- warning, forecast, and safety-zone relationships
- marine run-history reconstruction beyond metadata exposed by the accepted
  products

## Deferred work

- supplemental provider selection outside accepted source responsibilities
- observed-water-level ingestion
- tidal-current products and inlet-current requirements
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

Run the final diff check, then stage the nine authorized documentation files
and prepare the commit.

Do not begin coastal ingestion implementation.
