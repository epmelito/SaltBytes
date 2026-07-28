# Minimum coastal source-result validity rules

## Status

Accepted

## Context

The accepted first-release source decisions define separate atmospheric, wave,
sea-surface-temperature, and tide products. Implementation needs a minimum set
of deterministic checks that prevents incomplete or spatially inconsistent
source results from being normalized.

The current ForecastOps pipeline already applies quality checks before passing
raw snapshots and normalized forecasts are written. The coastal rules extend
that boundary without introducing partial normalization, fallbacks,
generalized validation frameworks, or unsupported tolerances.

The first-release production horizon is seven days.

## Decision

ForecastOps will validate atmospheric, wave, sea-surface-temperature, and tide
results independently.

A whole-source-result rejection applies only to the affected weather, wave,
sea-surface-temperature, or tide result. No values from that rejected result
are normalized. An unrelated successful source result is not rejected solely
because another source failed.

### Required source contracts

The atmospheric request must use selector `ncep_nbm_conus` and request:

- `wind_speed_10m`
- `wind_direction_10m`
- `wind_gusts_10m`
- `precipitation_probability`
- `precipitation`

The wave request must use selector `meteofrance_wave` and request:

- `wave_height`
- `wave_direction`
- `wave_period`

The sea-surface-temperature request must use selector
`meteofrance_currents`, request only `sea_surface_temperature`, and require
that field for normalization. Standard response metadata does not violate this
contract.

This selector does not authorize requesting or normalizing ocean current
velocity, ocean current direction, `sea_level_height_msl`, or another
environmental field from that product.

The tide request must use the configured NOAA prediction-location identifier,
product `predictions`, interval `hilo`, datum `MLLW`, time zone `gmt`, and
units `metric`.

### Hourly valid-time contract

For each hourly Open-Meteo result:

- normalize forecast valid times to UTC
- require exactly 168 unique, strictly ascending UTC instants
- require exactly one hour between consecutive UTC instants
- retain the source timezone and UTC offset as response metadata

### Rejection conditions

The affected source result is rejected when any of these conditions applies:

- a required field is absent
- a required field is null or invalid inside the 168-hour production window
- the parsed returned latitude or longitude differs from the configured
  product-specific expected returned coordinate
- the approved relationship or static coastal-regime classification is absent
- the configured model or product selector differs from the request
- the response timezone is invalid or unrecognized
- normalized UTC valid times violate the hourly valid-time contract
- the NOAA identifier, product, datum, interval, time zone, or units is absent
  from retained request provenance
- a tide valid time lacks the preceding extremum and next opposite extremum
  required to determine its phase

Coordinate equality is numeric equality after parsing. It is not raw JSON-text
or decimal-string equality. No geographic tolerance or fallback coordinate is
defined.

The SST result is rejected when its required `sea_surface_temperature` field is
missing, null, or invalid. It is not rejected merely because standard provider
metadata is also present.

These checks do not establish accuracy, bias, service reliability, or safety
authority. They establish only that a result satisfies its approved
first-release source, temporal, spatial, and provenance contract.

### Request provenance

Each Open-Meteo request must retain:

- configured model or product selector
- requested coordinate
- capture time

Each NOAA tide request must retain:

- prediction-location or station identifier
- product
- datum
- interval
- time zone
- units
- capture time

Returned coordinates, response timezone and UTC offset, source timestamps, and
other standard response metadata must remain attributable to the corresponding
captured source result.

## Consequences

Incomplete, spatially unexpected, or untraceable results cannot enter
normalization as though they satisfied the approved contract.

Weather, wave, sea-surface-temperature, and tide failures remain independently
observable. No partial normalization occurs within a rejected result, and a
failure does not invalidate unrelated successful source results.

No runtime fallback, tolerance tuning, geographic inference, or alternate-model
selection is authorized.

Further accuracy, observation, fallback, retention, and operational policies
require separate evidence and approval.

## Alternatives considered

Normalize available fields and mark only missing values. This was rejected
because the accepted products have small explicit field contracts, and partial
normalization would create records that do not satisfy those contracts.

Reject the complete multi-source location run when any one source fails. This
was rejected because a failure in one independently captured product does not
prove the other source results invalid.

Allow a coordinate-distance tolerance. This was rejected because the evaluated
relationships returned stable numeric coordinates and no evidence establishes
a safe tolerance.

Automatically retry with alternate coordinates, models, or stations. This was
rejected because no fallback or precedence policy has been approved.

## Related governance

- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Scope register](../scope-register.md)
- [Fishing-condition requirements](../requirements/fishing-conditions.md)
- [Coastal source evaluation](../research/coastal-source-evaluation.md)
- [Coastal spatial relationships](../research/coastal-spatial-relationships.md)
- [ADR 0004](0004-spatial-coordinate-and-returned-grid-policy.md)
- [ADR 0005](0005-open-meteo-model-strategy.md)
- [ADR 0006](0006-authoritative-tide-product-responsibility.md)
