# Fishing Factor Registry

## 1. Purpose
This document is a research backed decision reference for future SaltBytes data additions. It compares potential fishing value, evidence quality, species dependence, public data feasibility, implementation effort, and suitability for later deterministic analysis.

This document is not:

- a scoring model
- a set of weights or favorable thresholds
- a catch prediction system
- a commitment to implement every factor
- a substitute for target species research

The first SaltBytes model remains species agnostic. Factors whose direction depends materially on species, life stage, migration, feeding strategy, or habitat preference are retained for future target species work rather than generalized.

The registry describes data value. It does not interpret personal safety. Official warnings may be displayed by a future product, but safety only feeds are outside the fishing factor roadmap and do not increase a factor's value or implementation priority.

## 2. Interpretation boundaries
Each factor is classified for the narrowest outcome that the evidence can defend.

### Biological relevance
A factor changes habitat, physiology, distribution, feeding conditions, or environmental exposure. Biological relevance does not prove improved angler catch probability.

### Catch opportunity
A factor has evidence connecting it to fish availability, catchability, or catch per unit effort. Species specific, gear specific, offshore, estuarine, and freshwater evidence is not treated as direct North Carolina shore fishing evidence.

### Practical fishability
A factor changes the physical conditions under which a person can cast, manage line, reach water, detect bites, or access a site. Practical fishability is not a biological claim.

### Data confidence
A factor describes whether source data are fresh, complete, spatially representative, and applicable to the configured location. Confidence controls interpretation. It does not create positive fishing points.

### Safety boundary
SaltBytes does not determine whether conditions are safe. Lightning alerts, rip current warnings, high surf warnings, coastal flood warnings, tropical alerts, and public health advisories remain the responsibility of official agencies and personal judgment. These products are excluded from the main factor registry unless their underlying physical measurement also has a separate fishing data use.

### Evidence and project judgment
Evidence strength describes support for the stated outcome. Expected value, implementation effort, scoring suitability, and decision are SaltBytes project judgments informed by that evidence.

An A rating does not imply one universal favorable direction.

## 3. Decision criteria

### Expected fishing value

| Rating | Definition |
|---|---|
| High | The factor can materially improve biological, catch opportunity, practical fishability, or data confidence interpretation and is not adequately represented by existing attributes. |
| Medium | The factor is useful only for particular sites, seasons, interactions, or operational contexts. |
| Low | The factor has weak incremental value, substantial redundancy, inconsistent direction, or little relevance at usable shore fishing resolution. |

### Evidence strength

| Rating | Definition |
|---|---|
| A | Strong direct evidence, multiple credible studies, or authoritative operational science supports the exact outcome claimed. |
| B | Credible evidence exists, but geographic, observational, contextual, or transferability limitations remain. |
| C | The mechanism is plausible, but evidence is mixed, species specific, gear specific, offshore, freshwater, or poorly transferable. |
| D | Support is mainly expert opinion, anecdote, folklore, or weak research. |
| X | No defensible support exists for general use, or the construct combines unsupported assumptions. |

### Species dependence

| Rating | Definition |
|---|---|
| Low | The relevant effect is broadly physical, operational, or physiologically consistent across species. |
| Medium | The factor is broadly relevant, but magnitude, preferred range, or response timing differs among species or life stages. |
| High | Direction or usefulness changes materially by species, life stage, feeding strategy, stock, migration, or habitat. |

### Public data availability

| Rating | Definition |
|---|---|
| High | Free public access, useful coverage, machine readable delivery, suitable resolution, history, and credible continuity. |
| Medium | Public data exist, but coverage, automation, representativeness, history, or continuity has material limits. |
| Low | No dependable public source exists at useful site and time resolution. |

Availability evaluates the complete practical data supply, not whether a value can be found somewhere online.

### Source stability

| Rating | Definition |
|---|---|
| High | A durable public institution operates a documented interface or established downloadable product. |
| Medium | The operator is credible, but station operation, individual datasets, update schedules, schemas, or machine readable access may change. |
| Low | The source depends on local operators, manual pages, voluntary reports, unstable scraping, or short lived projects. |

### Implementation effort

| Rating | Definition |
|---|---|
| Low | Deterministic derivation from current fields or a small addition from an existing source. |
| Medium | Requires reviewed static metadata, a new source, source to location mapping, historical processing, or additional provenance rules. |
| High | Requires site specific validation, inconsistent sources, depth aware mapping, manual curation, frequently changing geometry, or extensive missing data handling. |

### Scoring suitability

| Rating | Definition |
|---|---|
| Strong | Can support a clear species agnostic rule, interaction, confidence control, or availability state without inventing a universal bite response. |
| Conditional | Requires companion inputs, site applicability, nonlinear interpretation, seasonal context, or local validation. |
| Weak | May support research or explanation, but not reliable deterministic scoring. |
| Unsuitable | Should not enter a species agnostic deterministic score because it is unsupported, redundant, misleading, or fundamentally species specific. |

### Decision

