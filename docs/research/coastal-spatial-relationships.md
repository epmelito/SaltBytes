# Coastal spatial relationships

## Purpose

This document records the evidence supporting the accepted first-release
coastal location-to-source relationships. It distinguishes authoritative
geometry, project inference, empirical probes, and approved relationships.

The approved relationships are future configuration and implementation inputs.
They do not constitute ingestion implementation or evidence of forecast
accuracy.

## Relationship model

SaltBytes preserves these distinct relationships:

- display or destination coordinate
- weather request coordinate
- marine request coordinate
- returned weather grid coordinate for each model or product
- returned marine grid coordinate for each model or product

Returned cells are model- or product-specific relationships. Wave and
sea-surface-temperature products retain separate relationships even when they
return the same numeric coordinate.

Each relationship retains:

- coordinate evidence type
- evidence source and source date
- requested-to-returned displacement
- coastal-regime classification
- model or product selector
- source-resolution limitations
- spatial-representativeness limitations
- relationship status

## Evidence classifications

| Evidence type | Meaning |
| --- | --- |
| Directly published coordinate | A source publishes the coordinate for the named feature |
| Derived from authoritative geometry | The coordinate is extracted or calculated from official geometry |
| Project inference | The project derives a point from reviewed spatial evidence |
| Temporary empirical probe | A coordinate used only to test API grid behavior |

Temporary empirical probes may remain in research evidence. They are not
approved implementation relationships unless separately reviewed and accepted.

## Authoritative spatial sources

Sources used for issue #26 were accessed on 2026-07-29.

| Source | URL | Publication or update date | Use and limitation |
| --- | --- | --- | --- |
| NC Division of Coastal Management Beach and Waterfront Access GIS | https://services2.arcgis.com/kCu40SDxsCGcuUWO/arcgis/rest/services/DCM_Beach_and_Waterfront_Access/FeatureServer | Service date not published; feature survey dates retained below | Destination and ocean-access coordinates, not environmental sampling points |
| NOAA ENC Direct to GIS | https://www.fisheries.noaa.gov/inport/item/39973 | Updated 2026-03-04; maintained weekly | Chart-derived pier geometry for research, not navigation |
| NOAA Continually Updated Shoreline Product | https://services.arcgis.com/rD2ylXRs80UroD90/ArcGIS/rest/services/NOAA_Coastal_Shoreline/FeatureServer | Not published | Mean-high-water proxy that omits many piers |
| NPS Public Roads GIS | https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer | Ramp 72 feature edited 2025-10-09 | Ramp 72 route and beach endpoint |
| NPS Ramp 72 | https://www.nps.gov/places/000/beach-access-ramp-72.htm | Updated 2021-11-07 | Destination identity and southern Ocracoke beach relationship |
| FHWA and NPS Cape Hatteras route inventory | https://fhfl15gisweb.flhd.fhwa.dot.gov/Nps/Reports/Rip/Cycle6/CAHA_C6_RouteID.pdf | Cycle 6; date not published in accessible text | Identifies South Point Road as Ramp 72 and confirms that it leads to the beach |
| Jennette's Pier, NC Aquariums | https://www.ncaquariums.com/visit-jennettes-pier | Not published | Confirms an Atlantic-facing pier |
| Fort Macon State Park | https://www.ncparks.gov/state-parks/fort-macon-state-park | Not published | Park identity and separate ocean and inlet contexts |
| Fort Macon official map | https://www.ncparks.gov/maps/fort-macon-state-park-map/open | 2024-03 | Atlantic, inlet, sound, and bathhouse orientation |
| Fort Fisher State Recreation Area | https://www.ncparks.gov/state-parks/fort-fisher-state-recreation-area | Not published | Published park coordinate and ocean surf context |
| Fort Fisher official map | https://www.ncparks.gov/maps/fort-fisher-state-recreation-area-map/open | 2025-03 | Atlantic and Cape Fear orientation |
| Bogue Inlet Pier | https://www.bogueinletpier.com/directions/ | Page copyright 2026 | Current destination identity only |
| NOAA CO-OPS Data API | https://api.tidesandcurrents.noaa.gov/api/prod/ | Not published | Tide-prediction and datum behavior |
| NOAA CO-OPS Metadata API | https://api.tidesandcurrents.noaa.gov/mdapi/prod/ | Not published | Station coordinates, reference relationships, offsets, and multipliers |

## Accepted location-to-source relationships

The accepted coordinate and returned-grid relationships are:

