# Supplemental GFS pressure context

## Status

Accepted.

## Decision

`ncep_nbm_conus` remains SaltBytes' primary weather source. It supplies required
weather fields and optional cloud cover, air temperature, and apparent
temperature. Optional NBM context is stored as unavailable when missing,
malformed, null, or nonfinite; it does not invalidate otherwise usable weather.

Mean sea level pressure is a separate supplemental Open Meteo request using
`ncep_gfs025` and only `pressure_msl`. Each request retains its own snapshot,
model selector, requested and returned coordinates, and source result. GFS
pressure failure is visible in source monitoring but does not fail the weather
source, pipeline run, technical eligibility, or species assessments.

The verified GFS grid relationships are configured per location. They must not
be inferred from the NBM relationship. GFS 0.25 degree pressure is coarser than
NBM. Open-Meteo describes GFS as approximately 0.25 degree (about 25 km), with
native three-hourly values after 120 forecast hours; Open-Meteo interpolates
those values to hourly. SaltBytes stores the provider's returned hourly values
and does not perform interpolation. GFS forecast hours may have a different
issuance and valid-time context from NBM, so SaltBytes preserves them as their
own supplemental context rather than treating them as NBM values. Pressure is
informational only and is not a fishing interpretation or score input.

## Consequences

The Conditions dashboard may display pressure when available and must identify
it as unavailable otherwise. No fallback, blending, coordinate substitution, or
assessment behavior is authorized.

## Related governance

- [Open Meteo model strategy](0005-open-meteo-model-strategy.md)
- [Spatial coordinate and returned grid policy](0004-spatial-coordinate-and-returned-grid-policy.md)
- [Coastal source result validity rules](0009-coastal-source-result-validity-rules.md)
