# Scope register

## Purpose

This register separates verified current capability, approved future direction,
deferred decisions, and exclusions. It controls the scope of active work
without replacing the product charter or roadmap.

## Scope states

| State | Meaning |
| --- | --- |
| Current | Verified as implemented in the repository |
| Approved future | Part of the approved product direction but not necessarily implemented |
| Deferred | A recognized choice that has not been decided |
| Excluded | Outside the approved product boundary |
| Drift | Existing documentation differs from verified implementation |

## Current implementation

The current repository provides:

- a local Python coastal atmospheric, wave, SST, and tide prediction pipeline
- `dev`, `test`, and `prod` local YAML configurations
- the five approved North Carolina coastal locations
- seven-day Open-Meteo `ncep_nbm_conus` ingestion
- separate display, weather-request, and expected returned weather coordinates
- wind speed, direction, gust, precipitation probability, and precipitation
- seven-day Open-Meteo `meteofrance_wave` ingestion
- separate marine-request and expected returned wave-grid coordinates
- wave height, direction, and period
- seven-day Open-Meteo `meteofrance_currents` ingestion
- separate SST request and expected returned product-grid coordinates
- sea-surface temperature only
- NOAA CO-OPS high and low tide predictions using the five accepted
  prediction-location relationships
- normalized NOAA events and 168 hourly binary tide phases per passing result
- immutable raw JSON snapshots for payloads that pass pipeline quality checks
- 168 normalized hourly UTC forecasts for each passing source result
- independent weather, wave, SST, and tide quality rejection without partial
  result storage
- pipeline run, request, response, snapshot, and quality metadata
- atmospheric, wave, SST, and tide phase revision calculations
- structured logging and manual inspection scripts
- pytest coverage and GitHub Actions validation
- a bounded, diagnostic forecast failure review skill

The nullable `temperature_2m` database column remains only for compatibility
with existing local history. Ocean-current, sea-level-height,
observed-water-level, tidal-current, scoring, scheduling, publication, agents,
and cloud infrastructure are not implemented.

## Initial governance work package

The initial governance work package created:

- `AGENTS.md`
- `docs/project-charter.md`
- `docs/roadmap.md`
- `docs/scope-register.md`
- `docs/decisions/README.md`
- `docs/handoffs/current.md`

Pull request #13 introduced all six governance files after content review and a
successful required `test and lint` check. A follow-up correction aligned the
lifecycle records with the completed state.

The initial governance work package and roadmap stage 1 are complete.

## Completed documentation reconciliation work package

Issue #15 authorized the roadmap stage 2 documentation reconciliation work
package.

The work package modified only:

- `readme.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/environments.md`
- `docs/scope-register.md`
- `docs/roadmap.md`
- `docs/handoffs/current.md`

It reconciled verified documentation drift without changing application
behavior, repository skills, product direction, deferred decisions, or roadmap
stages 3 through 9. A follow-up lifecycle-state correction aligned the
governance records with the completed work package.

The documentation reconciliation work package and roadmap stage 2 are
complete.

## Completed coastal requirements work package

Issue #20 authorized the roadmap stage 3 coastal location and fishing-condition
requirements work package. Pull request #21 merged its requirements, accepted
decision records, and governance updates into `main`. Issue #20 closed after
its acceptance criteria were satisfied.

The coastal requirements work package and roadmap stage 3 are complete.
Roadmap stage 4 is authorized and in progress.

The requirements focus on stable location identity, spatial source
relationships, environmental metrics, forecast history, data quality, and
support for later deterministic and explainable scoring.

The approved requirements are documented in:

- [Coastal location requirements](requirements/coastal-locations.md)
- [Fishing-condition requirements](requirements/fishing-conditions.md)

The accepted decisions are:

- [First-release user and fishing-context boundary](decisions/0001-first-release-user-and-fishing-context.md)
- [Composite geographic model and initial locations](decisions/0002-composite-geographic-model-and-initial-locations.md)
- [First-release environmental requirement baseline](decisions/0003-first-release-environmental-requirement-baseline.md)

## Completed coastal atmospheric implementation checkpoint

Issues #24 and #26 established the accepted stage 4 source, spatial, tide, and
source-result decisions. Issue #30 implemented the first coastal ingestion
checkpoint for the five approved locations using `ncep_nbm_conus`. Pull
request #31 merged the atmospheric ingestion into `main`.