| Location | Relationship | Request or display coordinate | Expected returned coordinate | Displacement | Evidence type | Coastal regime and limitation |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Jennette's Pier | Display or destination | `35.9096355, -75.5966537` | Not applicable | Not applicable | Direct NCDCM coordinate, surveyed 2018-03-06 | Atlantic-facing pier; not a universal sampling point |
| Jennette's Pier | `ncep_nbm_conus` weather | `35.9096355, -75.5966537` | `35.8955700, -75.5936000` | 1.588 km | Direct destination coordinate and repeated empirical result | Atlantic coastal grid; accuracy untested |
| Jennette's Pier | `meteofrance_wave` | `35.9100000, -75.5400000` | `35.8750000, -75.5416600` | 3.895 km | Project inference from authoritative pier geometry and repeated empirical result | Atlantic-facing grid east and south of the pier |
| Jennette's Pier | `meteofrance_currents` SST | `35.9100000, -75.5400000` | `35.8750000, -75.5416600` | 3.895 km | Same supported request point; separate product relationship | Atlantic-facing grid; accuracy untested |
| Beach Access Ramp 72, Ocracoke Island | Display or destination | `35.0868922, -75.9844152` | Not applicable | Not applicable | Derived from authoritative NPS road endpoint | Ocean-side surf only |
| Beach Access Ramp 72, Ocracoke Island | `ncep_nbm_conus` weather | `35.0868922, -75.9844152` | `35.1019550, -75.9833150` | 1.678 km | Authoritative destination geometry and repeated empirical result | Ocean-side coastal grid; accuracy untested |
| Beach Access Ramp 72, Ocracoke Island | `meteofrance_wave` | `35.0868922, -75.9844152` | `35.1250000, -75.9583300` | 4.857 km | Authoritative destination geometry and repeated empirical result | Ocean-side Atlantic grid north of the destination |
| Beach Access Ramp 72, Ocracoke Island | `meteofrance_currents` SST | `35.0868922, -75.9844152` | `35.1250000, -75.9583300` | 4.857 km | Same supported request point; separate product relationship | Ocean-side Atlantic grid; accuracy untested |
| Fort Macon State Park, ocean side | Display or destination | `34.6949437, -76.6973910` | Not applicable | Not applicable | Direct NCDCM Bathhouse Access coordinate, surveyed 2021-03-10 | Ocean-side surf; general park coordinates are closer to the inlet |
| Fort Macon State Park, ocean side | `ncep_nbm_conus` weather | `34.6933000, -76.7117000` | `34.6858600, -76.7178960` | 1.003 km | Direct NOAA Atlantic Beach coordinate and repeated empirical result | Atlantic grid; avoids the display point's cross-inlet return |
| Fort Macon State Park, ocean side | `meteofrance_wave` | `34.6500000, -76.6970000` | `34.6250000, -76.7083300` | 2.967 km | Project-inferred seaward point and repeated empirical result | Atlantic-facing grid south of the destination |
| Fort Macon State Park, ocean side | `meteofrance_currents` SST | `34.6500000, -76.6970000` | `34.6250000, -76.7083300` | 2.967 km | Same supported request point; separate product relationship | Atlantic-facing grid; accuracy untested |
| Bogue Inlet Pier | Display or destination | `34.6601236, -77.0337424` | Not applicable | Not applicable | Derived from NOAA ENC pier-foot geometry; feature dated 2001-07-07 and facility identity confirmed in 2026 | Atlantic-facing pier only |
| Bogue Inlet Pier | `ncep_nbm_conus` weather | `34.6601236, -77.0337424` | `34.6712840, -76.9964140` | 3.632 km | Authoritative pier geometry and repeated empirical result | Atlantic coastal grid; accuracy untested |
| Bogue Inlet Pier | `meteofrance_wave` | `34.6579882, -77.0331663` | `34.6250000, -77.0416600` | 3.750 km | Derived from NOAA ENC pier-head geometry and repeated empirical result | Atlantic-facing grid south of the pier |
| Bogue Inlet Pier | `meteofrance_currents` SST | `34.6579882, -77.0331663` | `34.6250000, -77.0416600` | 3.750 km | Same supported request point; separate product relationship | Atlantic-facing grid; accuracy untested |
| Fort Fisher State Recreation Area | Display or destination | `33.9534000, -77.9290000` | Not applicable | Not applicable | Direct coordinate published by North Carolina State Parks | Ocean-side surf; the park covers a long beach |
| Fort Fisher State Recreation Area | `ncep_nbm_conus` weather | `33.9534000, -77.9290000` | `33.9541440, -77.9345400` | 0.518 km | Direct destination coordinate and repeated empirical result | Atlantic coastal grid; accuracy untested |
| Fort Fisher State Recreation Area | `meteofrance_wave` | `33.9300000, -77.9000000` | `33.8750000, -77.8749900` | 6.537 km | Project-inferred Atlantic-facing point and repeated empirical result | Atlantic-facing grid near the southern park extent |
| Fort Fisher State Recreation Area | `meteofrance_currents` SST | `33.9300000, -77.9000000` | `33.9583360, -77.8749900` | 3.905 km | Same supported request point; separate product relationship | Atlantic-facing grid distinct from the wave grid |

