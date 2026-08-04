# Fishing-condition requirements

## Status

This document defines the approved environmental baseline established before
the current scoring milestone. It does not define a species scoring
methodology, formula, threshold, weight, or implementation.

The product direction for species conditions scores is governed by
[decision 0010](../decisions/0010-research-backed-fishing-score-direction.md)
and the
[species conditions scoring requirements](species-condition-scoring.md).

## Purpose

SaltBytes should support explainable comparisons of upcoming environmental
windows for general recreational coastal anglers.

The first release covers surf and publicly accessible fixed fishing pier
contexts. Windows may be compared only within the same context.

The requirements describe environmental conditions, not expected catch,
species suitability, navigation suitability, or a guarantee of fishing
success.

## Interpretation boundaries

Fishing-quality information and safety information serve different purposes.

Environmental conditions may contribute to deterministic and explainable
species conditions scores under the separately approved scoring direction.
This document does not define the formulas, thresholds, weights, or
species-specific interpretation.

Safety-only information must:

- remain distinguishable from fishing-quality information
- retain official source and valid-time context
- not be converted into a fishing-success claim
- not be presented as a replacement for official guidance
- not be silently incorporated into a fishing-quality score

## Requirement classifications

| Classification | Meaning |
| --- | --- |
| Required environmental baseline | Required for the first-release environmental baseline, independently of whether a provider or implementation has been selected |
| Optional context | Useful explanatory context but not required for the first usable baseline |
| Safety-only | Official safety or access information that must remain separate from fishing-quality interpretation |
| Deferred | Recognized but outside the first-release baseline |
| Excluded | Outside the approved product boundary |

An accepted requirement does not imply that a provider has been selected or
that the corresponding field is implemented.

## Metric inclusion rule

A metric belongs in the first-release baseline only when it supports one or
more of:

- comparison of environmental windows
- spatial interpretation
- source validation
- forecast-revision analysis
- deterministic and explainable scoring in a later stage
- clear separation of safety information

## Required environmental baseline

### Location and fishing-context identity

Each condition record must identify:

- the composite coastal location
- its stable identifier
- its `surf` or `pier` context
- the geographic or sampling relationship represented by the data

This identity is required to enforce within-context comparison.

### Time and provenance

Each forecast value must retain:

- forecast valid time
- capture time
- timezone
- source and model provenance
- pipeline-run relationship

These fields are needed to distinguish when a forecast applies from when it was
collected and to trace later forecast revisions.

### Wind

The required environmental baseline includes:

- wind speed
- wind direction
- wind gust

The current pipeline implements only wind speed at 10 metres. Direction and
gust are accepted requirements but remain unimplemented.

### Precipitation and weather condition

The required environmental baseline includes:

- precipitation probability
- at least one precipitation-intensity or weather-condition representation,
  such as precipitation amount or a documented weather condition

The exact representation must be resolved through source evaluation and data
modeling. This requirement does not select a provider field or threshold.

### Waves

The required environmental baseline includes:

- wave height
- wave direction
- wave period

Swell and wind-wave decomposition remains optional context rather than a
first-release requirement.

### Sea-surface temperature

Sea-surface temperature is part of the required environmental baseline.

The source and spatial representativeness of sea-surface temperature must be
evaluated for each location. A coarse offshore grid value must not be described
as a direct measurement at a beach or pier.

### Tide or water-level phase

A tide or water-level phase tied to an appropriate local reference is part of
the required environmental baseline.

This requirement does not select:

- a provider
- a station
- a datum
- an interpolation method
- a phase-calculation method
- a source-authority rule

Those relationships must be documented before implementation.

### Forecast revision history

The platform must preserve enough source and capture identity to show how a
forecast for the same location and valid time changes across captures.

This requirement extends the current revision concept. It does not establish a
retention period.

### Data-quality status

Published or modeled conditions must expose whether required source data:

- passed applicable validation
- is missing
- is stale
- is invalid
- is unavailable
- is not applicable to the fishing context
- has an unresolved spatial or reference relationship

Detailed checks and thresholds remain implementation decisions.

## Optional context

The following may be added when evidence, provider capability, and implementation
scope support them:

- air temperature
- apparent temperature
- relative humidity
- dew point
- atmospheric pressure
- cloud cover
- daylight
- visibility outside official safety interpretation
- swell decomposition
- recent observations

Optional context must not become a hidden prerequisite for scoring or
publication without an approved scope change.

## Safety-only information

The following are safety-only:

- rip-current outlook
- beach hazards
- lightning and thunderstorm hazards
- official marine warnings
- fog advisories
- beach flags
- closures
- storm-surge products

The National Weather Service describes rip currents as hazardous currents and
publishes rip-current and beach-hazard information as safety guidance. Such
products must retain their official meaning rather than being reinterpreted as
fishing-quality recommendations.

Safety-only information may affect whether the platform displays a warning or
suppresses a recommendation after that behavior is explicitly approved. No
such behavior is approved by this requirements document.

Sources:

