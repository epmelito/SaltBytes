# Roadmap

## Current position

SaltBytes has completed:

- hosted six hour ingestion with durable Azure state
- forecast history and revision retention
- the species agnostic fishing factor registry
- the first research backed coastal attributes
- static and interactive public reporting
- the first analysis ready feature layer
- solar and ambient light context
- priority North Carolina shore-species selection
- the species opportunity research registry
- the durable product decision for research backed species conditions scores
- the first approved Spanish mackerel score methodology

The next objective is bounded Spanish mackerel score implementation.

SaltBytes does not yet provide species conditions scores, an overall fishing
conditions score, ranked fishing windows, or catch probability.

## Completed milestones

### Solar and ambient light context

Solar context, cloud cover, provenance, and explicit missing-input behavior are
complete.

### Priority North Carolina shore-species selection

The approved seven-species set and Spanish mackerel pilot are recorded in the
[species research package](research/nc-shore-species-research.md#2-research-outcome).

### Species opportunity research registry

Evidence profiles, shared synthesis, deferred inputs, prohibited
interpretations, decisions, and references are complete in the canonical
[species research package](research/nc-shore-species-research.md). Use the
[research navigation index](research/README.md) to locate the smallest relevant
section.

### Research backed species score direction

The durable product direction is recorded in
[decision 0010](decisions/0010-research-backed-fishing-score-direction.md), with
shared requirements in
[species conditions scoring requirements](requirements/species-condition-scoring.md).

### Spanish mackerel score methodology

The approved version 1 calculation, availability rules, confidence dimensions,
explanations, and validation scenarios are recorded in the
[Spanish mackerel conditions score methodology](requirements/spanish-mackerel-conditions-score.md).
The methodology is approved but not implemented.

## Next objective: bounded Spanish mackerel score implementation

Implement the approved version 1 Spanish mackerel conditions calculation against
existing normalized inputs.

The implementation work must preserve:

- the exact approved eligibility and availability rules
- deterministic seasonal, thermal, biological, wind, wave, and final-score
  calculations
- score confidence as separate categorical dimensions
- positive, limiting, and unknown factor selection
- methodology versioning and approved validation scenarios
- the distinction between modeled conditions alignment and fish presence or
  catch probability

The implementation package must not add unapproved factors, providers, report
fields, dashboard behavior, or the future overall-score aggregation method.
Publication remains a later bounded reporting package.

## Later sequence

```text
Completed: species selection, research registry, score direction, and first methodology
→ next: bounded Spanish mackerel score implementation
→ later: bounded score publication
→ later: additional species models
→ future: overall fishing conditions score aggregation
```

The overall fishing conditions score is an approved product direction, but its
aggregation method remains undecided until multiple species models exist.
