# Coastal source evaluation

## Purpose

This document preserves the reviewed stage 4 evidence for atmospheric, marine,
and tide-source responsibilities. It supports accepted decisions without
treating technical availability as accuracy or implementation.

The evaluation is limited to the five-location scope and environmental
requirements approved in stage 3. It is historical stage evidence, not a
current implementation inventory.

## Evaluation boundary

Issue #26 resolves the minimum first-release field contracts, coordinate
relationships, NOAA prediction relationships, tide phase, and deterministic
source-result validity rules.

It does not implement ingestion or establish accuracy. Observation
relationships, bias validation, fallback and precedence rules, warning and
forecast zones, marine run-history reconstruction, scoring, retention,
scheduling, publication, Azure architecture, and deployment remain unresolved
or deferred.

## Methodology

The evaluation combined:

- official source and model documentation
- official geographic and station metadata
- temporary Open-Meteo and NOAA CO-OPS API probes
- requested-to-returned coordinate comparison
- field availability and null-horizon checks
- repeated seven-day requests for the approved Open-Meteo relationships
- NOAA high and low event coverage checks

Documentation claims are direct evidence. Coordinate classification and coastal
representativeness are inference where the source does not state them.
Temporary responses were not written to tracked repository paths.

The initial source checkpoint was accessed on 2026-07-28. Issue #26 sources and
research evidence were reviewed on 2026-07-29.

## Sources

| Source | URL | Publication or update date | Use and limitation |
| --- | --- | --- | --- |
| Open-Meteo Weather API | https://open-meteo.com/en/docs | Not published | Weather fields, grid selection, timezone metadata, and forecast horizon |
| Open-Meteo GFS and HRRR API | https://open-meteo.com/en/docs/gfs-api | Not published | NBM, HRRR, and GFS resolution, horizon, and field availability |
| Open-Meteo Marine API | https://open-meteo.com/en/docs/marine-weather-api | Not published | Marine fields, models, grid selection, resolution, horizon, and coastal limitations |
| Open-Meteo Previous Runs API | https://open-meteo.com/en/docs/previous-runs-api | Not published | Weather forecasts from earlier lead-time offsets |
| Open-Meteo Single Runs API | https://open-meteo.com/en/docs/single-runs-api | Most models from 2026-04-02; ECMWF IFS from 2024-03-14 | Weather runs addressed by initialization time |
| NOAA CO-OPS Data API | https://api.tidesandcurrents.noaa.gov/api/prod/ | Not published | Prediction settings, high and low events, and response behavior |
| NOAA CO-OPS Metadata API | https://api.tidesandcurrents.noaa.gov/mdapi/prod/ | Not published | Station, reference-station, datum, offset, and multiplier metadata |
| NOAA tide-prediction locations | https://tidesandcurrents.noaa.gov/stations.html?type=Tide+Predictions | Current service; date not published | Harmonic and subordinate prediction relationships |

Official spatial sources and location evidence are recorded in
[Coastal spatial relationships](coastal-spatial-relationships.md).

## Atmospheric evaluation

| Selector | Documented resolution | Documented horizon | Evaluated limitation |
| --- | ---: | ---: | --- |
| `ncep_nbm_conus` | 2.5 km | About 11 days | Blended product without complete per-value upstream lineage |
| `ncep_hrrr_conus` | 3 km | 18 hours, or 48 hours for selected cycles | Cannot independently supply seven days |
| `ncep_gfs013` | About 13 km | 16 days | Did not supply every accepted field in the probe |
| `gfs_seamless` | 3 km to about 13 km | 16 days | Combines HRRR and GFS |
| `auto` | Model dependent | Up to 16 days | Does not identify the contributing model for each value |

The accepted first-release selector remains `ncep_nbm_conus`. It supplied the
complete accepted atmospheric field set, has the highest documented resolution
among the complete-field options evaluated, and covers the seven-day production
horizon.

NBM remains a blended product. The explicit selector improves request
provenance over `auto` but does not provide complete upstream run lineage.

## First-release atmospheric field contract

