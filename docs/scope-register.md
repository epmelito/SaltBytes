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

- a local Python weather forecast pipeline
- `dev`, `test`, and `prod` local YAML configurations
- Open-Meteo hourly forecast ingestion
- immutable raw JSON snapshots for payloads that pass pipeline quality checks
- normalized hourly weather forecasts in DuckDB
- pipeline run, snapshot, and quality metadata
- forecast revision calculations for implemented weather fields
- structured logging and manual inspection scripts
- pytest coverage and GitHub Actions validation
- a bounded, diagnostic forecast failure review skill

The configured locations are currently Prague and Ocracoke, North Carolina.
Implemented forecast fields are air temperature, precipitation probability,
and wind speed. These facts describe the current foundation and do not define
the future coastal location set or fishing-condition requirements.

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
Product implementation has not started. Roadmap stage 4 is authorized and in
progress through issue #24.

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

## Active coastal source evaluation work package

Issue #24 authorizes the roadmap stage 4 research and decision work needed to
evaluate coastal data sources and spatial relationships.

The current work package may:

- document the reviewed Open-Meteo source evaluation
- document candidate spatial and tide relationships
- accept bounded source, model, spatial-policy, and tide-product decisions
- update governance records to reflect those accepted decisions

The work package does not authorize ingestion implementation.

Roadmap stage 4 is in progress. Final coordinates, returned-grid
relationships, NOAA prediction-location, station and datum mappings,
tide-transfer rules, observation relationships, accuracy validation, fallback
rules, and marine run-history reconstruction remain unresolved.

The stage 4 evidence is recorded in:

- [Coastal source evaluation](research/coastal-source-evaluation.md)
- [Coastal spatial relationships](research/coastal-spatial-relationships.md)

The accepted stage 4 decisions are:

- [Spatial coordinate and returned-grid relationship policy](decisions/0004-spatial-coordinate-and-returned-grid-policy.md)
- [First-release Open-Meteo atmospheric and marine model strategy](decisions/0005-open-meteo-model-strategy.md)
- [Authoritative tide-product responsibility](decisions/0006-authoritative-tide-product-responsibility.md)

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
- surf and publicly accessible fixed fishing pier contexts
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

The accepted decisions and their rationale are recorded in the
[decision index](decisions/README.md). Implementation of these requirements has
not started.

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
| Final display or destination and weather-request coordinates | Deferred |
| Final marine request coordinates and returned-grid relationships | Deferred |
| Exact NOAA prediction-location, station, datum, phase, and transfer relationships | Deferred |
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
