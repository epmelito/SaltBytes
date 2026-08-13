# Spanish mackerel conditions score methodology

## Status

Current approved methodology version `spanish-mackerel-v1.1.0`.

`spanish-mackerel-v1.0.0` remains the complete immutable first-release
contract. Version `spanish-mackerel-v1.1.0` is an applicability-only revision:
it adds Sunset Beach Pier and retains v1.0.0 scoring behavior, confidence,
explanations, rounding, and interpretation boundaries unchanged.

This document defines the deterministic scoring contract. It does not implement,
persist, publish, or display the score.

## Purpose

The Spanish mackerel conditions score is a 0 to 100 index of how strongly the
available location, seasonal, thermal, and practical fishing conditions align
with the approved North Carolina shore-accessible Spanish mackerel research.

The score does not represent:

- catch probability
- bite probability
- expected catch
- proof that Spanish mackerel are present
- proof that fish are within casting range
- guaranteed fishing success

A score of 100 means all modeled conditions are fully aligned. It does not mean
that unobserved baitfish or Spanish mackerel are present.

## Applicable locations

Location applicability is an eligibility gate, not a source of score points.
A pier does not receive a permanent advantage over surf merely because it
extends farther into the water.

### Historical v1.0.0 applicability

Version `spanish-mackerel-v1.0.0` applies only to these persisted location and
fishing-context pairs:

| Location ID | Location | Fishing context | Eligibility |
| --- | --- | --- | --- |
| `jennettes_pier` | Jennette's Pier | pier | eligible |
| `ocracoke_ramp_72` | Beach Access Ramp 72, Ocracoke Island | surf | eligible |
| `fort_macon_ocean` | Fort Macon State Park, ocean side | surf | eligible |
| `bogue_inlet_pier` | Bogue Inlet Pier | pier | eligible |
| `fort_fisher` | Fort Fisher State Recreation Area | surf | eligible |

The approved source relationships establish stable ocean-facing source
geometry, not observed site-level abundance or validated nearshore accuracy.
Ocracoke's inlet-adjacent setting and all product-specific spatial limitations
remain part of confidence and explanation.

Any new location or changed fishing context requires methodology review before
it can produce this score.

### Current v1.1.0 applicability

Version `spanish-mackerel-v1.1.0` retains the complete v1.0.0 contract and
adds only this approved persisted location and fishing-context pair:

| Location ID | Location | Fishing context | Eligibility |
| --- | --- | --- | --- |
| `sunset_beach_pier` | Sunset Beach Pier | pier | eligible |

The v1.0.0 table remains the historical applicability contract. All v1.1.0
eligible pairs are the historical v1.0.0 pairs plus Sunset Beach Pier. This
revision does not alter the score formula, availability requirements for an
already eligible pair, numeric anchors, weights, coefficients, score bands,
confidence, explanations, rounding, or prohibited interpretations.

## Required inputs and score availability

The calculation uses values for one persisted run, location, and UTC forecast
hour. The local calendar date is derived from that forecast hour using the
persisted run-location display timezone.

| Input | Expected unit or state | Role |
| --- | --- | --- |
| local forecast date | persisted location timezone | seasonal alignment |
| approved location and fishing context | exact persisted pair | eligibility |
| `wind_speed_10m` | km/h | practical fishability |
| `wind_gusts_10m` | km/h | practical fishability |
| `wave_height` | m | practical fishability |
| `sea_surface_temperature` | degrees Celsius | thermal alignment |
| weather source status | `success` | availability |
| wave source status | `success` | availability |
| SST source status | `success` | availability |

A score is available only when:

- the location and fishing context match the approved applicability table
- the persisted run-location display timezone exists and the local calendar date
  can be derived deterministically
- weather, wave, and SST source results are successful for the selected run and
  location
- all four numeric inputs are present, finite, and valid for the forecast hour
- wind speed, wind gust, and wave height are nonnegative
- SST is between -2 and 40 degrees Celsius, inclusive

If any condition is not met, the score state is `unavailable`. The calculation
must not renormalize around missing inputs or turn missing data into a zero.
The unavailable result must identify the failed, missing, invalid, or
not-applicable requirement.

The existing general `technically_eligible` feature is not the Spanish mackerel
score-availability rule. It includes tide, precipitation windows, and other
inputs that this methodology does not require.