The issue #30 implementation includes only:

- the accepted location and weather-grid relationships
- the five accepted atmospheric fields
- seven-day requests and 168-hour UTC normalization
- deterministic whole-result quality checks
- immutable passing raw snapshots
- request and response provenance
- normalized atmospheric storage and revision history

## Implemented coastal wave checkpoint

Issue #33 implements the bounded wave-ingestion checkpoint:

- Open-Meteo Marine API wave ingestion
- model `meteofrance_wave`
- `wave_height`
- `wave_direction`
- `wave_period`
- the five approved coastal locations
- the accepted marine request and expected returned coordinates
- independent atmospheric and wave source results
- wave raw snapshots, normalized storage, provenance, quality evidence, and
  revision history

The implementation processes atmospheric and wave results independently,
retains source-qualified quality evidence, stores separate raw snapshots and
request and response provenance, normalizes passing results into separate
tables, and exposes wave revision history. A fully passing five-location run
produces ten snapshots and 1,680 normalized rows.

Issue #33 does not implement or authorize:

- sea-surface-temperature ingestion
- ocean-current ingestion
- sea-level-height ingestion
- NOAA tide ingestion
- tide-phase calculation
- scoring
- scheduling
- publication
- Azure deployment
- agents

## Implemented coastal SST checkpoint

Issue #41 implements the bounded sea-surface-temperature checkpoint:

- Open-Meteo Marine API SST ingestion
- model `meteofrance_currents`
- `sea_surface_temperature` only
- the five approved coastal locations
- accepted product-specific SST request and expected returned coordinates
- independent atmospheric, wave, and SST source results
- SST raw snapshots, normalized storage, provenance, source-qualified quality
  evidence, and revision history

The implementation validates and stores SST independently from atmospheric and
wave results. Passing SST results produce separate immutable raw snapshots and
168 normalized hourly UTC rows. A fully passing five-location run produces 15
snapshots and 2,520 normalized rows across the three implemented sources.

Issue #41 does not implement or authorize:

- ocean-current velocity or direction
- sea-level-height ingestion
- NOAA tide ingestion or tide-phase calculation
- sunrise, sunset, or lunar data
- scoring
- scheduling changes
- publication
- Azure deployment
- additional agents or skills

## Implemented coastal tide checkpoint

Issue #45 implements the bounded NOAA tide-prediction checkpoint:

- NOAA CO-OPS product `predictions`
- interval `hilo`, datum `MLLW`, time zone `gmt`, and units `metric`
- the five accepted direct or transfer prediction-location relationships
- source-qualified relationship, request, event, and phase validation
- separate immutable passing raw snapshots and NOAA provenance
- normalized high and low events with predicted water level
- exactly 168 hourly UTC binary phase rows per passing result
- tide phase revision history without numeric phase-delta semantics

The implementation validates and stores tide independently from atmospheric,
wave, and SST results. A tide quality rejection retains run and quality
evidence without tide raw, event, or phase rows and does not discard other
passing source results.

Issue #45 does not implement or authorize:

- observed water levels or tidal-current predictions
- interpolation, correction factors, alternate stations, or fallbacks
- continuous tide phase or synthetic extrema
- integrated coastal modeling or scoring
- scheduling, publication, or Azure deployment
- additional agents or skills

Roadmap stage 4 remains in progress. Observation relationships, accuracy and
bias validation, fallback and precedence rules, alternative marine-model
adoption, warning and forecast-zone mappings, and marine run-history
reconstruction remain unresolved or deferred.

The stage 4 evidence is recorded in:

- [Coastal source evaluation](research/coastal-source-evaluation.md)
- [Coastal spatial relationships](research/coastal-spatial-relationships.md)

The accepted stage 4 decisions are:

- [Spatial coordinate and returned-grid relationship policy](decisions/0004-spatial-coordinate-and-returned-grid-policy.md)
- [First-release Open-Meteo atmospheric and marine model strategy](decisions/0005-open-meteo-model-strategy.md)
- [Authoritative tide-product responsibility](decisions/0006-authoritative-tide-product-responsibility.md)
- [Final first-release location-to-source relationships](decisions/0007-final-location-source-relationships.md)
- [First-release NOAA tide relationships and phase](decisions/0008-noaa-tide-relationships-and-phase.md)
- [Minimum coastal source-result validity rules](decisions/0009-coastal-source-result-validity-rules.md)