The Open-Meteo relationships were returned identically by two temporary
requests on 2026-07-28. Repeated technical behavior supports the configured
relationship but does not establish accuracy, long-term stability, or
production fitness.

## Relationship validation boundary

Each source request must use its configured approved request coordinate. The
numeric latitude and longitude returned by the source must equal the configured
expected returned coordinate for that model or product after parsing.

The comparison does not use raw JSON text or decimal formatting. No geographic
tolerance is authorized. A different returned coordinate rejects only the
affected source result and requires review. SaltBytes does not infer a
replacement relationship at runtime.

Each relationship must have a configured static coastal-regime classification.
Temporary empirical probes remain research evidence and are not approved
implementation relationships.

## Rejected alternatives

- A Jennette's Pier destination-coordinate marine request returned a cell west
  of the pier that was not defensibly Atlantic-facing.
- The Fort Macon display-coordinate weather request returned a cross-inlet grid
  relationship.
- The Fort Macon display-coordinate marine request returned a northern
  inlet-side, sound-side, or land-adjacent relationship.
- The Fort Fisher display-coordinate marine request returned Cape Fear or
  estuarine-side relationships.
- Less-authoritative inferred Ramp 72 and Bogue Inlet Pier alternatives were
  rejected because authoritative destination or pier geometry produced
  equivalent or better-supported relationships.

## Accepted tide relationships

| Location | NOAA prediction location | Identifier | Distance | Relationship | Limitation |
| --- | --- | --- | ---: | --- | --- |
| Jennette's Pier | Jennettes Pier, Nags Head (ocean) | `8652226` | 0.448 km | Direct use | Prediction is not an observed water level |
| Beach Access Ramp 72, Ocracoke Island | Ocracoke Inlet | `TEC2793` | 3.697 km | Explicit transfer to the southern ocean-side surf location | No inlet-current interpretation |
| Fort Macon State Park, ocean side | Atlantic Beach | `8656590` | 1.321 km | Explicit transfer to the nearby Atlantic-facing beach | Not a prediction at the park destination |
| Bogue Inlet Pier | Bogue Inlet | `TEC2837` | 6.164 km | Explicit transfer for phase at the pier | Pier context only; no inlet-current interpretation |
| Fort Fisher State Recreation Area | Wilmington Beach | `8658559` | 9.308 km | Explicit transfer from the nearest reviewed ocean-facing relationship | Material distance north of the destination |

All five relationships use NOAA CO-OPS product `predictions`, interval `hilo`,
datum `MLLW`, time zone `gmt`, and units `metric`. The direct-use and transfer
relationships do not authorize project interpolation, correction factors,
fallback stations, observed-water-level ingestion, or tidal-current products.

## Relationships still unresolved or deferred

The approved relationships do not resolve:

- observation-station relationships
- accuracy or bias validation
- source fallback and precedence rules
- alternative marine-model adoption
- marine run-history reconstruction beyond metadata exposed by the selected
  products
- warning, forecast, and safety-zone relationships

These topics require separately authorized work. They do not block documenting
the approved first-release request and expected returned-grid relationships.

## Related governance

- [Project charter](../project-charter.md)
- [Scope register](../scope-register.md)
- [Roadmap stage 4](../roadmap.md#4-extend-coastal-data-source-ingestion)
- [Coastal location requirements](../requirements/coastal-locations.md)
- [Fishing-condition requirements](../requirements/fishing-conditions.md)
- [ADR 0004](../decisions/0004-spatial-coordinate-and-returned-grid-policy.md)
- [ADR 0005](../decisions/0005-open-meteo-model-strategy.md)
- [ADR 0006](../decisions/0006-authoritative-tide-product-responsibility.md)
- [ADR 0007](../decisions/0007-final-location-source-relationships.md)
- [ADR 0008](../decisions/0008-noaa-tide-relationships-and-phase.md)
- [ADR 0009](../decisions/0009-coastal-source-result-validity-rules.md)