## Calculation conventions

All component values use the inclusive 0 to 100 range.

Piecewise linear interpolation between adjacent anchors uses:

```text
y = y0 + ((x - x0) / (x1 - x0)) * (y1 - y0)
```

Values below the first numeric anchor use the first score. Values above the last
numeric anchor use the last score.

For calendar anchors, use dates in the forecast hour's local calendar year and
the actual number of elapsed calendar days between anchors. The seasonal value
is constant across all forecast hours with the same local date. Dates before
March 1 and after November 30 score zero.

Keep full precision through intermediate calculations. Clamp the final value to
0 through 100, then round half up to the nearest integer. Do not round component
values before the final calculation.

## Methodology basis and calibration status

The approved research determines which factors may enter the score and the role
each factor may play. Version 1 numeric anchors, weights, coefficients, and bands
are conservative modeling decisions. They are not calibrated catch-rate,
fish-presence, or bite-response relationships.

The numeric design uses these rationales:

- seasonal anchors translate the supported broad North Carolina migration
  period into a smooth calendar curve without claiming exact arrival or departure
- thermal anchors translate the supported warm-water association into a bounded
  modifier without creating an optimal temperature or arrival threshold
- the -2 through 40 degrees Celsius validity range is a permissive physical-data
  guard, not a favorable-temperature band or biological threshold
- the 70 percent seasonal and 30 percent conditional thermal weighting keeps the
  stronger seasonal evidence primary and limits overlapping SST credit
- the 0.60 gust coefficient retains material gust effects without treating a
  short peak gust as equivalent to sustained wind
- wind and wave anchors are broad practical-manageability heuristics for the
  current surf and pier contexts, not safety limits or biological-response rules
- one shared version 1 wind and wave curve is used for surf and pier because the
  approved evidence does not support separate calibrated mode-specific curves
- taking the lower wind or wave value prevents one manageable condition from
  canceling a strongly limiting condition
- the 0.25 practical floor preserves separate biological context while allowing
  poor practical conditions to reduce the combined score by as much as 75
  percent
- score bands are communication categories for the index, not biological states

No version 1 numeric rule has been retrospectively calibrated against
effort-normalized shore catches or direct fish-presence observations. Material
future calibration requires a new methodology version and must not silently
change historical results.

## Methodology versioning

`spanish-mackerel-v1.0.0` is the immutable identifier for the complete
first-release methodology. `spanish-mackerel-v1.1.0` is its immutable
applicability-only revision. Every calculated result must retain the exact
methodology version used.

A new methodology version is required for any change that can alter:

- applicable locations or fishing contexts
- required inputs or score-availability rules
- seasonal or thermal anchors
- interpolation, weights, coefficients, caps, floors, or score bands
- wind or wave treatment
- rounding or numeric boundary behavior
- confidence states
- positive, limiting, or unknown-factor selection or ordering
- prohibited interpretations

A documentation correction may retain the existing version only when it cannot
change any calculated score, availability state, confidence state, explanation
selection, or interpretation boundary.

An approved location applicability addition requires a new version even when it
does not change behavior for any previously eligible pair. The new version must
state whether every scoring and interpretation rule is inherited unchanged.

Historical results must remain reproducible under their recorded methodology
version. A later implementation must not silently recalculate or relabel them
under a newer version.

## Seasonal alignment

Seasonal alignment is the primary biological context because the evidence for
broad North Carolina seasonal occurrence is stronger than the evidence for an
exact thermal response.

| Local calendar date | Seasonal alignment |
| --- | ---: |
| January 1 | 0 |
| March 1 | 0 |
| April 1 | 40 |
| May 1 | 90 |
| May 15 | 100 |
| September 30 | 100 |
| October 31 | 60 |
| November 30 | 0 |
| December 31 | 0 |

These anchors are conservative methodology choices. They do not claim an exact
arrival date, departure date, statewide migration schedule, or fish presence.
Version 1 uses one statewide seasonal curve because the approved evidence does
not support precise separate regional calendars.

## Thermal alignment

SST describes broad warm-water migration context. It is not an arrival trigger,
an optimal-temperature claim, or proof that fish are near the location.

| SST | Thermal alignment |
| --- | ---: |
| 12 degrees Celsius or colder | 0 |
| 14 degrees Celsius | 25 |
| 16 degrees Celsius | 50 |
| 18 degrees Celsius | 75 |
| 20 degrees Celsius or warmer | 100 |