| Decision | Definition |
|---|---|
| Add first | Highest value and feasible implementation or semantic completion priority. |
| Maintain | Already implemented with no dedicated near term expansion required. Preserve the field, provenance, and limitations. |
| Investigate | Potentially valuable, but coverage, mapping, semantics, or incremental value must be verified first. |
| Opportunistic | Useful and inexpensive during related work, but not worth a dedicated expansion. |
| Defer | Potential value exists, but present data, transferability, resolution, or implementation cost is inadequate. |
| Species specific | Preserve for future target species work. Do not generalize into the first model. |
| Exclude | Do not implement for deterministic analysis unless materially stronger evidence changes the decision. |

## 4. Consolidated factor registry
Abbreviations used in the tables:

- `V`: expected fishing value
- `E`: evidence strength
- `S`: species dependence
- `A`: public data availability
- `St`: source stability
- `Ef`: implementation effort
- `Suit`: scoring suitability
- `Refs`: evidence, project inference, or repository reference IDs from section 8

### 4.1 Atmospheric and wave factors

#### Research classification

| Factor | Defensible outcome | V | E | S | Refs |
|---|---|---:|---:|---:|---|
| Wind speed | Practical casting, line control, and exposure context | High | B | Low | P03, R01 |
| Wind gusts | Short duration instability affecting practical fishability | Medium | B | Low | P03, R01 |
| Wind direction relative to site | Local onshore, offshore, and alongshore forcing | High | B | Low | P01, R01, R03 |
| Significant wave height | Physical sea state and nearshore energy context | High | B | Medium | F01, F11, R01 |
| Wave period | Distinguishes different wave energy patterns when combined with height | High | B | Medium | F11, R01 |
| Wave direction relative to site | Shore normal and alongshore wave forcing | High | B | Medium | P01, F11, R01, R03 |
| Nearshore breaker or surf height | Beach scale breaking conditions and practical fishability | High | B | Low | F11, P03 |
| Current precipitation | Immediate practical fishing conditions | Medium | C | Low | P03, R01 |
| Recent rainfall accumulation | Runoff context when paired with a defensible watershed pathway | Medium | C | Medium | F13, P03, R01 |
| Front passage | Descriptive weather context only | Low | C | Medium | F07 |
| Recent storm impacts | Local wind, wave, water level, and runoff context | Medium | C | Medium | P03 |
| Air and apparent temperature | Human exposure and comfort, not fish behavior | Low | B | Low | P03 |
| Cloud cover and ambient light | Light environment that may interact with species and turbidity | Medium | C | High | F02, F08 |
| Barometric pressure and pressure trend | Proposed direct catch effect | Low | C | High | F07 |

#### Implementation classification

| Factor | A | St | Current SaltBytes coverage | Ef | Suit | Decision |
|---|---:|---:|---|---:|---|---|
| Wind speed | High | High | Implemented hourly | Low | Conditional | Maintain |
| Wind gusts | High | High | Implemented hourly | Low | Conditional | Maintain |
| Wind direction relative to site | High | High | Raw direction only; no reviewed orientation | Medium | Strong | Add first |
| Significant wave height | High | High | Implemented hourly | Low | Conditional | Maintain |
| Wave period | High | High | Implemented hourly | Low | Conditional | Maintain |
| Wave direction relative to site | High | High | Raw direction only; no reviewed orientation | Medium | Strong | Add first |
| Nearshore breaker or surf height | Medium | High | Not implemented | High | Strong | Investigate |
| Current precipitation | High | High | Implemented hourly | Low | Weak | Maintain |
| Recent rainfall accumulation | High | High | Individual hourly amounts exist; no rolling feature | Low | Conditional | Opportunistic |
| Front passage | Medium | High | Not implemented | Medium | Weak | Defer |
| Recent storm impacts | High | High | Components partly represented; no event construct | Medium | Weak | Defer |
| Air and apparent temperature | High | High | Not implemented | Low | Weak | Opportunistic |
| Cloud cover and ambient light | High | High | Not implemented | Low | Conditional | Opportunistic |
| Barometric pressure and pressure trend | High | High | Not implemented | Low | Weak | Exclude |

Key limitations:

- Raw compass direction has no stable local meaning until shoreline or pier orientation is reviewed.
- Offshore or model grid wave height is not beach breaker height.
- A weather front or named storm should not receive independent credit when its local wind, waves, rainfall, and water level are already represented.
- The squid study behind pressure and weather associations concerns one species, one fishing method, and one Mediterranean boat fishery. It does not support a general shore fishing pressure rule.

### 4.2 Tide and current factors

#### Research classification

| Factor | Defensible outcome | V | E | S | Refs |
|---|---|---:|---:|---:|---|
| Tide phase | Position between adjacent high and low extrema | Medium | B | Medium | F02, F03, F12 |
| Tide extrema timing and predicted range | Local tidal cycle magnitude and time relative to adjacent extrema | High | B | Medium | F12, P02, R02, R03 |
| Hourly predicted water level | Tide adjusted depth and inundation context | High | B | Medium | F12 |
| Tidal current | Current speed and direction where a defensible current source exists | High | B | Medium | F12 |
| Longshore current | Alongshore transport and practical fishing conditions | High | B | Low | P03 |
| Anomalous water level | Departure from astronomical tide affecting depth and access | Medium | B | Low | F12 |

