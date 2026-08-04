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
- the internal Spanish mackerel conditions score calculation

The next objective is bounded Spanish mackerel score publication.

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
The methodology is implemented internally but is not persisted or published.

## Next objective: bounded Spanish mackerel score publication

Publish the approved version 1 Spanish mackerel conditions score through a
bounded reporting package.

The publication work must preserve:

- the exact approved eligibility and availability rules
- the implemented deterministic calculation and methodology version
- separate score confidence, positive, limiting, and unknown factor states
- the distinction between modeled conditions alignment and fish presence or
  catch probability

The publication package must not add unapproved factors, providers, or the
future overall-score aggregation method.

## Later sequence

```text
Completed: species selection, research registry, score direction, methodology, and calculation
→ next: bounded Spanish mackerel score publication
→ later: additional species models
→ future: overall fishing conditions score aggregation
```

The overall fishing conditions score is an approved product direction, but its
aggregation method remains undecided until multiple species models exist.
