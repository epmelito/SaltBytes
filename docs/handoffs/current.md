# Current handoff

## Handoff metadata

- Current branch: `docs/evaluate-coastal-data-sources`
- Resulting branch: `main`
- Issue: #24
- Work package: stage 4 coastal source and spatial-relationship evaluation
- Roadmap state: stage 4 authorized and in progress

This handoff records the edited documentation state for issue #24. It does not
mark roadmap stage 4, issue #24, or a future pull request complete.

## Objective

Document the reviewed Open-Meteo source evaluation, preserve candidate spatial
and tide relationships, and record the accepted decisions required before
coastal ingestion implementation.

## Research completed

- evaluated Open-Meteo weather and marine field coverage, model resolution,
  forecast horizons, null behavior, and provenance limitations
- evaluated authoritative location anchors and candidate weather and marine
  request relationships for the five accepted locations
- compared requested coordinates with returned model-grid coordinates
- classified candidate returned cells by coastal regime and limitation
- evaluated NOAA CO-OPS tide-prediction relationships without selecting final
  locations, stations, datums, transfer rules, or a phase calculation
- recorded all external source URLs, available source dates, and the access
  date 2026-07-28

The evidence is documented in:

- [Coastal source evaluation](../research/coastal-source-evaluation.md)
- [Coastal spatial relationships](../research/coastal-spatial-relationships.md)

## Accepted decisions

- [ADR 0004](../decisions/0004-spatial-coordinate-and-returned-grid-policy.md)
  preserves distinct display, request, and source-specific returned-grid
  relationships and their evidence and limitations.
- [ADR 0005](../decisions/0005-open-meteo-model-strategy.md) selects
  `ncep_nbm_conus` for first-release atmospheric fields,
  `meteofrance_wave` for wave height, direction, and period, and
  `meteofrance_currents` only for `sea_surface_temperature`.
- [ADR 0006](../decisions/0006-authoritative-tide-product-responsibility.md)
  establishes NOAA CO-OPS tide predictions as the authoritative source family
  for satisfying the locally referenced tide or water-level requirement.

Open-Meteo `models=auto` is not accepted for the first-release atmospheric or
marine strategy. Open-Meteo `sea_level_height_msl` does not satisfy the
authoritative tide requirement.

## Files changed

- `docs/research/coastal-source-evaluation.md`
- `docs/research/coastal-spatial-relationships.md`
- `docs/decisions/0004-spatial-coordinate-and-returned-grid-policy.md`
- `docs/decisions/0005-open-meteo-model-strategy.md`
- `docs/decisions/0006-authoritative-tide-product-responsibility.md`
- `docs/decisions/README.md`
- `docs/scope-register.md`
- `docs/roadmap.md`
- `docs/handoffs/current.md`

No ingestion implementation is included.

## Validation

Validation for this documentation-only change completed successfully:

- `.\.venv\Scripts\python.exe -m pytest`: 49 passed in 3.86s
- `.\.venv\Scripts\python.exe -m ruff check .`: All checks passed!
- `git diff --check`: passed with nonblocking LF-to-CRLF normalization
  warnings
- changed-path review: exactly the nine authorized documentation files are
  changed
- boundary review: no source code, configuration, tests, scripts, CI, skills,
  requirements, or existing ADRs changed

The full nine-file documentation diff was reviewed. Three minor documentation
corrections were identified.

## Unresolved relationships

- final display or destination coordinates
- final weather request coordinates
- final marine request coordinates
- final returned weather and marine grid relationships
- exact NOAA prediction-location, station, and datum mappings
- tide interpolation or station-to-location transfer rules
- tide or water-level phase calculation
- observation-station relationships
- accuracy and bias validation
- source fallback and precedence rules
- marine run-history reconstruction

Temporary empirical probes remain research evidence and are not approved
implementation relationships.

## Deferred work

- supplemental provider selection
- warning and forecast-zone mappings
- ECMWF WAM and other alternative marine models
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

Apply the three review corrections, rerun `git diff --check`, confirm the final
diff is ready, then stage the nine authorized files and prepare the commit. Do
not begin coastal ingestion implementation.