The `ncep_nbm_conus` request must contain:

- `wind_speed_10m`
- `wind_direction_10m`
- `wind_gusts_10m`
- `precipitation_probability`
- `precipitation`

`weather_code` is not part of the required first-release atmospheric field
contract. Its technical availability does not authorize ingestion or use.

## Marine evaluation

| Selector | Relevant fields | Documented resolution | Documented horizon |
| --- | --- | ---: | ---: |
| `meteofrance_wave` | Wave height, direction, and period | About 8 km | About 10 days |
| `meteofrance_currents` | Sea-surface temperature and other product fields | About 8 km | About 10 days |
| `ecmwf_wam` | Wave height, direction, and period | 9 km | 15 days |
| `ecmwf_wam025` | Wave height, direction, and period | About 25 km | 15 days |
| `ncep_gfswave016` | Wave height, direction, and period | About 16 km | 16 days |
| `ncep_gfswave025` | Wave height, direction, and period | About 25 km | 16 days |

The accepted first-release marine selectors remain:

- `meteofrance_wave` for:
  - `wave_height`
  - `wave_direction`
  - `wave_period`
- `meteofrance_currents` only for:
  - `sea_surface_temperature`

The `meteofrance_currents` request includes only
`sea_surface_temperature`, and that field is required for normalization.
Standard response metadata may also be present and does not violate the field
contract.

This selector does not authorize requesting or normalizing ocean current
velocity, ocean current direction, `sea_level_height_msl`, or another
environmental field from the product.

`models=auto` is not accepted. ECMWF WAM and other evaluated models remain
deferred alternatives, not fallbacks.

## Source contracts

