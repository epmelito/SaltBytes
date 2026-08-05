# Spatial coordinate and returned-grid relationship policy

## Status

Accepted

## Context

SaltBytes uses a composite coastal location as its geographic modeling unit.
The accepted locations are fishing destinations, but atmospheric, marine,
tide, and other environmental products do not necessarily apply at one
universal coordinate.

Stage 4 research confirmed that Open-Meteo may return a model-grid coordinate
several kilometres from the requested coordinate. Near barrier islands,
inlets, sounds, rivers, and long beach segments, the returned cell may
represent a different coastal regime from the intended fishing context.

The research also confirmed that wave and sea-surface-temperature products can
use different models and return different grid cells for the same composite
location. Treating one returned marine cell as universal would conceal those
source-specific relationships.

## Decision

SaltBytes will preserve these distinct relationships:

- display or destination coordinate
- weather request coordinate
- marine request coordinate
- returned weather grid coordinate for each model or product
- returned marine grid coordinate for each model or product

Each spatial relationship will retain:

- coordinate evidence type
- evidence source
- evidence source date when available
- requested-to-returned displacement
- coastal-regime classification
- model or product selector
- source-resolution limitations
- spatial-representativeness limitations
- relationship status

Coordinate evidence types will distinguish:

- directly published coordinates
- coordinates derived from authoritative geometry
- project inferences
- temporary empirical probes

Temporary empirical probes may be recorded in research evidence. They must not
become approved implementation relationships without separate review.

Returned marine cells are model-specific or product-specific relationships.
They are not universal coordinates for a composite coastal location.

Wave and sea-surface-temperature products may use different returned grid
cells.

This decision establishes the relationship policy and required metadata. Final
display, request, and returned-grid coordinates remain unresolved.

## Consequences

Benefits:

- preserves the difference between a fishing destination and an environmental
  model grid
- makes shoreline, inlet, sound, estuarine, inland, and offshore mismatches
  reviewable
- supports source-specific ingestion and lineage
- allows wave and sea-surface-temperature products to retain their actual grid
  relationships
- provides evidence needed for data quality and later explainable scoring
- permits spatial relationships to be revised without changing stable location
  identity

Costs and limitations:

- each location requires multiple spatial records
- a source or model change may require a new returned-grid relationship
- requested and returned coordinates must be captured and validated
- relationship status and limitations require ongoing maintenance
- the policy does not determine whether a candidate cell is accurate or fit
  for production use

Follow-up work:

- document candidate relationships for all five accepted locations
- select final coordinates only through separately authorized work
- validate returned cells against authoritative shoreline geometry
- define normalized storage for spatial relationships before ingestion
  implementation
- preserve relationship history when a coordinate, model, product, or source
  changes

## Alternatives considered

### One coordinate per location

A single coordinate would be simpler but would conceal the difference between
destination identity, request points, and returned model grids.

### Preserve request coordinates but not returned coordinates

This would record intended sampling locations but would not identify the grid
cells that actually produced the values.

### Use one returned marine coordinate for every marine field

This would incorrectly assume that wave and sea-surface-temperature products
share one grid and one spatial relationship.

### Preserve source-specific spatial relationships

This is the accepted choice. It preserves the evidence and limitations needed
for ingestion, validation, forecast history, data quality, and later
explainable scoring.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Roadmap: [Roadmap](../roadmap.md)
- Requirement: [Coastal location requirements](../requirements/coastal-locations.md)
- Requirement: [Fishing-condition requirements](../requirements/fishing-conditions.md)
- Existing decision: [Composite geographic model and initial locations](0002-composite-geographic-model-and-initial-locations.md)
- Evidence: [Coastal spatial relationships](../research/coastal-spatial-relationships.md)