#### Implementation classification

| Factor | A | St | Current SaltBytes coverage | Ef | Suit | Decision |
|---|---:|---:|---|---:|---|---|
| Tide phase | High | High | Implemented hourly from high and low events | Low | Conditional | Maintain |
| Tide extrema timing and predicted range | High | High | Event times and levels are stored; timing and range are not exposed | Low | Strong | Add first |
| Hourly predicted water level | Medium | High | No uniform hourly series; current source requests high and low events | Medium | Strong | Investigate |
| Tidal current | Medium | High | Not implemented | High | Conditional | Investigate |
| Longshore current | Medium | High | Not implemented | High | Conditional | Investigate |
| Anomalous water level | High | High | Astronomical predictions only; no anomaly measure | Medium | Conditional | Defer |

Key limitations:

- Water level is not current speed.
- Tide phase cannot be used to fabricate current.
- Time to extrema and adjacent predicted range can be derived from existing stored events.
- A continuous hourly water level series is a separate source contract problem. CO-OPS harmonic stations can provide interval predictions, while subordinate stations may be limited to high and low predictions. SaltBytes does not currently have one uniform hourly water level method across all five sites.
- Every derived tide field must preserve station, datum, direct or transfer relationship, and known limitation metadata.

### 4.3 Water property and water quality factors

#### Research classification

| Factor | Defensible outcome | V | E | S | Refs |
|---|---|---:|---:|---:|---|
| Sea surface temperature | Broad habitat and seasonal availability context | High | A | High | F01, R01 |
| SST trend and seasonal anomaly | Early or late seasonal thermal context | High | B | High | F01, F16 |
| Salinity and salinity trend | Habitat suitability near estuarine or freshwater influence | Medium | B | High | F14, F15 |
| Turbidity | Visual feeding and prey refuge conditions | Medium | B | High | F08, F14, F15 |
| Water clarity | Optical environment distinct from suspended sediment alone | Medium | C | High | F08, F16 |
| Dissolved oxygen and oxygen saturation | Severe hypoxia as habitat stress and displacement | High | A | Medium | F04, F14, F15 |
| Freshwater discharge | Hydrologic forcing where a reviewed watershed relationship exists | Medium | B | Medium | F13 |
| Chlorophyll a | Surface productivity context | Low | B | High | F16 |

#### Implementation classification

| Factor | A | St | Current SaltBytes coverage | Ef | Suit | Decision |
|---|---:|---:|---|---:|---|---|
| Sea surface temperature | High | High | Implemented hourly | Low | Conditional | Maintain |
| SST trend and seasonal anomaly | High | High | Current SST exists; no climatology or anomaly | Medium | Conditional | Investigate |
| Salinity and salinity trend | Medium | Medium | Not implemented | High | Conditional | Investigate |
| Turbidity | Medium | Medium | Not implemented | High | Weak | Defer |
| Water clarity | Low | Medium | Not implemented | High | Weak | Defer |
| Dissolved oxygen and oxygen saturation | Low | Medium | Not implemented | High | Conditional | Investigate |
| Freshwater discharge | High | High | Not implemented | Medium | Conditional | Investigate |
| Chlorophyll a | Medium | High | Not implemented | Medium | Weak | Defer |

Key limitations:

- No universal warm water, salinity, turbidity, clarity, or chlorophyll direction exists.
- Estuarine station data do not automatically represent an open beach or pier.
- Severe oxygen deficiency is harmful habitat compression. It can also concentrate fish in remaining oxygenated water, so local encounters and biological condition may move in opposite directions.
- A nearby stream gage is not sufficient. The site requires a defensible watershed connection and event lag.
- Satellite chlorophyll is an optical surface productivity signal, not baitfish presence.

### 4.4 Solar, seasonal, and lunar factors

#### Research classification

| Factor | Defensible outcome | V | E | S | Refs |
|---|---|---:|---:|---:|---|
| Solar timing and solar state | Dawn, day, dusk, and night context | Medium | B | Medium | F02, F18 |
| Day of year and seasonality | Broad annual availability context | High | A | High | F01, F02 |
| Artificial light at night | Local fish distribution and foraging changes near illuminated structure | Medium | B | High | F09, F10 |
| Moon phase | Proposed catch effect | Low | C | High | F05 |
| Lunar illumination and local timing | Nighttime light context | Low | C | High | F05, F18 |
| Spring and neap cycle | Broad tidal range context | Medium | B | Medium | F12 |
| Solunar index | Composite proposed catch predictor | Low | X | High | F05 |

#### Implementation classification

| Factor | A | St | Current SaltBytes coverage | Ef | Suit | Decision |
|---|---:|---:|---|---:|---|---|
| Solar timing and solar state | High | High | Not implemented | Low | Conditional | Opportunistic |
| Day of year and seasonality | High | High | Timestamp exists; no explicit seasonal feature | Low | Conditional | Investigate |
| Artificial light at night | Low | Low | Not implemented | Medium | Conditional | Opportunistic |
| Moon phase | High | High | Not implemented | Low | Unsuitable | Exclude |
| Lunar illumination and local timing | High | High | Not implemented | Low | Weak | Defer |
| Spring and neap cycle | High | High | Partly represented by adjacent tide levels | Low | Unsuitable | Exclude |
| Solunar index | Low | Low | Not implemented | Low | Unsuitable | Exclude |

