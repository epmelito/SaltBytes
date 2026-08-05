# First-release NOAA tide relationships and phase

## Status

Accepted

## Context

ADR 0006 assigns NOAA CO-OPS tide predictions responsibility for satisfying the
locally referenced tide or water-level requirement. It left prediction
locations, datums, station-to-location transfer relationships, and tide-phase
logic unresolved.

Issue #26 evaluated NOAA CO-OPS prediction relationships for the five approved
locations. A direct prediction location is not available at every fishing
location. The first release therefore needs explicit direct-use or transfer
relationships and one minimum deterministic tide-phase representation.

This decision concerns tide predictions. It does not authorize observed water
levels, tidal-current products, project interpolation, correction factors, or
Open-Meteo modeled mean-sea-level output as authoritative local tide.

## Decision

SaltBytes will request NOAA CO-OPS tide predictions with:

- product `predictions`
- interval `hilo`
- datum `MLLW`
- time zone `gmt`
- units `metric`

The first-release relationships are:

| Fishing location | NOAA prediction location | Identifier | Relationship | Distance | Published relationship data | Limitation |
| --- | --- | --- | --- | ---: | --- | --- |
| Jennette's Pier | Jennettes Pier, Nags Head (ocean) | `8652226` | Direct use | 0.448 km | Subordinate to `8651370`; high time -5 minutes, low time +1 minute; high multiplier 1.04, low multiplier 1.43 | Prediction behavior remains distinct from observed water levels |
| Beach Access Ramp 72, Ocracoke Island | Ocracoke Inlet | `TEC2793` | Explicit transfer to the southern ocean-side surf location | 3.697 km | Subordinate to `8654400`; high time +9 minutes, low time +11 minutes; high multiplier 0.63, low multiplier 0.83 | Transfer does not authorize inlet-current interpretation |
| Fort Macon State Park, ocean side | Atlantic Beach | `8656590` | Explicit transfer to the nearby Atlantic-facing beach location | 1.321 km | Harmonic or reference prediction; no subordinate offsets | It is not a prediction location at the park destination |
| Bogue Inlet Pier | Bogue Inlet | `TEC2837` | Explicit transfer for tide phase at the pier | 6.164 km | Subordinate to `8654400`; high time +13 minutes, low time +15 minutes; high multiplier 0.73, low multiplier 0.83 | Transfer does not authorize inlet-current interpretation |
| Fort Fisher State Recreation Area | Wilmington Beach | `8658559` | Explicit transfer from the nearest reviewed ocean-facing relationship | 9.308 km | Subordinate to `8654400`; high time +18 minutes, low time +10 minutes; high multiplier 1.40, low multiplier 1.25 | The prediction relationship is materially north of the destination |

The retained relationship metadata must include:

- NOAA identifier
- product
- datum
- interval
- time zone
- units
- reference station where NOAA defines one
- published time offsets
- published height multipliers where applicable
- distance to the fishing location
- coastal relationship
- direct-use or transfer classification
- known limitation

No additional project interpolation, correction factor, fallback station, or
alternate-station selection is authorized. NOAA's published subordinate
prediction relationships are source attributes, not project-defined transfer
logic.

The minimum first-release tide phase is binary:

- `rising` when `low_time <= valid_time < next_high_time`
- `falling` when `high_time <= valid_time < next_low_time`

An exact low-water event begins `rising`. An exact high-water event begins
`falling`.

Each forecast valid time requires the preceding high or low extremum and the
next opposite extremum. If those bounding events are unavailable, the affected
tide result is rejected.

The NOAA prediction-location or station identifier, product, datum, interval,
time zone, units, and capture time must be retained as request provenance
because the response does not necessarily echo them.

This phase is a deterministic representation of the selected prediction
relationship. It is not an observation, tidal-current estimate, safety
interpretation, or fishing-quality score.

## Consequences

The five locations have one explicit NOAA prediction relationship and datum for
first-release implementation.

The phase result is reproducible from retained NOAA high and low predictions
without a generalized interpolation framework. Transfer relationships and
their limitations remain visible instead of being presented as direct local
measurements.

Requests must include sufficient preceding and following events to bound every
forecast valid time. Missing bounding events reject the affected tide result.
They do not trigger a fallback station or inferred phase.

Observed water-level relationships, tidal-current products, alternate stations,
fallbacks, and validation against observations remain outside this decision.

## Alternatives considered

Use Open-Meteo `sea_level_height_msl`. This was rejected because it is generic
modeled mean-sea-level context and does not satisfy the accepted locally
referenced tide requirement.

Require a direct NOAA prediction location at every fishing destination. This
was rejected because authoritative direct relationships are not available for
all five locations.

Create a generalized station interpolation or transfer model. This was rejected
because NOAA already publishes defined reference and subordinate prediction
relationships, and no first-release requirement supports additional project
correction logic.

Use a continuous tide-stage percentage. This was rejected because the accepted
requirement needs a minimum explainable phase, and binary rising or falling is
sufficient without inventing another calculation model.

## Related governance

- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Fishing-condition requirements](../requirements/fishing-conditions.md)
- [Coastal source evaluation](../research/coastal-source-evaluation.md)
- [Coastal spatial relationships](../research/coastal-spatial-relationships.md)
- [ADR 0006](0006-authoritative-tide-product-responsibility.md)
