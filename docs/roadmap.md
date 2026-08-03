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

The next objective is a bounded Spanish mackerel implementation pilot.

SaltBytes does not yet provide species opportunity assessments, ranked fishing
windows, or catch probability.

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

## Next objective: Spanish mackerel implementation pilot

Implement a bounded pilot for shore-accessible Spanish mackerel that follows
the approved evidence, coverage, limits, and prohibited interpretations. The
pilot must not claim catch probability, use deterministic opportunity scoring,
or substitute unavailable local biology with proxy inputs.

## Implementation sequence

```text
Completed: solar and ambient light context
→ completed: North Carolina shore-species selection and research registry
→ next: Spanish mackerel implementation pilot
```

Use the canonical package's supported and prohibited interpretations to bound
the pilot; do not restore an implementation-ready research contract section.