Key limitations:

- Diel effects vary by species, habitat, season, and sampling method.
- Day of year, SST, photoperiod, migration, and spawning overlap. Treating each as an independent positive factor would double count the same seasonal transition.
- Lunar catch effects differ by species and gear, and several studied species showed no effect.
- Actual predicted tidal range is more direct than a separate spring or neap label.
- Commercial solunar indexes generally hide their assumptions and combine unsupported universal lunar and timing claims.

### 4.5 Site geometry, morphology, and habitat factors

#### Research classification

| Factor | Defensible outcome | V | E | S | Refs |
|---|---|---:|---:|---:|---|
| Reviewed shoreline or pier orientation and exposure | Shared local frame for interpreting wind and wave direction | High | B | Low | P01, F17, R03 |
| Beach slope and morphodynamic class | Baseline breaking, depth, and habitat context | Medium | B | High | F17 |
| Current bars, troughs, cuts, and runnels | Local casting range structure and depth variation | High | B | High | F17 |
| Water depth and casting range depth | Tide adjusted reachable habitat context | High | B | High | F17 |
| Bottom substrate | Habitat context for prey and target species | Medium | B | High | F17 |
| Inlet and estuary connectivity | Connection to channels, sounds, discharge, and tidal exchange | High | B | Medium | P03, R03 |
| Artificial structure | Habitat aggregation and practical fishing context | Medium | B | High | F06 |
| Pier geometry and accessible depth | Distinct fishing reach and habitat access at pier sites | Medium | C | Medium | P03 |
| Nourishment and recent morphology disturbance | Confidence and change context after major disturbance | Medium | C | Medium | F17 |

#### Implementation classification

| Factor | A | St | Current SaltBytes coverage | Ef | Suit | Decision |
|---|---:|---:|---|---:|---|---|
| Reviewed shoreline or pier orientation and exposure | High | High | Fishing context exists; orientation does not | Medium | Strong | Add first |
| Beach slope and morphodynamic class | Medium | Medium | Not implemented | High | Conditional | Investigate |
| Current bars, troughs, cuts, and runnels | Low | Medium | Not implemented | High | Conditional | Defer |
| Water depth and casting range depth | Medium | High | Not implemented | High | Conditional | Investigate |
| Bottom substrate | Medium | High | Not implemented | Medium | Conditional | Species specific |
| Inlet and estuary connectivity | High | High | Tide relationship notes exist; no general connectivity field | Medium | Conditional | Investigate |
| Artificial structure | High | High | Not implemented | Medium | Conditional | Opportunistic |
| Pier geometry and accessible depth | Low | Medium | Fishing context only | Medium | Conditional | Investigate |
| Nourishment and recent morphology disturbance | Medium | Medium | Not implemented | High | Weak | Defer |

Key limitations:

- Orientation must be reviewed static metadata. Automatically accepting one GIS segment for a curved beach, inlet edge, or pier is not defensible.
- Orientation and broad exposure are one metadata package, not two independent scoring factors.
- High resolution bathymetry may still be stale after storms, nourishment, or seasonal movement.
- A precise value derived from stale morphology is worse than an explicit unknown.
- Structure can aggregate fish without improving angler catch. The North Carolina pier experiment recovered in this review found that fish aggregating devices attracted baitfish but did not improve pier fishing success.
- Bottom substrate and detailed habitat preferences belong mainly in future target species work.

### 4.6 Biological observation and life history factors

#### Research classification

| Factor | Defensible outcome | V | E | S | Refs |
|---|---|---:|---:|---:|---|
| Coastal migration timing | Species and stock availability along the coast | High | A | High | F01 |
| Spawning cycles | Species specific movement, aggregation, or reduced feeding | High | A | High | F01 |
| Direct baitfish presence | Immediate local forage observation | High | C | High | P03 |
| Seasonal baitfish calendar | Expected regional forage timing | Medium | C | High | P03 |

#### Implementation classification

| Factor | A | St | Current SaltBytes coverage | Ef | Suit | Decision |
|---|---:|---:|---|---:|---|---|
| Coastal migration timing | Low | High | Not implemented | High | Unsuitable | Species specific |
| Spawning cycles | Medium | High | Not implemented | High | Unsuitable | Species specific |
| Direct baitfish presence | Low | Low | Not implemented | High | Conditional | Defer |
| Seasonal baitfish calendar | Low | Medium | Not implemented | High | Unsuitable | Species specific |

Key limitations:

- Migration, spawning, and forage timing differ sharply by species, stock, life stage, and habitat.
- No stable authoritative source currently provides hourly baitfish presence at casting range across all five SaltBytes locations.
- Chlorophyll, social reports, and seasonal calendars are not valid substitutes for direct baitfish observation.

