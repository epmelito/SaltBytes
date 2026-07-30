# First-release Open-Meteo atmospheric and marine model strategy

## Status

Accepted

## Context

The first-release environmental baseline requires:

- wind speed
- wind direction
- wind gust
- precipitation probability
- at least one precipitation-intensity or weather-condition representation
- wave height
- wave direction
- wave period
- sea-surface temperature

SaltBytes currently uses the Open-Meteo Weather API without an accepted
first-release model strategy. Stage 4 evaluated Open-Meteo best match and
explicit atmospheric and marine model selectors.

For atmospheric data, `ncep_nbm_conus` supplied the complete accepted field set
during the evaluation. Open-Meteo documents an approximately 2.5 km grid and
an approximately 11-day forecast horizon. That horizon covers SaltBytes'
current seven-day production horizon.

For marine data, `meteofrance_wave` supplied the required wave fields and
`meteofrance_currents` supplied sea-surface temperature. Open-Meteo documents
an approximately 8 km grid scale and approximately ten-day coverage for these
products.

Open-Meteo best match supplied technically available values but did not expose
the contributing model identity or initialization time in its response.
Explicit selectors provide clearer request provenance.

The evaluation did not establish accuracy, bias, fallback behavior, or
complete upstream run lineage.

## Decision

SaltBytes will use the explicit Open-Meteo atmospheric model selector:

- `ncep_nbm_conus`

It will be the first-release Open-Meteo model responsibility for the accepted
atmospheric fields.

The reasons are:

- it supplied all accepted atmospheric fields during evaluation
- its documented 2.5 km grid is the highest-resolution complete-field option
  evaluated
- its approximately 11-day horizon supports the current seven-day production
  horizon
- its named product identity is more traceable than `models=auto`

NBM is itself a blended product. The model selector identifies the named NBM
product but does not provide complete per-value upstream model or run lineage.

SaltBytes will use these explicit Open-Meteo marine model selectors:

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

SaltBytes will not use `models=auto` as the accepted first-release
atmospheric or marine strategy.

ECMWF WAM and other evaluated marine models remain deferred alternatives. They
are not accepted sources, fallback sources, or precedence rules.

This decision selects model responsibilities for the named atmospheric, wave,
and sea-surface-temperature fields. It does not approve final request
coordinates, returned-grid relationships, accuracy, fallback behavior, tide
data, observations, retention, scheduling, or ingestion implementation.

## Consequences

Benefits:

- gives atmospheric, wave, and sea-surface-temperature requests an explicit
  model or product identity
- provides all accepted atmospheric fields within the current production
  horizon
- provides the required wave fields and sea-surface temperature within the
  current production horizon
- improves request provenance compared with best match
- permits each marine product to preserve its actual returned grid
- creates a bounded source contract for later ingestion design

Costs and limitations:

- NBM remains a blended product without complete per-value upstream lineage
- wave and sea-surface-temperature data require separate marine requests
- the two marine products may return different grid cells
- explicit selectors do not expose complete marine initialization metadata
- availability and spatial plausibility do not establish accuracy
- no source fallback or precedence behavior is defined
- model changes will require renewed source and spatial evaluation

Follow-up work:

- select and document final request coordinates through authorized work
- verify final returned-grid relationships for each model and location
- define source and model provenance fields before ingestion
- define quality behavior for missing fields, horizon changes, coordinate
  displacement, and spatial mismatch
- evaluate accuracy or bias separately
- resolve marine forecast-history reconstruction before claiming run-level
  lineage
- retain ECMWF WAM and other marine models as deferred alternatives unless
  separately authorized

## Alternatives considered

### Open-Meteo best match

Best match is operationally simple and supplied the evaluated fields, but it
does not provide enough model identity for the accepted first-release
traceability boundary.

### GFS Seamless

GFS Seamless supplied the atmospheric field set over a longer horizon, but it
combines models and has a coarser long-range component.

### HRRR

HRRR provides high spatial resolution but does not independently supply the
complete accepted field set over the current seven-day horizon.

### GFS 0.13 degree

The evaluated selector provided a long horizon but did not supply all accepted
atmospheric fields.

### ECMWF WAM

ECMWF WAM provided a longer wave horizon and useful candidate cells, but it
does not provide sea-surface temperature. It remains a deferred alternative.

### Explicit NBM and MÃ©tÃ©o-France selectors

This is the accepted choice. It provides the evaluated required fields within
the current horizon while making model and product selectors explicit.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Scope: [Scope register](../scope-register.md)
- Roadmap stage: [Stage 4](../roadmap.md#4-extend-coastal-data-source-ingestion)
- Requirement: [Fishing-condition requirements](../requirements/fishing-conditions.md)
- Existing decision: [First-release environmental requirement baseline](0003-first-release-environmental-requirement-baseline.md)
- Evidence: [Coastal source evaluation](../research/coastal-source-evaluation.md)
- Evidence: [Coastal spatial relationships](../research/coastal-spatial-relationships.md)
