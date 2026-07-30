# Authoritative tide-product responsibility

## Status

Accepted

## Context

The first-release environmental baseline requires tide or water-level phase
tied to an appropriate local reference.

Stage 4 research distinguished:

- tide predictions
- observed water levels
- tidal-current predictions
- generic modeled mean-sea-level output

These products have different meanings and cannot be treated as
interchangeable.

NOAA CO-OPS publishes tide predictions for harmonic and subordinate prediction
locations, identifies reference-station relationships, and applies local datum
requirements. The available station relationships vary across the five
accepted SaltBytes locations.

Open-Meteo provides `sea_level_height_msl`, but it is referenced to global mean
sea level rather than a selected local tidal datum. Open-Meteo also documents
limited coastal accuracy for that modeled field.

The evidence is sufficient to establish the authoritative source family. It is
not sufficient to approve final prediction locations, stations, datums,
transfer rules, or a tide-phase calculation.

## Decision

NOAA CO-OPS tide predictions are the authoritative source family for satisfying
the locally referenced tide or water-level requirement.

SaltBytes will preserve the distinction between:

- tide predictions
- observed water levels
- tidal-current predictions
- generic modeled mean-sea-level output

Open-Meteo `sea_level_height_msl` will not satisfy the authoritative locally
referenced tide requirement.

It may remain eligible only as separately labeled modeled context. It must not
be represented as an authoritative local tide, a NOAA prediction, or an
observed water level.

This decision does not select:

- final prediction locations or stations
- final datums
- station-to-location transfer rules
- interpolation behavior
- a tide-phase calculation
- observation-station relationships
- tidal-current products

## Consequences

Benefits:

- establishes a responsible government source family for the local tide
  requirement
- prevents generic modeled mean-sea-level output from being mislabeled as a
  local tide
- preserves the semantic difference between prediction, observation, current,
  and modeled context
- supports traceable station, reference, and datum relationships
- bounds later tide work without selecting unsupported mappings

Costs and limitations:

- each SaltBytes location still requires a reviewed prediction relationship
- some nearby NOAA prediction locations represent an inlet, sound, river, or
  estuary rather than the accepted Atlantic-facing context
- subordinate predictions may support only high and low predictions
- station-to-location transfer remains undefined
- no tide phase can be calculated until station, datum, and transformation
  rules are approved
- observed water levels remain a separate unresolved relationship

Follow-up work:

- evaluate NOAA prediction candidates for each accepted location
- document harmonic or subordinate status and reference-station relationships
- select datums only after location-specific review
- determine whether direct use or an explicit transfer relationship is needed
- define tide-phase behavior through separately authorized work
- evaluate observation stations separately for validation or recent context
- keep tidal-current predictions outside the accepted surf and pier
  requirements unless future scope authorizes them

## Alternatives considered

### Use Open-Meteo modeled mean-sea-level height as local tide

This would not satisfy the requirement because the field uses a global
mean-sea-level reference and has documented coastal limitations.

### Use observed water levels as the primary tide product

Observations describe measured conditions rather than future astronomical tide
predictions. They may support validation or recent context but do not replace
the required prediction relationship.

### Use tidal-current predictions

Tidal-current predictions describe current timing and velocity rather than
local water-level phase. Inlet-current requirements are not approved for the
first release.

### Leave the tide source family entirely unresolved

The research established NOAA CO-OPS tide predictions as the appropriate
authoritative source family while location-specific mappings remain
unresolved.

### Use NOAA CO-OPS tide predictions

This is the accepted choice. It establishes the authoritative source family
without prematurely selecting stations, datums, transfer rules, or a phase
calculation.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Scope: [Scope register](../scope-register.md)
- Roadmap stage: [Stage 4](../roadmap.md#4-extend-coastal-data-source-ingestion)
- Requirement: [Fishing-condition requirements](../requirements/fishing-conditions.md)
- Existing decision: [Composite geographic model and initial locations](0002-composite-geographic-model-and-initial-locations.md)
- Existing decision: [First-release environmental requirement baseline](0003-first-release-environmental-requirement-baseline.md)
- Evidence: [Coastal source evaluation](../research/coastal-source-evaluation.md)
- Evidence: [Coastal spatial relationships](../research/coastal-spatial-relationships.md)