### 4.7 Operational factors

#### Research classification

| Factor | Defensible outcome | V | E | S | Refs |
|---|---|---:|---:|---:|---|
| Access and closure status | Whether the configured fishing location is usable | High | A | Low | P04 |
| Debris and floating vegetation | Practical interference with casting and line retrieval | Medium | D | Low | P03 |
| Angler crowding | Interference among anglers | Low | D | Low | P03 |

#### Implementation classification

| Factor | A | St | Current SaltBytes coverage | Ef | Suit | Decision |
|---|---:|---:|---|---:|---|---|
| Access and closure status | Low | Low | Not implemented | High | Strong | Investigate |
| Debris and floating vegetation | Low | Low | Not implemented | High | Weak | Defer |
| Angler crowding | Low | Low | Not implemented | High | Weak | Exclude |

Key limitations:

- Access status is factual operational data, not a fishing score.
- Operator pages and municipal notices may be manual, inconsistent, or stale.
- Debris and crowding lack dependable public data at the required site and time resolution.

### 4.8 Data confidence controls
Data confidence is not an environmental factor and is therefore not ranked in the main table.

SaltBytes should preserve and expose:

- source identity
- request and returned coordinates
- station and datum relationships
- capture time and valid time
- source result status
- missingness
- source age
- static metadata source and review date
- known applicability limitations

Confidence controls should determine whether a factor is interpretable. They should not add or subtract fishing points.

### 4.9 Safety only products outside scope
The following products are excluded from the main registry because their primary use is personal safety or public health:

- lightning and thunderstorm alerts
- official rip current risk
- high surf and shorebreak warnings
- coastal flood and tropical hazard warnings
- public health water quality advisories
- closure reasons that contain only safety guidance

A future SaltBytes interface may link or display authoritative warnings without interpreting them. That work is not a prerequisite for fishing factor expansion.

## 5. Near term additions
The registry identifies three coordinated additions. The roadmap controls implementation order. This document does not assign weights or authorize implementation.

### 5.1 Tide extrema context
Proposed fields:

```text
previous_tide_extremum_time
previous_tide_extremum_type
previous_tide_extremum_level
next_tide_extremum_time
next_tide_extremum_type
next_tide_extremum_level
minutes_since_previous_tide_extremum
minutes_until_next_tide_extremum
predicted_tidal_range
```

Why it ranks highly:

- SaltBytes already stores high and low event times and predicted levels.
- The fields can add local cycle timing and magnitude without pretending tide phase measures current.
- The station, datum, transfer relationship, and known limitation already exist in configuration and persistence.

Boundary:

- Do not create an hourly predicted water level by undocumented interpolation.
- A uniform hourly level series requires a separate source contract review because direct and subordinate CO-OPS stations do not provide identical interval options.

### 5.2 Reviewed orientation and exposure metadata
Proposed metadata should describe the reviewed local frame needed to interpret raw directions, including:

```text
shore_normal_azimuth_degrees
orientation_method
orientation_source
orientation_reviewed_at
orientation_limitation
```

Pier locations may require both shoreline orientation and pier alignment.

Why it ranks highly:

- Raw wind and wave direction already exist.
- One reviewed metadata package supports both directional derivations.
- It adds local physical context without another hourly provider.

Boundary:

- Do not guess orientation from a point alone.
- Do not turn a broad exposure class into an unsupported numeric score.
- Curved beaches, inlet edges, sheltering, and pier geometry require explicit review notes.

### 5.3 Wind and wave direction relative to site
Proposed derived fields may include:

```text
wind_to_shore_angle_degrees
wind_shore_normal_component
wind_alongshore_component
wave_to_shore_angle_degrees
wave_shore_normal_component
wave_alongshore_component
```

Why it ranks highly:

- The transformation is deterministic once reviewed orientation metadata exists.
- It converts regional compass directions into site relative data.
- The same dependency supports both wind and wave interpretation.

Boundary:

- Store numeric relationships before creating plain language classes.
- Offshore wave direction remains a model grid condition, not a validated final breaker direction at the beach.

## 6. Contradictory findings and uncertainty

### Tide and diel timing
Surf zone studies show that tide and time of day can affect measured fish assemblages, but responses differ among species, beaches, seasons, and sampling methods. Catch differences can also reflect gear avoidance. Tide and solar state are context, not universal bonuses.

### Dissolved oxygen
Severe hypoxia reduces usable habitat and can displace fish. Habitat compression can also raise local density in remaining oxygenated water. Biological condition and local encounter probability can therefore move in opposite directions.

### Lunar effects
The recovered Gulf reef fish study found different lunar patterns by species and gear and no detected effect for several species. It is direct evidence against a universal moon phase rule.

### Structure and aggregation
Artificial structure can aggregate fish or prey without increasing angler catch. Aggregation is not equivalent to improved catch probability.

### Pressure, fronts, and storms
Pressure, fronts, and storms change wind, waves, clouds, precipitation, temperature, and water level together. Treating the label as an independent factor risks duplicate credit and false causation.

