# Coastal spatial relationships

## Purpose

This document records the roadmap stage 4 spatial evidence and candidate
relationships for the five accepted composite coastal locations.

It does not approve final coordinates, returned grid cells, NOAA stations,
datums, transfer rules, or ingestion relationships.

## Relationship model

ForecastOps preserves these distinct relationships:

- display or destination coordinate
- weather request coordinate
- marine request coordinate
- returned weather grid coordinate for each model or product
- returned marine grid coordinate for each model or product

Returned marine cells are model-specific or product-specific relationships.
Wave and sea-surface-temperature products may use different returned cells.

## Required relationship metadata

Each relationship will retain:

- coordinate evidence type
- evidence source and source date
- requested-to-returned displacement
- coastal-regime classification
- model or product selector
- source-resolution limitations
- spatial-representativeness limitations
- relationship status

Relationship status must distinguish candidate, accepted, rejected for the
current context, and superseded relationships.

## Evidence classifications

| Evidence type | Meaning |
| --- | --- |
| Directly published coordinate | A source publishes the coordinate for the named feature |
| Derived from authoritative geometry | The coordinate is extracted or calculated from official geometry |
| Project inference | The project derives a candidate from reviewed spatial evidence |
| Temporary empirical probe | A coordinate used only to test API grid behavior |

Temporary empirical probes may remain in research evidence. They must not
become approved implementation relationships without separate review.

## Coastal-regime classifications

Candidate and returned coordinates are classified as:

- Atlantic-facing
- sound-side
- inlet-side
- estuarine
- inland
- excessively offshore
- unresolved

The classification is a spatial interpretation. It is not an accuracy or
source-fitness result.

## Authoritative spatial sources

All sources were accessed on 2026-07-28.

| Source | URL | Publication or update date | Use and limitation |
| --- | --- | --- | --- |
| NC Division of Coastal Management Beach and Waterfront Access GIS | https://services2.arcgis.com/kCu40SDxsCGcuUWO/arcgis/rest/services/DCM_Beach_and_Waterfront_Access/FeatureServer | Service date not published; feature survey dates retained below | Destination and ocean-access points, not environmental sampling points |
| NOAA ENC Direct to GIS | https://www.fisheries.noaa.gov/inport/item/39973 | Updated 2026-03-04; maintained weekly | Chart-derived coastal geometry for research, not navigation |
| NOAA Continually Updated Shoreline Product | https://services.arcgis.com/rD2ylXRs80UroD90/ArcGIS/rest/services/NOAA_Coastal_Shoreline/FeatureServer | Not published | Mean-high-water proxy; omits many piers |
| NPS Public Roads GIS | https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer | Not published | Ramp 72 route and beach endpoint |
| NPS Ramp 72 | https://www.nps.gov/places/000/beach-access-ramp-72.htm | Updated 2021-11-07 | Confirms destination identity and southern Ocracoke beach relationship |
| FHWA/NPS Cape Hatteras route inventory | https://fhfl15gisweb.flhd.fhwa.dot.gov/Nps/Reports/Rip/Cycle6/CAHA_C6_RouteID.pdf | Cycle 6; date not published in accessible text | Identifies South Point Road as Ramp 72 and confirms that it leads to the beach |
| Jennette's Pier, NC Aquariums | https://www.ncaquariums.com/visit-jennettes-pier | Not published | Confirms a 1,000-foot pier extending over the Atlantic |
| Fort Macon State Park | https://www.ncparks.gov/state-parks/fort-macon-state-park | Not published | Park GPS and separate ocean and inlet contexts |
| Fort Macon official map | https://www.ncparks.gov/maps/fort-macon-state-park-map/open | 2024-03 | Atlantic, inlet, sound, and bathhouse orientation |
| Fort Fisher State Recreation Area | https://www.ncparks.gov/state-parks/fort-fisher-state-recreation-area | Not published | Park GPS and ocean surf context |
| Fort Fisher official map | https://www.ncparks.gov/maps/fort-fisher-state-recreation-area-map/open | 2025-03 | Atlantic and Cape Fear orientation |
| Bogue Inlet Pier | https://www.bogueinletpier.com/directions/ | Page copyright 2026 | Destination identity only |
| NOAA CO-OPS Data API | https://api.tidesandcurrents.noaa.gov/api/prod/ | Not published | Tide-prediction and datum behavior |
| NOAA CO-OPS Metadata API | https://api.tidesandcurrents.noaa.gov/mdapi/prod/ | Not published | Station coordinates and prediction relationships |

## Location evidence

