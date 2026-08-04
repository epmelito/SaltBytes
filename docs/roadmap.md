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

The next objective is Spanish mackerel scoring methodology design.

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

## Next objective: Spanish mackerel scoring methodology

Define a deterministic and explainable 0 to 100 Spanish mackerel conditions
score using the approved research package and existing SaltBytes inputs.

The methodology must define:

- what the score represents and how the 0 to 100 range is interpreted
- the included dimensions and factor contribution rules
- treatment of season, habitat, environmental alignment, and practical
  fishability
- explicit behavior for missing or unavailable inputs
- confidence that remains separate from the conditions score
- positive, limiting, and unknown factors shown with the score
- methodology versioning
- validation scenarios and prohibited claims

The methodology must not claim catch probability, bite likelihood, guaranteed
presence, or substitute unavailable local biology with proxy inputs.

No weights, thresholds, curves, score bands, equations, implementation schema,
or report behavior are approved by this roadmap. Those decisions belong to the
methodology work package.

## Later sequence

```text
Completed: species selection, research registry, and score direction
→ next: Spanish mackerel scoring methodology
→ later: bounded Spanish mackerel score implementation
→ later: additional species models
→ future: overall fishing conditions score aggregation
```

The overall fishing conditions score is an approved product direction, but its
aggregation method remains undecided until multiple species models exist.