### Turbidity and clarity
Turbidity may reduce visual predator efficiency, increase prey contrast under some optical conditions, provide refuge, favor nonvisual feeders, or reflect normal surf sediment suspension. The ecological effect is real but not directionally generalizable.

### Season, SST, migration, and spawning
These factors overlap within the annual biological cycle. Scoring them independently could reward the same seasonal transition several times. Migration and spawning remain target species factors.

### Dynamic morphology
Bars, troughs, cuts, and reachable depth can matter at one beach, but they change after storms, nourishment, and seasonal sediment movement. Survey resolution does not guarantee current applicability.

### Baitfish presence
Direct baitfish observation could have high local value. The blocker is a stable, authoritative, real time data supply across the five locations. Proxy variables should not be relabeled as baitfish presence.

## 7. Deferred, species specific, and excluded factors

### Maintain
Existing core fields should be preserved with provenance and limitations:

- wind speed
- wind gusts
- significant wave height
- wave period
- current precipitation
- sea surface temperature
- tide phase

### Investigate
Potentially valuable factors that need source, mapping, or semantic work:

- hourly predicted water level
- tidal current
- longshore current
- nearshore breaker height
- SST anomaly
- salinity
- dissolved oxygen
- freshwater discharge
- beach slope
- depth
- inlet and estuary connectivity
- pier geometry
- access and closure status

### Opportunistic
Low effort context that may be added during related work:

- recent rainfall windows
- air temperature
- cloud cover
- solar state
- artificial light metadata
- artificial structure

### Defer
Factors with weak present coverage or poor transferability:

- front passage
- named storm age
- anomalous water level
- turbidity
- water clarity
- chlorophyll a
- lunar illumination
- dynamic bars and troughs
- nourishment disturbance
- direct baitfish presence
- debris and floating vegetation

### Species specific
Preserve for later target species work:

- coastal migration timing
- spawning cycles
- seasonal baitfish calendars
- bottom substrate preferences
- species temperature preferences
- species salinity preferences
- species habitat preferences
- bait preferences and presentation

### Exclude
Do not use in species agnostic deterministic scoring:

- barometric pressure as a direct bite modifier
- moon phase as a universal predictor
- spring or neap label as a separate score
- commercial solunar indexes
- angler crowding
- safety only warning feeds

## 8. Evidence register
All external sources were accessed on 2026-07-31.

