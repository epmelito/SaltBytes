# Coastal source evaluation

## Purpose

This document records the reviewed roadmap stage 4 evidence for atmospheric,
marine, and tide-source responsibilities. It supports the accepted decisions
without treating technical availability as accuracy or implementation.

The evaluation is limited to the five locations and environmental requirements
approved in roadmap stage 3. It focuses on ingestion feasibility, provenance,
forecast history, data quality, spatial relationships, and support for later
deterministic and explainable scoring.

## Evaluation boundary

The accepted locations are:

- Jennette's Pier
- Beach Access Ramp 72, Ocracoke Island
- Fort Macon State Park, ocean side
- Bogue Inlet Pier
- Fort Fisher State Recreation Area

Ramp 72 is an ocean-side surf context only. Bogue Inlet Pier is a pier context
only.

This checkpoint does not select final coordinates, NOAA stations, datums,
transfer rules, fallback behavior, scoring, retention, scheduling,
publication, Azure architecture, or ingestion implementation.

## Methodology

The evaluation combined:

- official source and model documentation
- official geographic and station metadata
- temporary Open-Meteo API probes
- requested-to-returned coordinate comparison
- field availability and null-horizon checks

Documentation claims are treated as direct evidence. Coordinate
classification and coastal representativeness are labeled as inference where
the source does not state them directly.

Temporary API responses were not written to tracked repository paths. All
external sources were accessed on 2026-07-28.

## Sources

| Source | URL | Publication or update date | Use and limitation |
| --- | --- | --- | --- |
| Open-Meteo Weather API | https://open-meteo.com/en/docs | Not published | Weather fields, best-match behavior, grid selection, and forecast horizon |
| Open-Meteo GFS and HRRR API | https://open-meteo.com/en/docs/gfs-api | Not published | NBM, HRRR, and GFS resolution, horizon, and field availability |
| Open-Meteo Marine API | https://open-meteo.com/en/docs/marine-weather-api | Not published | Marine fields, models, grid selection, resolution, horizon, and coastal limitations |
| Open-Meteo Previous Runs API | https://open-meteo.com/en/docs/previous-runs-api | Not published | Weather forecasts from earlier lead-time offsets |
| Open-Meteo Single Runs API | https://open-meteo.com/en/docs/single-runs-api | Most models from 2026-04-02; ECMWF IFS from 2024-03-14 | Weather model runs addressed by initialization time |
| NOAA CO-OPS Data API | https://api.tidesandcurrents.noaa.gov/api/prod/ | Not published | Prediction, observation, datum, and interval behavior |
| NOAA CO-OPS Metadata API | https://api.tidesandcurrents.noaa.gov/mdapi/prod/ | Not published | Station, reference-station, datum, and prediction-offset metadata |
| NOAA tide-prediction stations | https://tidesandcurrents.noaa.gov/stations.html?type=Tide+Predictions | Current service; date not published | Candidate harmonic and subordinate prediction locations |

The official spatial sources and location evidence are recorded in
[Coastal spatial relationships](coastal-spatial-relationships.md).

## Current ForecastOps baseline

The implemented weather pipeline currently requests:

- `temperature_2m`
- `precipitation_probability`
- `wind_speed_10m`

It preserves passing raw snapshots, normalized hourly records, pipeline and
snapshot metadata, quality results, and revision history for the implemented
fields.

It does not implement the accepted coastal location set, the additional
atmospheric fields, marine ingestion, sea-surface temperature, or locally
referenced tide data.

## Open-Meteo atmospheric evaluation

Open-Meteo documents the following North American models:

| Selector | Documented resolution | Documented horizon | Relevant limitation |
| --- | ---: | ---: | --- |
| `ncep_nbm_conus` | 2.5 km | 11 days | NBM is a blended product; temporal resolution becomes coarser later in the horizon |
| `ncep_hrrr_conus` | 3 km | 18 hours, or 48 hours for selected cycles | Too short to supply the current seven-day horizon independently |
| `ncep_gfs013` | about 13 km | 16 days | Not all accepted fields were available in the empirical probe |
| `gfs_seamless` | 3 km to about 13 km | 16 days | Combines HRRR and GFS rather than preserving one upstream model |
| `auto` | model dependent | up to 16 days | The response does not identify the contributing model for each value |