| Location | Display or destination evidence | Shoreline or pier evidence | Intended context | Evidence limitation |
| --- | --- | --- | --- | --- |
| Jennette's Pier | NCDCM `35.9096355, -75.5966537`, surveyed 2018-03-06 | NOAA CO-OPS point `35.9100000, -75.5917000`; facility reports a 1,000-foot Atlantic pier | Pier, Atlantic-facing | NOAA point is not explicitly labeled as the pier head |
| Ramp 72 | NPS road endpoint `35.0868922, -75.9844152` | NPS route begins near `35.1064948, -75.9697201` and ends at the beach | Surf, ocean side only | Local shoreline direction still needs a dated shoreline intersection |
| Fort Macon, ocean side | Park GPS `34.6979000, -76.6783000`; NCDCM park point `34.6979227, -76.6781161` | NCDCM Bathhouse Access `34.6949437, -76.6973910`, surveyed 2021-03-10 | Surf, Atlantic-facing | General park GPS is closer to the inlet-side portion |
| Bogue Inlet Pier | Facility identity and NOAA ENC geometry | ENC foot `34.6601236, -77.0337424`; head `34.6579882, -77.0331663` | Pier, Atlantic-facing | ENC feature source date is 2001-07-07 and needs current confirmation |
| Fort Fisher | Park GPS `33.9534000, -77.9290000` | Official map places the accepted beach east of the anchor | Surf, Atlantic-facing | The park covers a long beach and no single fishing point is published |

## Weather-coordinate candidates

Open-Meteo weather probes used the default land-cell preference. Ranks are
research priorities, not approved coordinates.

| Location | Rank | Requested coordinate | Evidence type | Returned NBM or evaluated weather cell | Displacement | Limitation |
| --- | ---: | --- | --- | --- | ---: | --- |
| Jennette's Pier | 1 | `35.9096355, -75.5966537` | Directly published NCDCM coordinate | `35.8847100, -75.6122360` in the best-match probe | 3.11 km | Final NBM returned cell must be reconfirmed |
| Jennette's Pier | 2 | `35.9100000, -75.5917000` | Directly published NOAA coordinate | `35.8847100, -75.6122360` | 3.37 km | Pier precision did not change the evaluated cell |
| Ramp 72 | 1 | `35.0868922, -75.9844152` | Derived from NPS road geometry | `35.0978160, -75.9805900` | 1.26 km | Final NBM relationship remains unresolved |
| Ramp 72 | 2 | `35.0945080, -75.9815370` | NPS-authored image metadata along the route | `35.0978160, -75.9805900` | 0.38 km | Represents the route rather than its beach endpoint |
| Fort Macon | 1 | `34.6949437, -76.6973910` | Directly published NCDCM bathhouse point | `34.7101200, -76.6981800` | 1.69 km | Returned cell is north of the ocean beach |
| Fort Macon | 2 | `34.6979000, -76.6783000` | Directly published park GPS | `34.7040860, -76.6662700` | 1.30 km | Closer to the inlet-side portion |
| Bogue Inlet Pier | 1 | `34.6601236, -77.0337424` | Derived from NOAA ENC pier foot | `34.6649630, -77.0464900` | 1.28 km | Final NBM relationship remains unresolved |
| Bogue Inlet Pier | 2 | `34.6579882, -77.0331663` | Derived from NOAA ENC pier head | `34.6649630, -77.0464900` | 1.44 km | Same evaluated cell as the pier foot |
| Fort Fisher | 1 | `33.9534000, -77.9290000` | Directly published park GPS | `33.9460400, -77.9392500` | 1.25 km | Returned cell is west of the Atlantic shoreline |
| Fort Fisher | 2 | `33.9534000, -77.9150000` | Temporary empirical probe | `33.9460400, -77.9392500` | 2.38 km | Same land-selected cell and not an approved relationship |

The listed weather returns came from the evaluation probes. The accepted NBM
strategy must be probed and reviewed for each final request coordinate before
any relationship becomes approved.

## Marine-coordinate candidates

Open-Meteo marine probes used the default sea-cell preference. The requested
coordinates and returned cells remain candidates.

### Jennette's Pier

| Rank | Request | Product | Returned cell | Displacement | Inferred regime and limitation |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `35.9100000, -75.5400000` | `meteofrance_wave` | `35.8750000, -75.5416600` | 3.89 km | Atlantic-facing; several kilometres east and south of the pier |
| 1 | same | `meteofrance_currents` SST | `35.8750000, -75.5416600` | 3.89 km | Same candidate cell in the probe; relationship remains product-specific |
| Rejected for current context | `35.9100000, -75.5917000` | Evaluated best match | `35.8750000, -75.6249900` | 4.91 km | West of the pier and not defensibly Atlantic-facing |

### Ramp 72

| Rank | Request | Product | Returned cell | Displacement | Inferred regime and limitation |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `35.0868922, -75.9844152` | Evaluated best match | `35.1250000, -75.9583300` | 4.86 km | Plausibly Atlantic-side north of the endpoint |
| 2 | `35.0800000, -75.9700000` | Evaluated best match | `35.0416640, -75.9583300` | 4.39 km | Atlantic-facing south-point candidate with possible inlet influence |
| 3 | `35.0600000, -75.9500000` | `meteofrance_wave` and `meteofrance_currents` | `35.0416640, -75.9583300` | 2.18 km | Temporary probe; shoreline relationship remains unresolved |

