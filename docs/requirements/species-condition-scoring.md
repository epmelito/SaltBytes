# Species conditions scoring requirements

## Status

Approved product boundary. No scoring formula or implementation is approved by
this document.

## Purpose

SaltBytes will provide deterministic and explainable 0 to 100 conditions scores
for individual target species.

A species conditions score represents how favorable the available location,
seasonal, habitat, environmental, and practical fishability conditions are for
targeting that species according to approved research.

It is a conditions alignment index. It is not a probability or proof of fish
presence.

## Required score contract

Each species scoring methodology must define:

- the meaning of the 0 to 100 range
- the species and location contexts where the score applies
- the dimensions and factors included
- each factor's contribution rule and evidence basis
- interactions and protections against duplicate credit
- behavior for missing, failed, unavailable, and not-applicable inputs
- the confidence dimensions reported separately from the score
- the positive, limiting, and unknown factors shown with the result
- deterministic rounding and boundary behavior
- a methodology version
- validation scenarios and prohibited interpretations

The same normalized inputs and methodology version must produce the same
result.

No factor may enter a score only because it is available from a provider. Its
role must be supported by the authoritative species research and the approved
methodology.

## Score and confidence

The conditions score and confidence must remain separate.

The score describes alignment of the available conditions. Confidence describes
how complete, representative, applicable, and well supported the assessment is.

A missing or failed input must not silently behave as an unfavorable condition.
The methodology must state whether the score is unavailable, calculated from a
reduced input set, or handled another explicit way. The associated confidence
and unknown factors must remain visible.

Unobserved local biology must not receive fabricated positive or negative
values. It must remain an explicit unknown unless a reviewed direct source is
later approved.

## Explanation requirements

Each score result must identify the material reasons behind the number.

The explanation must distinguish:

- species and location applicability
- seasonal and environmental alignment
- practical fishability
- limiting conditions
- unavailable or unobserved biology
- data and evidence confidence

The score may combine approved dimensions into one index, but it must not hide
which dimensions drove the result.

## User-facing presentation

Score labels, explanations, confidence, positive factors, limiting factors, and
unknowns must follow the
[user-facing language requirements](user-facing-language.md). They must sound
natural to recreational anglers, explain necessary technical ideas in context,
and preserve uncertainty without reading like research prose.

Internal factor names, field names, evidence classifications, and model
terminology must not become default product copy merely because they exist in
the research or implementation. Final wording remains part of the methodology
and reporting work; this document does not select specific labels or phrases.

## Interpretation boundaries

A species conditions score must not be described as:

- catch probability
- bite probability
- expected catch count
- proof that fish are present
- proof that fish are within casting range
- guaranteed success
- an optimal-temperature claim
- a universal tide, solar, cloud, pressure, or weather rule

The score must not use unsupported proxies for prey, fish presence, water
quality, current, habitat occupancy, or other missing biology.

Practical fishability may affect the score when the approved methodology
defines its role, but it must not be relabeled as biological activity.

Official safety products and personal safety decisions remain separate from
fishing quality.

## First methodology

Spanish mackerel is the first scoring methodology pilot.

The methodology must use the authoritative Spanish mackerel profile and shared
research synthesis. This requirements document does not approve:

- factor weights
- numeric thresholds or score bands
- curves or equations
- seasonal boundaries
- thermal cutoffs
- report wording
- persistence schemas
- dashboard behavior
- new data providers

Those choices require a separate approved methodology work package.

## Future overall fishing conditions score

SaltBytes may later publish an overall fishing conditions score for a location
and forecast period.

The overall score should represent the quality of relevant species-targeting
options, not the average catch probability across species.

Its aggregation rule remains deferred until multiple species models exist.
Future design must resolve:

- species applicability and seasonal relevance
- treatment of unavailable species scores
- whether one strong species can dominate the result
- whether the result uses an average, weighted blend, top-species blend, or
  another transparent method
- explanation and confidence across the contributing species

## Related governance

- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Decision 0010](../decisions/0010-research-backed-fishing-score-direction.md)
- [Fishing-condition requirements](fishing-conditions.md)
- [Analysis-ready feature contract](analysis-ready-features.md)
- [User-facing language requirements](user-facing-language.md)
- [North Carolina shore-fishing species research package](../research/nc-shore-species-research.md)
