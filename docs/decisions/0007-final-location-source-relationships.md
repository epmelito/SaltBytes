# Final first-release location-to-source relationships

## Status

Accepted

## Context

SaltBytes represents each approved fishing location as a composite coastal
location. ADR 0004 requires display, request, and returned-grid coordinates to
remain distinct and associates returned coordinates with the model or product
that produced them.

Stage 4 research evaluated authoritative destination geometry and temporary
Open-Meteo requests for the five approved locations. Several destination
coordinates returned sound-side, inlet-side, estuarine, land-adjacent, or
cross-inlet model cells. One coordinate therefore cannot represent every
source relationship reliably.

Implementation needs one bounded set of configured request coordinates and
expected returned-grid relationships. Runtime geographic inference, fallback
coordinates, and generalized coordinate selection are outside the first-release
boundary.

## Decision

SaltBytes will use these first-release location-to-source relationships.

| Location | Relationship | Request or display coordinate | Expected returned coordinate | Displacement | Evidence type | Coastal regime and limitation |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Jennette's Pier | Display or destination | `35.9096355, -75.5966537` | Not applicable | Not applicable | Direct NCDCM surveyed coordinate, 2018-03-06 | Atlantic-facing pier; destination anchor is not a universal sample point |
| Jennette's Pier | `ncep_nbm_conus` weather | `35.9096355, -75.5966537` | `35.8955700, -75.5936000` | 1.588 km | Direct destination coordinate with repeated empirical result | Atlantic coastal grid; representativeness is not accuracy |
| Jennette's Pier | `meteofrance_wave` | `35.9100000, -75.5400000` | `35.8750000, -75.5416600` | 3.895 km | Project inference from authoritative Atlantic pier geometry with repeated empirical result | Atlantic-facing marine grid several kilometres east and south |
| Jennette's Pier | `meteofrance_currents` SST | `35.9100000, -75.5400000` | `35.8750000, -75.5416600` | 3.895 km | Same supported request point with a separately retained product relationship | Atlantic-facing marine grid; SST relationship remains product-specific |
| Beach Access Ramp 72, Ocracoke Island | Display or destination | `35.0868922, -75.9844152` | Not applicable | Not applicable | Derived from the authoritative NPS Ramp 72 road endpoint | Ocean-side surf only |
| Beach Access Ramp 72, Ocracoke Island | `ncep_nbm_conus` weather | `35.0868922, -75.9844152` | `35.1019550, -75.9833150` | 1.678 km | Authoritative destination geometry with repeated empirical result | Ocean-side coastal grid; representativeness is not accuracy |
| Beach Access Ramp 72, Ocracoke Island | `meteofrance_wave` | `35.0868922, -75.9844152` | `35.1250000, -75.9583300` | 4.857 km | Authoritative destination geometry with repeated empirical result | Ocean-side Atlantic grid north of the destination |
| Beach Access Ramp 72, Ocracoke Island | `meteofrance_currents` SST | `35.0868922, -75.9844152` | `35.1250000, -75.9583300` | 4.857 km | Same supported request point with a separately retained product relationship | Ocean-side Atlantic grid; SST relationship remains product-specific |
| Fort Macon State Park, ocean side | Display or destination | `34.6949437, -76.6973910` | Not applicable | Not applicable | Direct NCDCM Bathhouse Access coordinate, 2021-03-10 | Ocean-side surf; general park coordinates are closer to the inlet |
| Fort Macon State Park, ocean side | `ncep_nbm_conus` weather | `34.6933000, -76.7117000` | `34.6858600, -76.7178960` | 1.003 km | Direct NOAA Atlantic Beach coordinate with repeated empirical result | Atlantic coastal grid; avoids the display point's cross-inlet return |
| Fort Macon State Park, ocean side | `meteofrance_wave` | `34.6500000, -76.6970000` | `34.6250000, -76.7083300` | 2.967 km | Project-inferred seaward point with repeated empirical result | Atlantic-facing grid south of the destination |
| Fort Macon State Park, ocean side | `meteofrance_currents` SST | `34.6500000, -76.6970000` | `34.6250000, -76.7083300` | 2.967 km | Same supported request point with a separately retained product relationship | Atlantic-facing grid; SST relationship remains product-specific |
| Bogue Inlet Pier | Display or destination | `34.6601236, -77.0337424` | Not applicable | Not applicable | Derived from NOAA ENC pier-foot geometry | Atlantic-facing pier only |
| Bogue Inlet Pier | `ncep_nbm_conus` weather | `34.6601236, -77.0337424` | `34.6712840, -76.9964140` | 3.632 km | Authoritative pier geometry with repeated empirical result | Atlantic coastal grid; representativeness is not accuracy |
| Bogue Inlet Pier | `meteofrance_wave` | `34.6579882, -77.0331663` | `34.6250000, -77.0416600` | 3.750 km | Derived from NOAA ENC pier-head geometry with repeated empirical result | Atlantic-facing grid south of the pier |
| Bogue Inlet Pier | `meteofrance_currents` SST | `34.6579882, -77.0331663` | `34.6250000, -77.0416600` | 3.750 km | Same supported request point with a separately retained product relationship | Atlantic-facing grid; SST relationship remains product-specific |
| Fort Fisher State Recreation Area | Display or destination | `33.9534000, -77.9290000` | Not applicable | Not applicable | Direct coordinate published by North Carolina State Parks | Ocean-side surf; the park covers a long beach |
| Fort Fisher State Recreation Area | `ncep_nbm_conus` weather | `33.9534000, -77.9290000` | `33.9541440, -77.9345400` | 0.518 km | Direct destination coordinate with repeated empirical result | Atlantic coastal grid; representativeness is not accuracy |
| Fort Fisher State Recreation Area | `meteofrance_wave` | `33.9300000, -77.9000000` | `33.8750000, -77.8749900` | 6.537 km | Project-inferred Atlantic-facing point with repeated empirical result | Atlantic-facing grid near the southern park extent |
| Fort Fisher State Recreation Area | `meteofrance_currents` SST | `33.9300000, -77.9000000` | `33.9583360, -77.8749900` | 3.905 km | Same supported request point with a separately retained product relationship | Atlantic-facing grid distinct from the wave grid |

