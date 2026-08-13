# Little Bridge location evidence

## Status

Completed bounded evidence for the accepted seventh-location contract, assessed
2026-08-13. This is not implementation configuration or a substitute for the
accepted decision record.

## Candidate and destination evidence

Little Bridge Sound Access remains the selected planned location 7 and first
`sound-side` context, in Roanoke Sound and the Northern North Carolina coast
project region. Bebop's Multi-Use Pier was a genuine comparison: its NOAA Manns
Harbor station `8652247` was approximately 1.005 km away, materially closer than
Little Bridge's tide transfer. That advantage did not outweigh Little Bridge's
approved sound-side rationale, named-site observation value, and reviewed
weather and marine relationships.

The destination `35.8980750, -75.6163500` is a project-inferred representative
facility coordinate from separately published Little Bridge Access Park entrance
GPS evidence, visually corroborated against current map imagery of the Town
facility. It identifies the public fishing destination, not a surveyed point on
the fishing edge or structure, and is not a universal sampling coordinate.

## Orientation evidence

Reviewed north-up imagery shows the fishing structure substantially along the
shoreline rather than projecting seaward. The project inference is an open-water
normal of approximately 60 degrees true, rounded to the nearest five degrees at
moderate confidence. It is analytical directional context, not survey-grade
geometry; a pier seaward azimuth is not applicable.

## Environmental probe evidence

| Relationship | Bounded result | Limitation |
| --- | --- | --- |
| Weather, `ncep_nbm_conus` | Request `35.8980750, -75.6163500` returned `35.898766, -75.62099`, a 0.425 km displacement, with 24 hourly values. | Atmospheric model grid, not an access observation. |
| SST, `meteofrance_currents` | Request `35.8980750, -75.6163500` returned `35.875, -75.62499`, a 2.681 km displacement, with 24 non-null SST values. | Approximately 8 km source resolution; same Roanoke Sound regime supports representative context, not exact-site temperature. |
| Waves, `meteofrance_wave` | The same request returned `35.875, -75.62499`, a 2.681 km displacement, with 24 non-null wave-height values. | Approximately 8 km model; supports modeled sound wave/chop context, not fishing-edge wave height, breaker height, or exact local chop. |

The marine standard applied here is same materially relevant regime, reasonable
displacement relative to source resolution, and explicit limitations. It is
product-specific: spatial suitability does not approve every field from a
returned cell. Bounded probes establish returned-grid behavior and availability,
not forecast accuracy or long-term reliability.

## Tide and water-temperature evidence

NOAA subordinate prediction station `8652591`, Roanoke Sound Channel
(`35.7983, -75.5833`), is approximately 11.487 km from Little Bridge. Its
reference station is `8652587`; returned metadata gives `type = S`,
`timeOffsetHighTide = 97`, `timeOffsetLowTide = 77`,
`heightOffsetHighTide = 0.47`, `heightOffsetLowTide = 0.14`, and
`heightAdjustedType = R`. A bounded `predictions`, `hilo`, `MLLW`, `gmt`, and
`metric` request returned 39 ordered high/low events. The result is transferred
astronomical tide context, not a direct Little Bridge water-level observation,
actual water level, or current.

USGS water-temperature checks returned zero current instantaneous-temperature
series for both reviewed Roanoke Sound and Croatan Sound comparison sites over
the tested 14-day request. This leaves no current local water-temperature
validation; it does not invalidate the approved modeled SST relationship.

## Unresolved and rejected products

The marine probe returned non-null current fields at the reviewed Roanoke Sound
cell, but current representativeness is unresolved. Local channels, bridges,
constrictions, and shoreline geometry may materially alter speed and direction.

Modeled sea level also returned values but is not approved. NOAA tide predictions
remain the water-level timing relationship.

## Observation-source posture

The frozen source-suitability assessment classifies Little Bridge Yellow
overall and the structured Outer Banks This Week production path Red. Exact-site
fishing evidence is strategically useful, but usefulness does not establish an
automated production ingestion source. No automated exact-site Little Bridge
source is approved; that uncertainty does not block the environmental contract.

## Sources

| Evidence class | Reference | Supports |
| --- | --- | --- |
| Direct published evidence | [Town of Nags Head Little Bridge Sound Access](https://www.nagsheadnc.gov/facilities/facility/details/Little-Bridge-Sound-Access-14) | Public facility identity and access context. |
| Published location evidence | [Little Bridge Access Park](https://www.saltchef.com/catch_fish/NC/Dare/fishing_piers.html) | Little Bridge Access Park entrance coordinate `35° 53'53.07" N, 75° 36'58.86" W`; it is published location evidence, not authoritative government evidence. |
| Project inference | [Approved #186 destination record](https://github.com/epmelito/SaltBytes/issues/186#issuecomment-5287141104) | Destination-coordinate interpretation from published facility-location evidence and current map imagery. |
| Project inference | [Approved #186 orientation record](https://github.com/epmelito/SaltBytes/issues/186#issuecomment-5287124634) | Sound-side orientation interpretation and not-applicable pier seaward azimuth. |
| Empirical probe evidence | [Approved #186 consolidated evidence](https://github.com/epmelito/SaltBytes/issues/186#issuecomment-5287178302) | Candidate comparison and bounded provider, NOAA, and USGS probe results. |
| Approved project decision | [Decision 0014](../decisions/0014-little-bridge-seventh-location-contract.md) | The accepted contract; it does not replace the evidence above. |
| Frozen research | [Fishing-observation source suitability assessment](fishing-observation-source-suitability.md#little-bridge-reporting) | Yellow overall and Red structured production posture. |