The anchors are explicit conservative modeling choices. The research supports a
warm-water association and broad migration context, but it does not validate a
single shore-opportunity threshold.

## Biological alignment

Season and SST overlap as migration context. They must not receive independent
full positive credit.

```text
biological_alignment =
    0.70 * seasonal_alignment
    + 0.30 * min(seasonal_alignment, thermal_alignment)
```

This rule means:

- season provides the ceiling for biological alignment
- SST can reduce alignment when it conflicts with the seasonal context
- warm SST cannot raise alignment above the seasonal value
- warm winter water cannot manufacture an in-season result
- SST remains conditional context rather than a fish-presence signal

## Practical fishability

Wind and waves describe whether shore targeting is practically manageable.
They do not claim that Spanish mackerel activity rises or falls because of the
weather.

### Effective wind

```text
effective_wind_kmh = max(wind_speed_10m, 0.60 * wind_gusts_10m)
```

| Effective wind | Wind fishability |
| --- | ---: |
| 15 km/h or less | 100 |
| 25 km/h | 80 |
| 35 km/h | 50 |
| 45 km/h | 20 |
| 55 km/h or more | 0 |

### Wave height

| Wave height | Wave fishability |
| --- | ---: |
| 0.5 m or less | 100 |
| 1.0 m | 80 |
| 1.5 m | 50 |
| 2.0 m | 20 |
| 2.5 m or more | 0 |

### Combined practical fishability

```text
practical_fishability = min(wind_fishability, wave_fishability)
```

The weaker practical condition controls this component. Calm wind cannot cancel
extremely rough water, and small waves cannot cancel severe wind.

## Final score

Biological alignment sets the upper limit. Practical conditions can reduce the
quality of the targeting window but cannot create biological alignment.

```text
conditions_score_unrounded =
    biological_alignment
    * (0.25 + 0.75 * practical_fishability / 100)
```

The practical multiplier ranges from 0.25 through 1.00. Severe wind or waves can
therefore reduce an otherwise aligned result by at most 75 percent without
claiming that the species disappeared.

After calculation, clamp and round according to the calculation conventions.

## Score bands

| Integer score | Interpretation |
| --- | --- |
| 0 through 19 | Very limited alignment |
| 20 through 39 | Limited alignment |
| 40 through 59 | Mixed conditions |
| 60 through 79 | Favorable alignment |
| 80 through 100 | Strong alignment |

`Unavailable` is a separate result state and must never be displayed as zero.
The bands describe modeled conditions alignment, not likelihood of catching a
fish.

## Confidence

Version 1 does not publish a numeric confidence score. Numeric precision would
suggest validation and biological coverage that SaltBytes does not have.

Each available score must report the shared confidence dimensions separately:

| Confidence dimension | Version 1 state |
| --- | --- |
| `species_identity_confidence` | high |
| `location_applicability_confidence` | high, except moderate at `ocracoke_ramp_72` |
| `environmental_source_confidence` | moderate |
| `seasonal_evidence_confidence` | high |
| `habitat_data_confidence` | moderate |
| `biological_observation_confidence` | low |
| `fishability_data_confidence` | moderate |
| `overall_interpretation_confidence` | moderate |

The states mean:

- species identity is stable and unambiguous for the pilot
- approved locations are applicable, while Ocracoke retains stronger
  inlet-adjacent limitations
- weather, wave, and SST inputs are available but are not validated site-level
  observations
- broad seasonal evidence is strong, while exact annual timing remains unknown
- site type is available, but detailed shoreline exposure and habitat occupancy
  are incomplete
- local baitfish, Spanish mackerel presence, and casting-range access are not
  observed
- wind and waves support broad practical fishability, but do not represent
  beach breaker state or every access limitation
- the overall interpretation remains bounded by missing local biology and the
  lack of retrospective catch validation

For an unavailable result, the specific missing, failed, invalid, or
not-applicable requirement must be stated instead of assigning confidence to a
score that was not calculated.

No version 1 result may describe overall interpretation as high confidence.
SaltBytes cannot observe local baitfish, current fish presence, whether schools
are within casting range, or validated shore catch outcomes.

## Explanations and unknowns

Each available result must report every triggered material factor in this
stable order: season, thermal context, wind, waves, then unknown biology.