Returned weather and marine coordinates are model- or product-specific
relationships. A shared numeric value does not merge the relationships.

The configured expected latitude and longitude must equal the numeric
coordinates returned by the source after parsing. Raw JSON formatting and
decimal-string representation are not part of the comparison. No geographic
tolerance is authorized.

An unexpected returned coordinate rejects only the affected source result and
requires relationship review. SaltBytes will not select a fallback coordinate
or infer a replacement geographic relationship at runtime.

Every approved relationship must include its static coastal-regime
classification. Temporary empirical probes may remain in research evidence but
are not approved implementation relationships.

Ramp 72 remains an ocean-side surf location only. Bogue Inlet Pier remains a
pier location only. These relationships do not authorize inlet-current
requirements or scoring.

## Consequences

The first release can configure source requests without treating the display
coordinate as a universal sampling point.

Request and returned coordinates must remain separate for weather, wave, and
sea-surface-temperature products. A provider grid change becomes visible as a
rejected source result instead of silently changing the spatial meaning of
normalized data.

These relationships document representativeness, not accuracy. Accuracy and
bias validation remain separate work.

No fallback coordinate, coordinate-search algorithm, distance tolerance, or
runtime coastal-regime inference is authorized.

## Alternatives considered

Use each display coordinate for every source request. This was rejected because
empirical requests produced unsuitable cross-inlet, sound-side, estuarine, or
land-adjacent returned cells for some locations.

Use one marine request and returned relationship without retaining product
identity. This was rejected because wave and sea-surface-temperature products
can return different grid coordinates.

Select a nearby replacement dynamically when the expected grid changes. This
was rejected because no evidence supports a deterministic runtime selection
rule, and silent replacement would weaken provenance and reviewability.

## Related governance

- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Coastal location requirements](../requirements/coastal-locations.md)
- [Coastal spatial relationships](../research/coastal-spatial-relationships.md)
- [ADR 0004](0004-spatial-coordinate-and-returned-grid-policy.md)
- [ADR 0005](0005-open-meteo-model-strategy.md)
