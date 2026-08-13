# Little Bridge seventh-location contract

## Status

Accepted

## Context

Decision 0012 established `sound-side` as the next location context and selected
Little Bridge Sound Access as planned location 7, while leaving its
location-source relationships unresolved. Bounded research now supports a
complete accepted environmental contract without treating this Roanoke Sound
access as a surf location or a pier.

## Decision

Little Bridge Sound Access is SaltBytes location 7, with fishing
context `sound-side`, in Roanoke Sound and the Northern North Carolina coast
project region. Its destination coordinate is `35.8980750, -75.6163500`: a
project-inferred representative facility coordinate, not a surveyed fishing-edge
point.

The orientation is `shore_normal_azimuth_degrees = 60`, rounded to the
existing nearest-five-degree convention at moderate confidence.
`pier_seaward_azimuth_degrees` is not applicable. Little Bridge must not be
modeled as a pier merely to satisfy the current implementation contract.

The approved environmental relationships are:

| Product | Request coordinate | Expected returned coordinate | Contract |
| --- | --- | --- | --- |
| Weather, `ncep_nbm_conus` | `35.8980750, -75.6163500` | `35.898766, -75.62099` | Approved atmospheric relationship; 0.425 km displacement. Returned model grid, not an observation at the access. |
| Water temperature, `meteofrance_currents` | `35.8980750, -75.6163500` | `35.875, -75.62499` | Approved representative sound-side SST context; 2.681 km displacement within the approximately 8 km source resolution. Not exact-site water temperature. |
| Waves, `meteofrance_wave` | `35.8980750, -75.6163500` | `35.875, -75.62499` | Approved modeled sound wave/chop context; 2.681 km displacement within the approximately 8 km source resolution. Strong representativeness limitation: not fishing-edge wave height, breaker height, or exact local chop. |

The water-temperature and wave returns remain supportable because they are in
the same materially relevant Roanoke Sound regime and their displacement is
reasonable relative to source resolution. Each product retains its own
relationship and limitation.

NOAA subordinate prediction station `8652591`, Roanoke Sound Channel, is the
approved transferred astronomical high/low tide relationship. Its station
coordinate is `35.7983, -75.5833`, approximately 11.487 km from the destination.
It references station `8652587` with `type = S`,
`timeOffsetHighTide = 97`, `timeOffsetLowTide = 77`,
`heightOffsetHighTide = 0.47`, `heightOffsetLowTide = 0.14`, and
`heightAdjustedType = R`. The existing `predictions`, `hilo`, `MLLW`, `gmt`,
and `metric` request contract applies. This is not a direct Little Bridge
water-level observation, actual water level, or current measurement.

Current support and modeled sea level are not approved. Although the reviewed
marine product returned current and sea-level fields, site representativeness
for currents is unresolved and NOAA predictions remain the approved water-level
timing relationship.

The frozen observation-source posture remains Yellow overall for Little Bridge,
with the structured Outer Banks This Week production path Red. Exact-site
fishing evidence is useful, but no automated exact-site observation source is
approved. That uncertainty does not block the environmental location contract.

## Consequences

Later implementation must extend the configured fishing-context contract for
`sound-side`, preserve a not-applicable pier orientation, and implement only
these product-specific relationships and limitations. It must retain NOAA
subordinate tide-transfer semantics, leave currents unsupported, and not make
exact-site observation automation a prerequisite.

This decision does not implement location 7 or design its implementation.

## Alternatives considered

### Replace Little Bridge with Bebop's Multi-Use Pier

Rejected. Bebop had a materially more local NOAA tide relationship, but did not
provide a materially stronger overall location contract.

### Treat Little Bridge as surf or pier

Rejected. Neither context represents the sound-side fishing setting or its
orientation honestly.

### Require currents or automated exact-site observations

Rejected. Neither relationship is sufficiently supported, and neither is needed
to scope the approved environmental location contract.

## Related governance

- [Sound-side location expansion](0012-sound-side-location-expansion.md)
- [Spatial coordinate and returned-grid relationship policy](0004-spatial-coordinate-and-returned-grid-policy.md)
- [Little Bridge location evidence](../research/little-bridge-location-evidence.md)
- [Fishing observation source suitability assessment](../research/fishing-observation-source-suitability.md)