### Atmospheric field probe

The representative probe requested 384 hourly positions over 16 days near
Jennette's Pier.

| Selector | Wind speed | Wind direction | Wind gust | Precipitation probability | Precipitation amount | Weather code |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `auto` | 384 | 384 | 384 | 384 | 384 | 384 |
| `gfs_seamless` | 384 | 384 | 384 | 384 | 384 | 384 |
| `ncep_nbm_conus` | 283 | 283 | 283 | 283 | 283 | 283 |
| `ncep_hrrr_conus` | 67 | 67 | 67 | 283 | 67 | 67 |
| `ncep_gfs013` | 384 | 384 | 0 | 0 | 384 | 384 |

Counts show non-null technical availability only. They do not measure
forecast accuracy.

The extended precipitation-probability series returned with the HRRR selector
must not be attributed silently to native HRRR. Open-Meteo documents
precipitation probability as a derived or blended field whose availability
differs by model.

### Accepted atmospheric responsibility

The accepted first-release selector is:

- `ncep_nbm_conus`

It supplied the complete accepted atmospheric field set, has the
highest-resolution documented grid among the complete-field options evaluated,
and covers the current seven-day production horizon.

NBM remains a blended product. The named selector improves request provenance
over `auto`, but it does not provide complete per-value upstream model or run
lineage.

## Open-Meteo marine evaluation

Open-Meteo documents:

| Selector | Relevant fields | Documented resolution | Documented horizon |
| --- | --- | ---: | ---: |
| `meteofrance_wave` | Wave height, direction, and period | about 8 km | 10 days |
| `meteofrance_currents` | Sea-surface temperature and modeled sea-level fields | about 8 km | about 10 days |
| `ecmwf_wam` | Wave height, direction, and period | 9 km | 15 days |
| `ecmwf_wam025` | Wave height, direction, and period | about 25 km | 15 days |
| `ncep_gfswave016` | Wave height, direction, and period | about 16 km | 16 days |
| `ncep_gfswave025` | Wave height, direction, and period | about 25 km | 16 days |

The Marine API documentation lists `forecast_days` up to eight. A temporary
16-day request was accepted, but behavior beyond the documented parameter
range is not treated as a stable source contract.

### Marine field probe

The representative probe requested 384 hourly positions. Non-null counts were:

| Selector | Wave height | Wave direction | Wave period | Sea-surface temperature | Modeled MSL |
| --- | ---: | ---: | ---: | ---: | ---: |
| `auto` | 240 | 240 | 243 | 246 | 240 |
| `meteofrance_wave` | 240 | 240 | 243 | 0 | 0 |
| `ecmwf_wam` | 373 | 373 | 373 | 0 | 0 |
| `ecmwf_wam025` | 372 | 372 | 375 | 0 | 0 |
| `ncep_gfswave016` | 384 | 384 | 384 | 0 | 0 |
| `ncep_gfswave025` | 384 | 384 | 384 | 0 | 0 |
| `meteofrance_currents` | 0 | 0 | 0 | 246 | 240 |

These counts establish field availability and differing horizons. They do not
establish coastal accuracy or production fitness.

### Accepted marine responsibilities

The accepted first-release selectors are:

- `meteofrance_wave` for:
  - `wave_height`
  - `wave_direction`
  - `wave_period`
- `meteofrance_currents` only for:
  - `sea_surface_temperature`

Selecting `meteofrance_currents` does not authorize:

- ocean current velocity
- ocean current direction
- inlet-current requirements
- `sea_level_height_msl` as tide
- any other field from that product

The two products may return different grid cells. Their spatial relationships
must be preserved independently.

`models=auto` is not accepted for the first-release atmospheric or marine
strategy. ECMWF WAM and other evaluated models remain deferred alternatives,
not fallbacks.

## Tide-product evaluation

NOAA CO-OPS distinguishes:

- tide predictions
- observed water levels
- tidal-current predictions
- station and datum metadata

Subordinate tide-prediction locations apply published time and height offsets
from a reference station. NOAA requires subordinate tide predictions to use
Mean Lower Low Water and limits them to high and low predictions.