### F01
**Source:** Andrew D. Olds, Elena Vargas-Fonseca, Rod M. Connolly, et al. [The ecology of fish in the surf zones of ocean beaches: A global review](https://doi.org/10.1111/faf.12237). *Fish and Fisheries*, 2018, 19, 78 to 89.

**Claim supported:** Surf zone fish assemblages vary with water temperature, wave climate, habitat, and drifting vegetation. Surf zones are important fishing and ecological environments.

**Evidence type and applicability:** Peer reviewed global review of 152 studies. Direct surf zone ecology evidence, but not direct North Carolina recreational catch evidence.

**Limitations:** The review emphasizes variability and research gaps. It does not establish universal favorable conditions or catch thresholds.

### F02
**Source:** Fabiana C. Félix-Hackradt, Henry L. Spach, Pietro S. Moro, et al. [Diel and tidal variation in surf zone fish assemblages of a sheltered beach in southern Brazil](https://doi.org/10.3856/vol38-issue3-fulltext-9). *Latin American Journal of Aquatic Research*, 2010, 38(3), 447 to 460.

**Claim supported:** Tide and diel timing can affect measured surf fish assemblages.

**Evidence type and applicability:** Peer reviewed surf zone field study.

**Limitations:** Southern Brazil, one sheltered beach, beach seine sampling, species specific responses, and evidence that gear avoidance affected catches.

### F03
**Source:** Luiz Ricardo Gaelzer and Ilana R. Zalmon. [Tidal influence on surf zone ichthyofauna structure at three sandy beaches, southeastern Brazil](https://doi.org/10.1590/S1679-87592008000300002). *Brazilian Journal of Oceanography*, 2008, 56(3), 165 to 177.

**Claim supported:** Tidal effects differed by beach and by community measure, including abundance, richness, diversity, biomass, and catch per unit effort.

**Evidence type and applicability:** Peer reviewed multi beach surf zone field study.

**Limitations:** Southeastern Brazil and scientific seine sampling. It does not establish a universal angling response.

### F04
**Source:** Lisa A. Eby and Larry B. Crowder. [Hypoxia based habitat compression in the Neuse River Estuary: Context dependent shifts in behavioral avoidance thresholds](https://doi.org/10.1139/f02-067). *Canadian Journal of Fisheries and Aquatic Sciences*, 2002, 59(6), 952 to 965.

**Claim supported:** Ten studied fish species avoided dissolved oxygen below 2 mg/L, while expanding hypoxia compressed fish into reduced oxygenated habitat.

**Evidence type and applicability:** Peer reviewed North Carolina estuarine study.

**Limitations:** Estuarine habitat and severe hypoxia. Habitat compression may increase local density while reducing habitat quality, so it does not provide a simple catch direction for open coast fishing.

### F05
**Source:** J. R. Pulver. [Does the Lunar Cycle Affect Reef Fish Catch Rates?](https://doi.org/10.1080/02755947.2017.1293574). *North American Journal of Fisheries Management*, 2017, 37(3), 536 to 549.

**Claim supported:** Lunar catch patterns were detected for some Gulf reef species, differed by species and gear, and were absent for several other species.

**Evidence type and applicability:** Peer reviewed fishery observer CPUE analysis.

**Limitations:** Gulf offshore commercial reef fisheries, species specific results, and gear dependent effects. It directly contradicts a universal moon phase rule.

### F06
**Source:** James D. Murray, David G. Lindquist, David C. Griffith, and Jeffrey C. Howe. [The Use of Midwater Fish Aggregating Devices to Attract Marine Fish at Two North Carolina Fishing Piers](https://repository.library.noaa.gov/view/noaa/43068). UNC Sea Grant College Program, 1985, publication 85-1.

**Claim supported:** Experimental devices attracted baitfish but did not improve fishing success at the piers.

**Evidence type and applicability:** Direct North Carolina pier experiment.

**Limitations:** Preliminary study with limited configuration testing. It supports the distinction between aggregation and improved angler catch.

### F07
**Source:** Miguel Cabanellas-Reboredo, Josep Alós, Miquel Palmer, and Beatriz Morales-Nin. [Environmental effects on recreational squid jigging fishery catches](https://doi.org/10.1093/icesjms/fss159). *ICES Journal of Marine Science*, 2012, 69(10), 1823 to 1830.

**Claim supported:** Environmental variables, including pressure, wind, SST, season, and lunar state, were associated with European squid catch per unit effort.

**Evidence type and applicability:** Peer reviewed experimental recreational style fishery study.

**Limitations:** One species, one gear, one Mediterranean inshore boat fishery, and multiple correlated environmental variables. Poor transferability to species agnostic North Carolina shore fishing.

### F08
**Source:** Anne C. Utne-Palm. [Visual feeding of fish in a turbid environment: Physical and behavioural aspects](https://doi.org/10.1080/10236240290025644). *Marine and Freshwater Behaviour and Physiology*, 2002, 35(1 to 2), 111 to 128.

**Claim supported:** Turbidity can either improve or reduce prey contrast depending on suspended particles, light, and predator visual sensitivity.

**Evidence type and applicability:** Peer reviewed synthesis of physical and behavioral mechanisms.

**Limitations:** The direction is predator, prey, and optical context dependent. It does not provide one favorable turbidity rule.

### F09
**Source:** Arshpreet Bassi, Oliver P. Love, Steven J. Cooke, Theresa R. Warriner, Christopher M. Harris, and Christine L. Madliger. [Effects of artificial light at night on fishes: A synthesis with future research priorities](https://doi.org/10.1111/faf.12638). *Fish and Fisheries*, 2022.

**Claim supported:** Artificial light can alter fish behavior, abundance, community structure, and physiology.

**Evidence type and applicability:** Peer reviewed synthesis.

**Limitations:** Fish studies remain underrepresented, long term fitness evidence is limited, and responses vary by species and habitat.

### F10
**Source:** Alistair Becker, Alan K. Whitfield, Paul D. Cowley, Johanna Järnegren, and Tor F. Næsje. [Potential effects of artificial light associated with anthropogenic infrastructure on the abundance and foraging behaviour of estuary associated fishes](https://doi.org/10.1111/1365-2664.12024). *Journal of Applied Ecology*, 2013, 50, 43 to 50.

**Claim supported:** Experimental lighting changed fish abundance and behavior near an illuminated estuarine structure.

**Evidence type and applicability:** Peer reviewed manipulative field study.

**Limitations:** One estuarine structure and community. Aggregation near light does not establish a universal catch benefit.

### F11
**Source:** NOAA National Data Buoy Center. [How are significant wave height, dominant period, average period, and wave steepness calculated?](https://www.ndbc.noaa.gov/faq/wavecalc.shtml).

**Claim supported:** Authoritative definitions for significant wave height and dominant and average wave periods.

**Evidence type and applicability:** Government variable definition.

**Limitations:** Defines measurements. It does not prove biological or catch effects, and offshore buoy values are not beach breaker height.

### F12
**Source:** NOAA Center for Operational Oceanographic Products and Services. [CO-OPS Data Retrieval API](https://api.tidesandcurrents.noaa.gov/api/prod/) and [Web Services](https://tidesandcurrents.noaa.gov/web_services_info.html).

**Claim supported:** Public access to tide predictions, water levels, currents, station metadata, datums, and interval rules. Harmonic and subordinate stations have different prediction options.

**Evidence type and applicability:** Authoritative government source and interface documentation.

**Limitations:** A station must be mapped defensibly to the fishing location. Water level and current are separate products. Subordinate stations may provide high and low predictions only.

### F13
**Source:** U.S. Geological Survey. [USGS Water Data APIs](https://www.usgs.gov/tools/usgs-water-data-apis) and [API documentation](https://api.waterdata.usgs.gov/docs/).

**Claim supported:** Machine readable access to current measurements, daily values, historical data, monitoring locations, and streamflow.

**Evidence type and applicability:** Authoritative government data service.

**Limitations:** Provider availability does not prove that a gage is hydrologically connected to a SaltBytes site. Legacy WaterServices are scheduled for decommissioning in early 2027.

### F14
**Source:** NOAA National Estuarine Research Reserve System Centralized Data Management Office. [SWMP Data Parameters](https://www.nerrsdata.org/data/parameters.cfm).

**Claim supported:** Reserve water quality stations report temperature, salinity, dissolved oxygen, depth, and related parameters at 15 minute intervals.

**Evidence type and applicability:** Authoritative monitoring program documentation.

**Limitations:** Reserve stations are estuarine and location specific. Metadata and vertical control differ by station.

### F15
**Source:** Southeast Coastal Ocean Observing Regional Association. [SECOORA ERDDAP](https://erddap.secoora.org/erddap) and [North Carolina, South Carolina, and Florida Moorings](https://secoora.org/projects/north-carolina-south-carolina-moorings-university-of-north-carolina-wilmington/).

**Claim supported:** Public machine readable access to regional buoy, station, water quality, current, depth, temperature, and salinity datasets, including Carolinas observing systems.

**Evidence type and applicability:** Regional observing network and data service.

**Limitations:** Coverage is station and project dependent. Individual stations, variables, and update continuity must be checked before implementation.

### F16
**Source:** NOAA CoastWatch. [Data Access Tools](https://coastwatch.noaa.gov/cwn/data-access-tools.html) and [ERDDAP dataset catalog](https://coastwatch.noaa.gov/erddap/info/index.html).

**Claim supported:** Public subset and download access to gridded environmental datasets, including SST and chlorophyll products.

**Evidence type and applicability:** Authoritative satellite and gridded data service.

**Limitations:** Product resolution, algorithm, cloud gaps, measurement type, continuity, and shoreline representativeness vary by dataset. Chlorophyll is not direct baitfish observation.

### F17
**Source:** NOAA Office of Coast Survey. [BlueTopo](https://nauticalcharts.noaa.gov/data/bluetopo.html) and [BlueTopo specifications](https://www.nauticalcharts.noaa.gov/data/bluetopo_specs.html).

**Claim supported:** Public curated bathymetric models with source and quality metadata.

**Evidence type and applicability:** Authoritative government geospatial product.

**Limitations:** Data combine sources of varying age and quality, may include interpolation, use NAVD88 rather than a navigational datum, and are not guaranteed to represent current beach morphology.

### F18
**Source:** U.S. Naval Observatory Astronomical Applications Department. [Data Services](https://aa.usno.navy.mil/data/) and [API documentation](https://aa.usno.navy.mil/data/api.html).

**Claim supported:** Public calculation services for sunrise, sunset, twilight, moonrise, moonset, lunar phases, and illumination.

**Evidence type and applicability:** Authoritative astronomical calculation service.

**Limitations:** Availability and calculation accuracy do not establish fishing relevance.

### Project inference and repository references

#### P01
**Inference:** Reviewed shoreline or pier orientation can convert existing wind and wave compass direction into deterministic site relative angles and components.

**Basis:** Current SaltBytes direction fields, basic vector geometry, and the physical need for a local reference frame.

**Limitation:** The orientation itself must be manually reviewed. The transformation does not model nearshore refraction, sheltering, or bathymetric change.

#### P02
**Inference:** Adjacent stored high and low tide events can support time to extrema and predicted range fields.

**Basis:** Existing event times, event types, predicted levels, station mapping, and datum metadata.

**Limitation:** This does not create a continuous hourly water level or tidal current.

#### P03
**Inference:** Several physical variables have clear practical fishability uses even when direct catch evidence is weak.

**Basis:** The variable's physical meaning and SaltBytes use case.

**Limitation:** Project inference is not presented as fisheries science and cannot justify universal catch direction.

#### P04
**Project decision:** Access status may be retained as factual operational context. Personal safety interpretation and safety only warning feeds are outside registry scope.

#### R01
**Repository source:** `src/saltbytes/api.py`, audited 2026-07-31.

**Claim supported:** SaltBytes requests hourly wind speed, wind direction, wind gusts, precipitation probability, precipitation, wave height, wave direction, wave period, and sea surface temperature.

#### R02
**Repository source:** `src/saltbytes/database.py`, audited 2026-07-31.

**Claim supported:** SaltBytes persists the current hourly environmental fields, tide high and low event times and predicted levels, hourly tide phase, source results, and integrated hourly conditions. The integrated view exposes tide phase but not tide event level, range, or time to extrema.

#### R03
**Repository source:** `config/local.yml`, audited 2026-07-31.

**Claim supported:** SaltBytes stores fishing context, source coordinates, tide station relationships, transfer metadata, datum related offsets and multipliers, and known tide limitations. It does not store reviewed shoreline or pier orientation.

#### R04
**Repository source:** `docs/roadmap.md`, audited 2026-07-31.

**Claim supported:** The immediate sequence after the registry is tide state completion, reviewed orientation metadata, then wind and wave directional interactions.