| Source result | Selector or product | Required values |
| --- | --- | --- |
| Atmospheric | `ncep_nbm_conus` | `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, `precipitation_probability`, and `precipitation` |
| Wave | `meteofrance_wave` | `wave_height`, `wave_direction`, and `wave_period` |
| Sea-surface temperature | `meteofrance_currents` | `sea_surface_temperature` only |
| Tide predictions | NOAA CO-OPS `predictions`, `hilo`, `MLLW`, `gmt`, `metric` | Bounding high and low events sufficient to classify each valid time |

## Empirical seven-day results

Two requests for every approved Open-Meteo relationship returned:

- 168 source timestamps from `2026-07-28T00:00` through
  `2026-08-03T23:00`
- source timezone `America/New_York`
- UTC offset `-14400`
- ordered and unique source timestamps
- no nulls in the required fields
- the same parsed returned grid coordinate on both requests

These results demonstrate technical behavior during the July 2026 checkpoint.
They do not demonstrate accuracy, long-term reliability, or production fitness.

The durable seven-day rule operates on normalized time:

- normalize forecast valid times to UTC
- require exactly 168 unique, strictly ascending UTC instants
- require exactly one hour between consecutive UTC instants
- retain the source timezone and UTC offset as response metadata

## Tide-product evaluation

NOAA CO-OPS distinguishes tide predictions, observed water levels,
tidal-current predictions, and station and datum metadata.

SaltBytes will request the accepted prediction relationships with:

- product `predictions`
- interval `hilo`
- datum `MLLW`
- time zone `gmt`
- units `metric`

`metric` is the exact units value used in the successful issue #26 research
requests.

| Location | Prediction location | Identifier | Type | Relationship | Distance | Limitation |
| --- | --- | --- | --- | --- | ---: | --- |
| Jennette's Pier | Jennettes Pier, Nags Head (ocean) | `8652226` | Subordinate | Direct use | 0.448 km | Not an observed water level |
| Beach Access Ramp 72, Ocracoke Island | Ocracoke Inlet | `TEC2793` | Subordinate | Explicit transfer to ocean-side surf | 3.697 km | No inlet-current interpretation |
| Fort Macon State Park, ocean side | Atlantic Beach | `8656590` | Harmonic or reference | Explicit transfer to the nearby Atlantic beach | 1.321 km | Not a prediction at the destination |
| Bogue Inlet Pier | Bogue Inlet | `TEC2837` | Subordinate | Explicit transfer for phase at the pier | 6.164 km | Pier context only; no inlet-current interpretation |
| Fort Fisher State Recreation Area | Wilmington Beach | `8658559` | Subordinate | Explicit transfer from an ocean-facing relationship | 9.308 km | Material distance north of the destination |

The issue #26 request window covered 2026-07-27 through 2026-08-05. Each
relationship returned 39 ordered, unique, alternating high and low events,
including events before and after the seven-day forecast window.

The response contained prediction objects with time, value, and high or low
type. It did not necessarily echo the identifier, product, datum, interval,
time zone, or units. Those request values must therefore be retained as
provenance with the capture time.

## Tide phase

The minimum first-release phase is:

- `rising` when `low_time <= valid_time < next_high_time`
- `falling` when `high_time <= valid_time < next_low_time`

An exact low begins `rising`. An exact high begins `falling`. Each valid time
requires the preceding extremum and next opposite extremum. Missing bounding
events reject the affected tide result.

No project interpolation, correction factor, fallback station, observation
relationship, or tidal-current product is authorized.

Open-Meteo `sea_level_height_msl` remains generic modeled context referenced to
global mean sea level. It does not satisfy the authoritative locally referenced
tide requirement.

## Minimum result-validity boundary

Weather, wave, SST, and tide results are validated independently. A failed
result is rejected as a whole and is not partially normalized. Unrelated
successful source results are not rejected solely because another result
failed.

The affected result is rejected for:

- a missing required field
- a null or invalid required value in the production window
- a parsed returned coordinate that differs from its configured
  product-specific expected coordinate
- a missing approved relationship or static coastal-regime classification
- a configured model or product selector that differs from the request
- an invalid or unrecognized response timezone
- hourly valid times that fail the normalized UTC contract
- missing NOAA identifier, product, datum, interval, time zone, or units in
  retained request provenance
- a missing tide bounding event

Returned-coordinate equality is numeric equality after parsing. It does not
compare raw JSON text, and it has no geographic tolerance.

The SST result is invalid when `sea_surface_temperature` is missing, null, or
invalid, not merely because standard response metadata is present.

No fallback behavior is defined.

## Provenance and forecast revisions

Open-Meteo request provenance must retain:

- endpoint
- explicit model or product selector
- requested coordinate
- capture time

Response metadata must retain:

- returned coordinate
- source timezone
- UTC offset
- forecast valid time
- field units
- source-resolution limitations
- spatial-representativeness limitations

NOAA request provenance must retain:

- prediction-location or station identifier
- product
- datum
- interval
- time zone
- units
- capture time

The Open-Meteo responses tested did not include a contributing model key or
model initialization time. Explicit selectors improve request provenance
without providing complete run provenance.

Open-Meteo documents weather Previous Runs and Single Runs APIs. Equivalent
marine run-level reconstruction was not verified. SaltBytes can retain
successive captured marine forecasts but must not claim run-level lineage until
the source exposes or research establishes it.

## Remaining evidence gaps

The following remain unresolved or deferred:

- observation-station relationships
- forecast accuracy and observational bias validation
- source fallback and precedence behavior
- alternative marine-model adoption
- marine initialization or run-history reconstruction beyond exposed metadata
- warning, forecast, and safety-zone relationships
- scoring formulas, thresholds, and weights

Technical coverage does not resolve these topics.

## Related governance

- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Coastal location requirements](../requirements/coastal-locations.md)
- [Fishing-condition requirements](../requirements/fishing-conditions.md)
- [ADR 0004](../decisions/0004-spatial-coordinate-and-returned-grid-policy.md)
- [ADR 0005](../decisions/0005-open-meteo-model-strategy.md)
- [ADR 0006](../decisions/0006-authoritative-tide-product-responsibility.md)
- [ADR 0007](../decisions/0007-final-location-source-relationships.md)
- [ADR 0008](../decisions/0008-noaa-tide-relationships-and-phase.md)
- [ADR 0009](../decisions/0009-coastal-source-result-validity-rules.md)