Positive factors are triggered when:

- seasonal alignment is at least 80
- seasonal alignment is greater than zero and thermal alignment is greater
  than or equal to seasonal alignment
- wind fishability is at least 80
- wave fishability is at least 80

Limiting factors are triggered when:

- seasonal alignment is below 80
- thermal alignment is below seasonal alignment
- wind fishability is below 80
- wave fishability is below 80

The explanation must distinguish biological alignment from practical
fishability. It must not relabel wind or waves as fish activity.

Every available result must report these unknowns:

- local baitfish presence
- current Spanish mackerel presence
- whether schools are within casting range
- nearshore SST accuracy and site representativeness

The methodology defines the meanings and selection rules, not final product
copy. User-facing wording must follow the
[user-facing language requirements](user-facing-language.md) and must not expose
internal field names or equations as default labels.

## Context-only and excluded factors

These retained inputs remain outside version 1 scoring:

- tide phase and time relative to tide extrema
- solar state
- cloud cover
- precipitation
- wind direction
- wave direction
- wave period

They may remain visible as context or be used in later retrospective analysis.
Their availability does not establish a favorable direction.

Version 1 excludes:

- barometric pressure and weather fronts
- moon and solunar variables
- spawning status as an opportunity bonus
- generic pier, inlet, structure, or depth bonuses
- rainfall as a salinity, clarity, prey, or fish-presence proxy
- inferred baitfish, current, water clarity, salinity, or fish presence

## Validation scenarios

The implementation must reproduce these results from the exact inputs shown.
All unspecified source statuses are successful, and all locations are approved.

| Scenario | Local date | SST | Wind | Gust | Waves | Biological | Practical | Final result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| warm winter and calm weather | January 15 | 20 | 10 | 15 | 0.5 | 0 | 100 | 0 |
| April start and warm water | April 1 | 20 | 10 | 15 | 0.5 | 40 | 100 | 40 |
| April start and cool water | April 1 | 14 | 10 | 15 | 0.5 | 35.5 | 100 | 36 |
| peak season and calm weather | July 15 | 20 | 10 | 15 | 0.5 | 100 | 100 | 100 |
| peak season and mixed fishability | July 15 | 20 | 20 | 30 | 1.2 | 100 | 68 | 76 |
| peak season and severe conditions | July 15 | 20 | 55 | 60 | 2.5 | 100 | 0 | 25 |
| late shoulder and warm water | October 31 | 20 | 10 | 15 | 0.5 | 60 | 100 | 60 |
| late shoulder and cool water | October 31 | 14 | 10 | 15 | 0.5 | 49.5 | 100 | 50 |

Units are degrees Celsius for SST, km/h for wind and gust, and metres for waves.
The late-shoulder cool-water case verifies half-up rounding from 49.5 to 50.

The following cases must return `unavailable`, not zero or a reduced score:

- an unapproved location or changed fishing context
- missing persisted run-location display timezone or an unresolvable local date
- missing or failed weather source
- missing or failed wave source
- missing or failed SST source
- any required hourly value missing, non-finite, or invalid

Repeated calculation from identical normalized inputs and methodology version
must produce the same result and explanations.

## Prohibited interpretations

The score must not be described as:

- Spanish mackerel will bite
- catch probability is high or low
- fish are present or absent
- fish are within casting range
- water above a threshold means fish arrived
- warmer water is always better
- calm or rough water changes biological activity predictably
- a missing input means poor fishing
- an unobserved baitfish state means baitfish are absent
- a score is safe-to-fish guidance

Official safety guidance, regulations, and management status remain separate
presentation layers.

## Related governance

- [Species conditions scoring requirements](species-condition-scoring.md)
- [User-facing language requirements](user-facing-language.md)
- [Fishing-condition requirements](fishing-conditions.md)
- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Decision 0010](../decisions/0010-research-backed-fishing-score-direction.md)
- [Spanish mackerel evidence profile](../research/nc-shore-species-research.md#8-spanish-mackerel-evidence-profile)
- [Shared confidence dimensions](../research/nc-shore-species-research.md#19-shared-confidence-dimensions)
- [Shared conceptual layers](../research/nc-shore-species-research.md#20-shared-conceptual-layers)
- [Final location-to-source relationships](../decisions/0007-final-location-source-relationships.md)