- [NWS rip-current safety frequently asked questions](https://www.weather.gov/safety/ripcurrent-faqs),
  publication or update date not shown, accessed 2026-07-28
- [NWS Wilmington rip-current information](https://www.weather.gov/ilm/ripcurrents),
  publication or update date not shown, accessed 2026-07-28

## Deferred conditions

The following remain deferred:

- salinity
- turbidity
- dissolved oxygen
- chlorophyll
- river discharge
- biological variables
- catch history
- lunar phase
- bathymetry and sandbar state
- score formulas, thresholds, weights, and validation methods

Species-specific variables and interpretations are governed by the approved
species research and scoring requirements. Additional data inputs remain
deferred until separately approved.

## Excluded interpretations

The first-release requirements exclude:

- guarantees of fishing success
- predicted catch probabilities without an approved evidence basis
- opaque AI-generated fishing scores
- unsupported species presence, bite, or success recommendations
- navigation suitability
- replacement of official marine or beach-safety guidance
- direct ranking of surf windows against pier windows

## Current implementation mapping

Repository evidence is authoritative for implemented behavior.

| Requirement | Current implementation | Gap |
| --- | --- | --- |
| Location identity | Configured location identifiers, names, latitude, longitude, and timezone | No composite coastal-location model or fishing-context field |
| Valid time | Implemented as hourly forecast time | No complete coastal-condition model |
| Capture and run identity | Pipeline run and snapshot metadata are implemented | Must be carried consistently into future coastal models |
| Source provenance | Open-Meteo is the implemented forecast source | No source-authority model |
| Wind speed | `wind_speed_10m` | Direction and gust are accepted but unimplemented requirements |
| Precipitation probability | `precipitation_probability` | No precipitation-intensity or weather-condition representation is implemented |
| Air temperature | `temperature_2m` | Optional context already ingested |
| Waves | Not implemented | Height, direction, and period are accepted but unimplemented requirements |
| Sea-surface temperature | Not implemented | Source and spatial relationship require evaluation |
| Tide or water-level phase | Not implemented | Local reference, provider, and phase method remain unresolved |
| Revision history | Revision changes exist for the three implemented hourly fields | Future required coastal fields are not covered |
| Data quality | Payload checks and persisted quality results are implemented | Coastal, reference, freshness, and context checks are not defined |
| Safety products | Not implemented | Provider and display behavior remain deferred |

Verified repository evidence:

- `config/dev.yml`
- `config/test.yml`
- `config/prod.yml`
- `src/saltbytes/config.py`
- `src/saltbytes/api.py`
- `src/saltbytes/database.py`
- `src/saltbytes/pipeline.py`
- `src/saltbytes/quality.py`
- relevant tests under `tests/`

## Open-Meteo baseline evaluation

Open-Meteo remains the existing baseline source to evaluate. It is not accepted
by this document as the authoritative marine, tide, current, or safety
provider.

### Implemented now

The current pipeline requests and stores:

- `temperature_2m`
- `precipitation_probability`
- `wind_speed_10m`
- hourly valid times

It also records pipeline and snapshot metadata, quality results, and revision
changes for the three implemented fields.

### Available but not implemented

Open-Meteo weather documentation lists potentially relevant fields including:

- wind direction at 10 metres
- wind gusts at 10 metres
- precipitation amount
- rain and showers
- weather code
- apparent temperature
- relative humidity
- dew point
- pressure
- cloud cover
- visibility
- sunshine or daylight-related values

Open-Meteo marine documentation lists potentially relevant fields including:

- wave height, direction, and period
- swell height, direction, and period
- wind-wave height, direction, and period
- sea-surface temperature
- ocean-current velocity and direction
- sea-level height relative to mean sea level

Availability in an API does not establish fitness, accuracy, spatial
representativeness, source authority, or approval for implementation.

### Unsupported or uncertain

Open-Meteo does not by itself establish:

- an authoritative locally referenced tide prediction
- an appropriate tide station or datum relationship
- authoritative rip-current outlooks
- official beach-hazard products
- official marine warnings
- beach flags
- access closures
- storm-surge authority
- pier-scale or beach-scale observations
- location-specific accuracy at shorelines or structures

Its marine documentation describes model-grid data with model-dependent spatial
resolution and cautions that coastal sea-level values have limited accuracy.
Those limitations require later source and location evaluation.

Sources:

- [Open-Meteo Weather Forecast API](https://open-meteo.com/en/docs),
  publication or update date not shown, accessed 2026-07-28
- [Open-Meteo Marine Weather API](https://open-meteo.com/en/docs/marine-weather-api),
  publication or update date not shown, accessed 2026-07-28
- [NOAA Tides and Currents frequently asked questions](https://tidesandcurrents.noaa.gov/faq.html),
  publication or update date not shown, accessed 2026-07-28

## Provider and scoring boundary

This requirements document does not:

- accept Open-Meteo as the authoritative marine, tide, current, or safety
  provider
- select a supplemental provider
- define final source-authority or fallback rules
- define species score inputs, formulas, thresholds, or weights
- determine whether safety products suppress or modify recommendations
- define retention or scheduling
- define publication, API, dashboard, Azure, or deployment architecture

## Evidence rules

A condition requirement must:

- be traceable to approved product direction or reviewed evidence
- distinguish direct source evidence from project inference
- preserve safety and fishing-quality boundaries
- state spatial, temporal, and reference limitations
- avoid fishing-success claims
- avoid treating API availability as provider acceptance

## Related governance

- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Scope register](../scope-register.md)
- [Coastal location requirements](coastal-locations.md)
- [First-release user and fishing-context decision](../decisions/0001-first-release-user-and-fishing-context.md)
- [First-release environmental requirement baseline decision](../decisions/0003-first-release-environmental-requirement-baseline.md)
- [Research backed species conditions scoring direction](../decisions/0010-research-backed-fishing-score-direction.md)
- [Species conditions scoring requirements](species-condition-scoring.md)
