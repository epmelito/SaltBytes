# Roadmap

## Current position

SaltBytes has completed:

- hosted six hour ingestion with durable Azure state
- forecast history and revision retention
- the species agnostic fishing factor registry
- the first research backed coastal attributes
- static and interactive public reporting
- the first analysis ready feature layer

The next objective is to complete solar and ambient light context, then define
the first target species scope.

SaltBytes does not yet provide species opportunity assessments, ranked fishing
windows, or catch probability.

## 1. Add solar and ambient light context

### Objective

Add the remaining low effort contextual inputs needed before target species
rules are defined.

### Scope

- persist immutable display latitude
- persist immutable display longitude
- persist immutable display timezone
- derive sunrise and sunset
- derive civil dawn and civil dusk
- derive hourly solar state
- derive time relative to sunrise and sunset
- ingest hourly cloud cover
- preserve source and calculation provenance

### Boundaries

- do not assign universal positive or negative values to dawn, daylight, dusk,
  or night
- do not claim cloud cover directly measures underwater light
- do not add moon phase, solunar indexes, or barometric pressure as universal
  predictors
- do not introduce scoring weights
- do not add a new external provider unless repository discovery proves it is
  necessary

### Exit criteria

- location and timezone inputs are retained immutably
- solar calculations are deterministic and reproducible
- solar state is available at the existing hourly grain
- cloud cover is validated and source attributable
- missing solar or cloud inputs remain explicit
- documentation and tests define the new semantics

## 2. Select priority North Carolina shore species

### Objective

Choose a small, evidence based first set of target species.

### Scope

Use recent multi year evidence where possible, including:

- North Carolina shore mode recreational catch estimates
- directed fishing effort where available
- North Carolina recreational fishing reports
- surf and pier occurrence
- relevance across the five SaltBytes locations
- applicability to surf, pier, or both
- quality of species specific research
- compatibility with existing or feasible SaltBytes inputs
- regulatory complications affecting public presentation

### Expected output

Produce a concise selection reference that:

- identifies approximately five to eight initial species
- explains why each species was selected
- identifies surf, pier, or mixed applicability
- records excluded candidates and reasons
- distinguishes fishing popularity from management importance
- identifies one pilot species

### Boundaries

- do not select species from generic popularity articles alone
- do not mix shore fishing with offshore or private boat catch without
  qualification
- do not treat harvest regulations as evidence of environmental opportunity
- do not define implementation rules in this work package

### Exit criteria

- the selection method is documented
- selected species are relevant to North Carolina shore fishing
- location and fishing context applicability is explicit
- one pilot species is justified
- major evidence gaps remain visible

## 3. Build the species opportunity research registry

### Objective

Define the evidence supported factors and interpretations for the selected
species.

### Scope

For each selected species, document:

- seasonal availability
- North Carolina geographic applicability
- surf, pier, inlet, sound, or structure relevance
- SST relationships
- solar and diel behavior
- tide and water movement relationships
- habitat associations
- migration and spawning timing
- salinity, turbidity, or freshwater influence where relevant
- evidence strength
- transferability limitations
- supported and unsupported interpretations
- current SaltBytes coverage
- missing high value inputs

### Required distinctions

Keep separate:

- biological availability
- environmental alignment
- practical fishability
- evidence confidence
- safety information
- regulations and harvest opportunity

### Boundaries

- do not create catch probability
- do not invent precise thresholds from broad qualitative evidence
- do not convert angler folklore into deterministic rules
- do not double count SST, photoperiod, migration, and seasonal timing
- do not require every species to use every factor
- preserve contradictory findings

### Exit criteria

- every selected species has an evidence profile
- shared common metrics are identified
- species specific metrics remain explicit
- unsupported rules are excluded
- the pilot species has an implementation ready contract
- remaining research gaps are documented

## Immediate sequence

```text
Solar and ambient light context
→ priority North Carolina shore species selection
→ species opportunity research registry
```

After these milestones, replace this roadmap group with the next bounded set
based on the approved pilot species and implementation contract.
