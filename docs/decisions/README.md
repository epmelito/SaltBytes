# Decision records

## Purpose

Decision records preserve the context, choice, rationale, and consequences of
durable SaltBytes product, data, and architecture decisions.

## When a record is required

Create a decision record when work requires a durable choice that:

- selects between meaningful product, data, or architecture alternatives
- resolves an intentionally deferred decision
- changes an accepted technical or operational direction
- introduces a meaningful cross-cutting, long-lived, or difficult-to-reverse
  constraint
- supersedes an earlier accepted decision

Routine implementation details that follow existing accepted direction do not
require a record.

Deferred topics remain governed by the [project charter](../project-charter.md)
and [roadmap](../roadmap.md). They do not receive a decision record until active
work requires a concrete proposal.

## Responsibilities

Accepted decision records are authoritative for the specific choices they
cover. They must remain consistent with the product intent and durable
boundaries in the [project charter](../project-charter.md).

The [roadmap](../roadmap.md) identifies when a decision becomes necessary. A
handoff may reference a decision but cannot accept one.

## Statuses

- `proposed`: under review and not authoritative
- `accepted`: approved and active
- `rejected`: considered but not adopted
- `superseded`: replaced by a later accepted record

## Naming

Use a zero-padded sequence and concise lowercase slug:

```text
NNNN-short-decision-title.md
```

Assign the next available number when the proposed record is created. Do not
reuse numbers or rewrite accepted history.

## Record template

```markdown
# Decision title

## Status

Proposed

## Context

State the verified situation, constraints, and decision that is needed.

## Decision

State the chosen direction precisely.

## Consequences

Describe expected benefits, costs, limitations, and follow-up work.

## Alternatives considered

Summarize credible alternatives and why they were not selected.
If no credible alternative exists, state that explicitly instead of inventing
one.

## Related governance

- Charter:
- Product boundary:
- Roadmap:
```

Do not invent evidence, alternatives, or retrospective rationale.

## Lifecycle rules

- Proposed records may be revised during review.
- Accepted records are not rewritten except for minor factual corrections.
- Rejected records remain historical and are not rewritten into new proposals.
- A renewed proposal after rejection uses a new decision number and links the
  rejected record.
- An accepted record becomes superseded only after its replacement record is
  accepted.
- Superseded records remain unchanged except for their status and links to
  replacement records.

## Workflow

1. Confirm that the decision is required by active, approved work.
2. Create a proposed record with evidence and credible alternatives, or state
   that no credible alternative exists.
3. Review the proposal without treating it as accepted.
4. Mark the record accepted or rejected after explicit approval.
5. Update the index and any affected product-boundary or roadmap references.
6. When replacing a decision, mark the old record superseded and link both
   records.

## Index

| ID | Decision | Status | Supersedes or replacement |
| --- | --- | --- | --- |
| 0001 | [First-release user and fishing-context boundary](0001-first-release-user-and-fishing-context.md) | Accepted | None |
| 0002 | [Composite geographic model and initial locations](0002-composite-geographic-model-and-initial-locations.md) | Accepted | None |
| 0003 | [First-release environmental requirement baseline](0003-first-release-environmental-requirement-baseline.md) | Accepted | None |
| 0004 | [Spatial coordinate and returned-grid relationship policy](0004-spatial-coordinate-and-returned-grid-policy.md) | Accepted | None |
| 0005 | [First-release Open-Meteo atmospheric and marine model strategy](0005-open-meteo-model-strategy.md) | Accepted | None |
| 0006 | [Authoritative tide-product responsibility](0006-authoritative-tide-product-responsibility.md) | Accepted | None |
| 0007 | [Final first-release location-to-source relationships](0007-final-location-source-relationships.md) | Accepted | None |
| 0008 | [First-release NOAA tide relationships and phase](0008-noaa-tide-relationships-and-phase.md) | Accepted | None |
| 0009 | [Minimum coastal source-result validity rules](0009-coastal-source-result-validity-rules.md) | Accepted | None |
| 0010 | [Research backed species conditions scoring direction](0010-research-backed-fishing-score-direction.md) | Superseded | Replaced by [0011](0011-location-first-species-assessment-direction.md); preserves the rationale for the Spanish mackerel numeric experiment |
| 0011 | [Location-first species-assessment direction](0011-location-first-species-assessment-direction.md) | Accepted | Supersedes 0010; establishes the active product direction |
| 0012 | [Sound-side location expansion](0012-sound-side-location-expansion.md) | Accepted | None |
