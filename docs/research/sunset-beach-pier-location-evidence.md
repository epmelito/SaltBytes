# Sunset Beach Pier location evidence

## Status

Completed bounded evidence for the approved sixth-location contract, assessed
2026-08-13. This is not implementation configuration or a substitute for the
current decision record.

## Destination and spatial relationships

NOAA publishes Sunset Beach Pier, Atlantic Ocean at `33.8650000, -78.5067000`.
The following metadata records the approved relationships in
[Decision 0013](../decisions/0013-sunset-beach-pier-sixth-location-contract.md).

| Relationship | Request and expected return | Request-to-return displacement | Source resolution | Representativeness limit | Status |
| --- | --- | ---: | --- | --- | --- |
| Weather, `ncep_nbm_conus` | destination `33.8650000, -78.5067000` to `33.875553, -78.49414` | 1.6 km | approximately 2.5 km grid | Returned atmospheric grid, not a pier observation; local coastal accuracy is untested. | Approved |
| Wave, `meteofrance_wave` | marine request `33.8389394, -78.4982931` to `33.791664, -78.45833` | 6.4 km | approximately 8 km grid | Returned Atlantic-facing marine grid, not pier or nearshore wave conditions; accuracy is untested. | Approved |
| SST, `meteofrance_currents` | marine request `33.8389394, -78.4982931` to `33.875, -78.45833` | 5.4 km | approximately 8 km grid | Product-specific returned marine grid, not a pier temperature observation; accuracy is untested. | Approved |
| Marine request geometry | `33.8389394, -78.4982931`, about 3 km seaward along shore normal 165 degrees | Not applicable | No grid; project-derived request point | Supports an Atlantic-facing request only. It does not make wave and SST returns interchangeable or establish nearshore accuracy. | Approved project inference |
| Tide, NOAA station `8659897` | direct station, Sunset Beach Pier | 0 km; no returned grid | Station prediction, not a gridded product | Astronomical prediction at the station, not an observed water level, local current, or site-specific condition. | Approved direct use |

Bounded seven-day probes on 2026-08-13 returned 168 unique hourly timestamps
and zero nulls in required weather, wave, and SST fields; each product's
returned coordinate repeated. They establish checkpoint behavior for these
relationships, not forecast accuracy, long-term reliability, or production
fitness.

The direct NOAA prediction probe for station `8659897` returned ordered high
and low predictions over the required window using `predictions`, `hilo`,
`MLLW`, `gmt`, and `metric`.

The reviewed north-up satellite image, local DCM shoreline geometry, and NOAA
pier geometry support shore normal 165 degrees and pier seaward azimuth 180
degrees at moderate confidence. The DCM `Sunset Beach Boating Access & Fishing
Pier` feature is a separate estuarine facility and was excluded.

## Observation suitability

The prior frozen assessment recorded a Yellow classification because the
Windows review could not retrieve the robots policy. Current owner-reviewed
policy retrieval blocks named bots but has no wildcard prohibition applying to
a SaltBytes-specific agent. Under the existing low-frequency,
factual-extraction, attribution, and no-circumvention posture, Sunset Beach
Pier is Green. This remains dated and conditional; it is not legal advice or
permanent authorization.

## Spanish mackerel applicability

The consolidated research rates ocean-pier applicability High. No
Sunset-specific biological exclusion was found, supporting the applicability
revision in `spanish-mackerel-v1.1.0`; it does not add local presence evidence
or change score behavior.

## Sources

| Evidence class | Reference | Supports |
| --- | --- | --- |
| Direct published evidence | [NOAA benchmark sheet for station 8659897](https://tidesandcurrents.noaa.gov/benchmarks/8659897.html) | Sunset Beach Pier identity, published coordinate, and Vesta Pier entrance-ramp extended centerline geometry used in the orientation review. |
| Direct published evidence | [Sunset Beach Pier history and scenic overlook](https://sunsetbeachpier.com/history-scenic-overlook/) | Operator description that the pier end faces south and the beach runs east–west. |
| Authoritative geometry | [NC DCM Beach and Waterfront Access GIS](https://services2.arcgis.com/kCu40SDxsCGcuUWO/arcgis/rest/services/DCM_Beach_and_Waterfront_Access/FeatureServer) | Local shoreline geometry and exclusion of the separate estuarine DCM feature. |
| Direct published evidence | [Open-Meteo NBM Conus documentation](https://open-meteo.com/en/docs/gfs-api) | Approximately 2.5 km resolution for `ncep_nbm_conus`. |
| Direct published evidence | [Open-Meteo Marine Weather API data sources](https://open-meteo.com/en/docs/marine-weather-api) | Approximately 8 km resolution for the Météo-France wave and current products. |
| Project inference | [Approved #181 orientation record](https://github.com/epmelito/SaltBytes/issues/181#issuecomment-5285674442) | Shore normal 165 degrees, pier seaward azimuth 180 degrees, and the marine request geometry derived from the published and authoritative evidence. |
| Empirical probe evidence | [Approved 2026-08-13 probe record](https://github.com/epmelito/SaltBytes/issues/181#issuecomment-5285674442) | Repeated weather, wave, and SST return behavior. |
| Approved project decision | [Decision 0013](../decisions/0013-sunset-beach-pier-sixth-location-contract.md) | Approved spatial relationships, tide use, and observation-source posture; it does not replace the underlying evidence above. |
| Direct published evidence | [Sunset Beach Pier robots policy](https://apps.sunsetbeachpier.com/robots.txt) | The dated, conditional observation-source classification. |
| Frozen historical research | [Initial fishing-observation source-suitability assessment](fishing-observation-source-suitability.md#sunset-beach-pier) | The prior Yellow classification and its Windows retrieval blocker. |
| Research synthesis | [Consolidated North Carolina shore-fishing species research](nc-shore-species-research.md) | Ocean-pier Spanish mackerel applicability. |