The final Météo-France request and returned cells must be reviewed against the
accepted ocean-side surf context. No inlet-current requirement is introduced.

### Fort Macon, ocean side

| Rank | Request | Product | Returned cell | Displacement | Inferred regime and limitation |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `34.6500000, -76.6970000` | `meteofrance_wave` | `34.6250000, -76.7083300` | 2.97 km | Atlantic-facing south of the bathhouse |
| 1 | same | `meteofrance_currents` SST | `34.6250000, -76.7083300` | 2.97 km | Same candidate cell in the probe; relationship remains product-specific |
| Rejected for current context | `34.6949437, -76.6973910` | Evaluated best match | `34.7083360, -76.7083300` | 1.79 km | Plausibly land, sound, or inlet-side |

### Bogue Inlet Pier

| Rank | Request | Product | Returned cell | Displacement | Inferred regime and limitation |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `34.6579882, -77.0331663` | `meteofrance_wave` | `34.6250000, -77.0416600` | 3.75 km | Atlantic-facing south of the pier |
| 1 | same | `meteofrance_currents` SST | `34.6250000, -77.0416600` | 3.75 km | Same candidate cell in the probe; relationship remains product-specific |
| 2 | `34.6400000, -77.0330000` | Both accepted selectors | `34.6250000, -77.0416600` | 1.85 km | Temporary seaward probe, not an approved implementation relationship |

Bogue Inlet Pier remains a pier context only. These relationships do not
authorize inlet-current fields or inlet scoring.

### Fort Fisher

| Rank | Request | Product | Returned cell | Displacement | Inferred regime and limitation |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `33.9300000, -77.9000000` | `meteofrance_wave` | `33.8750000, -77.8749900` | 6.54 km | Atlantic-facing but near the southern park extent |
| 1 | same | `meteofrance_currents` SST | `33.9583360, -77.8749900` | 3.91 km | Atlantic-facing and distinct from the wave cell |
| Rejected for current context | `33.9534000, -77.9290000` | Evaluated best match | `33.8750000, -77.9583300` | 9.13 km | Plausibly Cape Fear or estuarine rather than Atlantic-facing |

Fort Fisher demonstrates why wave and SST relationships cannot share one
universal returned marine coordinate.

## Tide-relationship candidates

These are candidates for later station and datum review. NOAA CO-OPS tide
predictions are the accepted source family, but no mapping is accepted here.

| Location | Candidate | Distance | Product relationship | Coastal relationship | Limitation |
| --- | --- | ---: | --- | --- | --- |
| Jennette's Pier | `8652226`, Jennette's Pier | 0.45 km | Subordinate prediction referenced to `8651370` Duck | Ocean-facing pier | Final station and datum mapping remains unresolved |
| Ramp 72 | `TEC2793`, Ocracoke Inlet | 2.90 km | Subordinate prediction referenced to `8654400` Cape Hatteras Fishing Pier | Inlet and south point | Closest named prediction but not purely ocean-side surf |
| Ramp 72 | `8654769`, Ocracoke, Pamlico Sound | 4.17 km | Harmonic prediction and observed-water relationship | Sound-side | Wrong side of the island for the accepted surf context |
| Fort Macon | `8656590`, Atlantic Beach Triple S Pier | 1.32 km | Harmonic or reference prediction | Ocean-facing pier | Physical station is historical; current prediction use requires review |
| Fort Macon | `8656571`, Fort Macon | 1.48 km | Subordinate prediction referenced to `8654400` | Beaufort Inlet side | Less representative of the accepted ocean-side context |
| Bogue Inlet Pier | `TEC2837`, Bogue Inlet | 6.18 km | Subordinate prediction referenced to `8654400` | Inlet-side west of the pier | Must not introduce inlet-current scope |
| Bogue Inlet Pier | `8656613`, Swansboro | 8.39 km | Harmonic or reference prediction | Estuarine and inland | Less representative of Atlantic pier conditions |
| Fort Fisher | `8658559`, Wilmington Beach | 9.31 km | Subordinate prediction referenced to `8654400` | Ocean-facing former pier | Correct regime but materially north of the park |
| Fort Fisher | `8658715`, Federal Point | 1.37 km | Subordinate prediction referenced to `8658120` Wilmington | Cape Fear River side | Close but not Atlantic-facing |
| Fort Fisher | `8658741`, Zekes Island | 2.13 km | Harmonic or reference prediction | Estuarine and Cape Fear side | Close but wrong coastal regime |

Tide predictions, observed water levels, tidal-current predictions, and
generic modeled mean-sea-level output remain distinct products.

## Unresolved relationships

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
- [Composite geographic model and initial locations](../decisions/0002-composite-geographic-model-and-initial-locations.md)
- [Spatial coordinate and returned-grid policy](../decisions/0004-spatial-coordinate-and-returned-grid-policy.md)
- [Open-Meteo model strategy](../decisions/0005-open-meteo-model-strategy.md)
- [Authoritative tide-product responsibility](../decisions/0006-authoritative-tide-product-responsibility.md)
