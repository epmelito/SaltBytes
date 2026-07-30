# First-release environmental requirement baseline

## Status

Accepted

## Context

SaltBytes needs an environmental requirement baseline before evaluating
coastal sources or implementing ingestion.

The current pipeline implements air temperature, precipitation probability,
and wind speed from Open-Meteo. It retains passing raw snapshots, normalized
hourly values, run metadata, quality results, and revision changes for those
fields.

Comparisons for surf and publicly accessible fixed fishing pier locations
require additional marine, timing, provenance, and quality information. Safety
products have a different authority and purpose from fishing-quality
conditions and must remain distinguishable.

This decision establishes requirement categories. It does not select providers
or define scoring.

Each required metric supports at least one of environmental-window comparison,
spatial interpretation, source validation, forecast-revision analysis, later
deterministic and explainable scoring, or clear safety separation.

## Decision

The first-release required environmental baseline will include:

- location and fishing-context identity
- forecast valid time
- capture time
- timezone
- source and model provenance
- wind speed, direction, and gust
- precipitation probability
- at least one precipitation-intensity or weather-condition representation,
  such as precipitation amount or a documented weather condition
- wave height, direction, and period
- sea-surface temperature
- tide or water-level phase tied to an appropriate local reference
- forecast revision history
- data-quality status

Optional context will include:

- air temperature
- apparent temperature
- humidity
- dew point
- pressure
- cloud cover
- daylight
- visibility outside official safety interpretation
- swell decomposition
- recent observations

Safety-only information will include:

- rip-current outlook
- beach hazards
- lightning and thunderstorm hazards
- official marine warnings
- fog advisories
- beach flags
- closures
- storm-surge products

Deferred conditions will include:

- salinity
- turbidity
- dissolved oxygen
- chlorophyll
- river discharge
- biological variables
- catch history
- lunar phase
- bathymetry and sandbar state
- score formulas, thresholds, and weights

Excluded interpretations will include:

- guarantees of fishing success
- predicted catch probabilities without an approved evidence basis
- opaque AI-generated fishing scores
- species recommendations
- navigation suitability
- replacement of official marine or beach-safety guidance
- direct ranking of surf windows against pier windows

Open-Meteo will remain the baseline source to evaluate because it is already
used by the current weather pipeline. It is not accepted by this decision as
the authoritative marine, tide, current, or safety provider.

Safety-only information will remain separate from fishing-quality
interpretation and will not silently become a scoring input.

An accepted environmental requirement does not imply that a provider has been
selected or that its corresponding field has been implemented.

## Consequences

Benefits:

- establishes a reviewable minimum environmental baseline
- extends current weather capability without describing unimplemented fields as
  current
- preserves valid-time, capture-time, source, revision, and quality traceability
- separates official safety products from fishing-quality information
- enables bounded provider evaluation in later work

Costs and limitations:

- the baseline requires data not implemented by the current pipeline
- multiple sources may be needed
- local tide or water-level relationships remain unresolved
- model-grid marine data may not represent a beach or pier directly
- optional information may remain unavailable in the first implementation
- the baseline does not determine how conditions affect a score

Follow-up work:

- evaluate source fitness and authority
- document display, request, sampling, station, datum, and zone relationships
  for each location
- evaluate source resolution and spatial representativeness
- define normalized and historical models
- define quality behavior
- resolve scoring only in its authorized roadmap stage
- preserve deferred variables unless separately approved

## Alternatives considered

### Use only currently implemented weather fields

This would minimize implementation work but would not meet the approved coastal
condition baseline.

### Require every available environmental variable

This would exceed the bounded first-release purpose and introduce variables
without demonstrated necessity.

### Mix official safety products into fishing-quality scoring

This would obscure the distinction between safety guidance and fishing-quality
recommendations and is not approved.

### Use a classified environmental baseline

This is the accepted choice. It separates the required environmental baseline
from optional context, safety-only information, deferred conditions, and
excluded interpretations while leaving providers and scoring unresolved.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Scope: [Scope register](../scope-register.md)
- Roadmap stage: [Stage 3](../roadmap.md#3-define-coastal-locations-and-fishing-condition-requirements)
- Requirements: [Fishing-condition requirements](../requirements/fishing-conditions.md)
- Requirements: [Coastal location requirements](../requirements/coastal-locations.md)
- Related decision: [First-release user and fishing-context boundary](0001-first-release-user-and-fishing-context.md)
- Related decision: [Composite geographic model and initial locations](0002-composite-geographic-model-and-initial-locations.md)