## Approved future scope

Approved future scope is grouped into:

- North Carolina coastal condition data and retained forecast history
- deterministic scoring, fishing-window ranking, and consumer-ready data
- a reusable personal Azure portfolio platform and public display
- bounded AI-assisted engineering workflows

The full durable product direction is defined in the
[project charter](project-charter.md). These categories approve capability
areas, not their deferred product or architecture details.

Roadmap stage 3 has approved the following first-release requirements:

- general recreational coastal anglers
- surf and fixed publicly accessible fishing pier contexts
- comparison of windows only within the same fishing context
- general environmental conditions rather than species-specific
  recommendations
- a composite coastal location model
- Jennette’s Pier
- Beach Access Ramp 72, Ocracoke Island, as an ocean-side surf context
- Fort Macon State Park, ocean side
- Bogue Inlet Pier as a pier context only
- Fort Fisher State Recreation Area
- the required, optional, safety-only, deferred, and excluded environmental
  classifications in the
  [fishing-condition requirements](requirements/fishing-conditions.md)
- separation of safety-only information from fishing-quality interpretation
- distinct display, request, and source-specific returned-grid relationships
  with evidence, displacement, coastal-regime, resolution, representativeness,
  and relationship-status metadata
- Open-Meteo `ncep_nbm_conus` for the first-release atmospheric fields
- Open-Meteo `meteofrance_wave` for wave height, direction, and period
- Open-Meteo `meteofrance_currents` only for `sea_surface_temperature`
- NOAA CO-OPS tide predictions as the authoritative source family for the
  locally referenced tide or water-level requirement
- separation of tide predictions, observed water levels, tidal-current
  predictions, and generic modeled mean-sea-level context
- the final first-release display, request, and product-specific expected
  returned-grid relationships for the five approved locations
- NOAA CO-OPS prediction-location relationships using `MLLW`, `gmt`, and
  `metric`, including one direct-use and four explicit transfer relationships
- a binary rising or falling tide phase based on bounding high and low events
- independent whole-source-result validity and provenance rules for weather,
  wave, sea-surface-temperature, and tide results

The accepted decisions and their rationale are recorded in the
[decision index](decisions/README.md). Issues #30, #33, #41, and #45 implement
the atmospheric, wave, SST, and tide subsets described in the current
implementation section.

Delivery order is controlled by the [roadmap](roadmap.md).

## Exclusions

Excluded scope is defined by the
[product boundaries in the charter](project-charter.md#product-boundaries).
It covers fishing-success or safety-authority claims, opaque scoring, an
initial real-time commercial service, exhaustive first-release coverage or
variables, and product feature implementation before the governance lifecycle
above is complete.

## Deferred decisions

The following decisions are intentionally open:

| Topic | Status |
| --- | --- |
| Supplemental provider selection and source-authority rules outside the accepted atmospheric, wave, sea-surface-temperature, and tide responsibilities | Deferred |
| Observation-station relationships | Deferred |
| Warning and forecast-zone mappings | Deferred |
| Accuracy and bias validation | Deferred |
| Source fallback and precedence rules | Deferred |
| Marine run-history reconstruction | Deferred |
| Alternative marine-model adoption | Deferred |
| Score variables, formulas, thresholds, and weights | Deferred |
| Shore-accessed inlet use cases | Deferred |
| Vessel-based nearshore use cases | Deferred |
| Offshore use cases | Deferred |
| Species-specific use cases and recommendations | Deferred |
| Forecast and observation retention periods | Deferred |
| Publication format | Deferred |
| Dashboard or API design | Deferred |
| Scheduling frequency | Deferred |
| Azure service and deployment architecture | Deferred |
| Infrastructure as code approach | Deferred |
| Service levels | Deferred |
| Cost limits | Deferred |
| Final success metrics | Deferred |

These topics should remain open until a roadmap stage requires a durable choice.
Accepted choices should be recorded through the
[decision process](decisions/README.md).

## Known documentation drift

No verified documentation drift remains unresolved.

## Scope changes

A proposed change should:

1. identify the charter outcome it supports
2. identify the affected roadmap stage
3. state whether it changes current, future, deferred, or excluded scope
4. use a decision record when a durable choice or tradeoff requires rationale
5. update this register after approval

The [current handoff](handoffs/current.md) may report scope status but cannot
approve a scope change.