NOAA CO-OPS tide predictions are the accepted authoritative source family for
satisfying the locally referenced tide or water-level requirement.

Final prediction locations, stations, datums, transfer rules, interpolation
behavior, phase calculation, observation relationships, and tidal-current
products remain unresolved.

Open-Meteo `sea_level_height_msl` is referenced to global mean sea level.
Open-Meteo documents limited coastal accuracy for this field. It cannot satisfy
the authoritative locally referenced tide requirement. It may remain eligible
only as separately labeled modeled context.

## Requirement coverage

| Requirement | Accepted source or model responsibility | Implementation state | Limitation |
| --- | --- | --- | --- |
| Wind speed | Open-Meteo `ncep_nbm_conus` | Not implemented for the accepted locations | NBM is blended |
| Wind direction | Open-Meteo `ncep_nbm_conus` | Not implemented | NBM is blended |
| Wind gust | Open-Meteo `ncep_nbm_conus` | Not implemented | NBM is blended |
| Precipitation probability | Open-Meteo `ncep_nbm_conus` | Existing field uses no accepted explicit strategy yet | Upstream probability lineage is incomplete |
| Precipitation intensity or weather condition | Open-Meteo `ncep_nbm_conus` can supply both | Final field contract not implemented | At least one representation is required |
| Wave height | Open-Meteo `meteofrance_wave` | Not implemented | Candidate cells remain unresolved |
| Wave direction | Open-Meteo `meteofrance_wave` | Not implemented | Candidate cells remain unresolved |
| Wave period | Open-Meteo `meteofrance_wave` | Not implemented | Candidate cells remain unresolved |
| Sea-surface temperature | Open-Meteo `meteofrance_currents` | Not implemented | Selector authorizes SST only |
| Locally referenced tide or water-level phase | NOAA CO-OPS tide predictions | Not implemented | Station, datum, transfer, and phase rules remain unresolved |

## Provenance and forecast revisions

Future ingestion must preserve:

- endpoint
- explicit model or product selector
- requested coordinate
- returned coordinate
- capture time
- forecast valid time
- response timezone
- units
- source-resolution limitations
- spatial-representativeness limitations

The Open-Meteo live responses tested did not include a contributing model key
or model initialization time. Explicit selectors therefore improve request
provenance without providing complete run provenance.

Open-Meteo documents weather Previous Runs and Single Runs APIs. The Single
Runs API can address a weather model run by initialization time. Equivalent
marine run-level reconstruction was not verified.

ForecastOps can retain successive captured marine forecasts, but it must not
claim source run-level lineage until marine initialization or reconstruction
behavior is established.

## Source-fitness limitations

- Technical availability is not accuracy.
- Non-null fields are not evidence of coastal representativeness.
- Plausible Atlantic-facing cells are not approved production relationships.
- No accuracy or bias validation has been completed.
- No source fallback or precedence behavior is defined.
- No supplemental provider has been selected.
- No final coordinate, station, datum, or tide-transfer rule has been selected.

## Unresolved work

- Final display or destination coordinates remain unresolved.
- Final weather request coordinates remain unresolved.
- Final marine request coordinates remain unresolved.
- Final returned weather and marine grid relationships remain unresolved.
- Exact NOAA prediction-location, station, and datum mappings remain unresolved
  for each accepted location.
- Tide interpolation or station-to-location transfer rules remain unresolved.
- The tide or water-level phase calculation remains unresolved.
- Observation-station relationships remain unresolved.
- Accuracy and bias validation remain unresolved.
- Source fallback and precedence rules remain unresolved.
- Marine run-history reconstruction remains unresolved.

## Related governance

- [Project charter](../project-charter.md)
- [Scope register](../scope-register.md)
- [Roadmap stage 4](../roadmap.md#4-extend-coastal-data-source-ingestion)
- [Coastal location requirements](../requirements/coastal-locations.md)
- [Fishing-condition requirements](../requirements/fishing-conditions.md)
- [Spatial coordinate and returned-grid policy](../decisions/0004-spatial-coordinate-and-returned-grid-policy.md)
- [Open-Meteo model strategy](../decisions/0005-open-meteo-model-strategy.md)
- [Authoritative tide-product responsibility](../decisions/0006-authoritative-tide-product-responsibility.md)
