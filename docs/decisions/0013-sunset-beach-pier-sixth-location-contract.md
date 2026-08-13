# Sunset Beach Pier sixth-location contract

## Status

Accepted

## Context

Sunset Beach Pier is the planned sixth SaltBytes location. First-release
location decisions remain frozen history and do not establish its source or
spatial relationships. Each environmental product requires its own supported
request and returned-grid relationship.

## Decision

SaltBytes will treat Sunset Beach Pier as location 6 with fishing context
`pier`, southern North Carolina region, and an Atlantic-facing coastal regime.
Its published NOAA destination coordinate is `33.8650000, -78.5067000`.

The approved environmental relationships are:

| Product | Request coordinate | Expected returned coordinate | Contract |
| --- | --- | --- | --- |
| Weather, `ncep_nbm_conus` | `33.8650000, -78.5067000` | `33.875553, -78.49414` | Weather request at the destination. |
| Waves, `meteofrance_wave` | `33.8389394, -78.4982931` | `33.791664, -78.45833` | Marine request about 3 km seaward along the reviewed shore normal. |
| SST, `meteofrance_currents` | `33.8389394, -78.4982931` | `33.875, -78.45833` | Same supported marine request coordinate as waves. |

NOAA station `8659897`, Sunset Beach Pier, is the direct tide-prediction
relationship using the existing `predictions`, `hilo`, `MLLW`, `gmt`, and
`metric` contract.

The reviewed orientation metadata is
`shore_normal_azimuth_degrees = 165` and
`pier_seaward_azimuth_degrees = 180`, each at moderate confidence under the
existing nearest-five-degree convention. The separate estuarine DCM feature
named `Sunset Beach Boating Access & Fishing Pier` is not this location.

Sunset Beach Pier observations are Green under the current low-frequency,
factual-extraction, attribution, and no-circumvention posture. This dated,
conditional classification follows current crawler-policy evidence and does
not create permanent authorization.

Spanish mackerel applicability is approved for this ocean pier. Methodology
`spanish-mackerel-v1.1.0` adds this eligibility only; it retains every
calculation and interpretation rule from `spanish-mackerel-v1.0.0`.

## Consequences

This contract is sufficient to define the complete sixth-location implementation
package without reusing another location's marine relationships. It does not
implement the location, add fallback geography, or approve other locations.

Product-specific returned grids and their spatial-representativeness limits
remain visible rather than being treated as destination observations. Future
source-policy changes require a bounded suitability re-review.

## Alternatives considered

### Reuse another ocean pier's relationships

Rejected. Existing spatial policy requires evidence for each source product and
location relationship.

### Use the estuarine DCM fishing-pier feature

Rejected. It is a separate facility north of the oceanfront destination.

### Retain the previous Yellow observation classification

Rejected. Current reviewed crawler-policy evidence resolves the prior
environment-specific retrieval blocker under the stated posture.

## Related governance

- [Spatial coordinate and returned-grid relationship policy](0004-spatial-coordinate-and-returned-grid-policy.md)
- [Final first-release location-to-source relationships](0007-final-location-source-relationships.md)
- [First-release NOAA tide relationships and phase](0008-noaa-tide-relationships-and-phase.md)
- [Spanish mackerel methodology](../requirements/spanish-mackerel-conditions-score.md)
- [Sunset Beach Pier evidence](../research/sunset-beach-pier-location-evidence.md)
- [Current roadmap](../roadmap.md)
