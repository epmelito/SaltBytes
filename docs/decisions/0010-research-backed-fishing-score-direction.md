# Research backed species conditions scoring direction

## Status

Accepted

## Context

SaltBytes already collects and publishes the environmental inputs needed to
begin species-specific interpretation. The North Carolina shore-fishing species
research package establishes the approved species set, identifies Spanish
mackerel as the strongest pilot, separates biological alignment from practical
fishability, and records important unknown local biology.

Earlier decisions intentionally deferred species-specific use cases,
recommendations, and scoring until biological evidence and scoring choices were
available. That research is now complete enough to establish the species
conditions scoring direction, but it does not authorize other species-specific
product behavior or define weights, thresholds, equations, or a validated
prediction model.

A scoreless categorical assessment would preserve uncertainty but would not
deliver the intended product value. Catch probability would overstate the
available evidence and validation data.

## Decision

SaltBytes will develop deterministic, explainable 0 to 100 species conditions
scores.

A species conditions score represents SaltBytes' assessment of how favorable
the available location, seasonal, habitat, environmental, and practical
fishability conditions are for targeting that species according to approved
research.

Each implemented species score must:

- use an explicit, versioned methodology
- expose material positive and limiting factors
- expose important unknown factors
- keep evidence and input confidence separate from the conditions score
- preserve species and location applicability
- handle missing inputs explicitly
- remain reproducible from the same inputs and methodology version

The score does not represent:

- catch probability
- bite probability
- proof that the species is present
- proof that fish are within casting range
- expected catch count
- guaranteed fishing success
- an opaque AI-generated recommendation

Unavailable local biology, including prey, school presence, fish depth, feeding
state, and casting-range access, must remain unknown. SaltBytes must not replace
those observations with unsupported proxies.

Spanish mackerel will be the first scoring methodology and implementation pilot.

SaltBytes may later provide an overall fishing conditions score that summarizes
the quality of relevant species-targeting options for a location and forecast
period. The aggregation method remains deferred until multiple species models
exist.

Safety information remains separate from fishing quality and must not silently
increase or decrease a species score.

This decision resolves only the deferral of deterministic species conditions
scoring for the approved shore species in decisions 0001 and 0003. It does not
authorize other species-specific use cases or recommendation behavior. Their
audience, fishing-context, environmental, provenance, source-quality, and safety
boundaries remain accepted.

## Consequences

Benefits:

- gives the product a clear user-facing analytical objective
- distinguishes a conditions assessment from an unsupported prediction
- allows species-specific research to influence results without hiding the
  reasoning
- preserves uncertainty through separate confidence and unknown-factor output
- creates a path from the current data platform to species reports and a future
  overall fishing conditions score

Costs and limitations:

- the first methodology will be an evidence-informed heuristic index rather
  than an empirically calibrated prediction model
- weights, curves, thresholds, and interactions require explicit design
- unobserved prey and local fish presence will continue to limit interpretation
- score changes require methodology versioning and review
- the overall score cannot be designed responsibly from one species model

Follow-up work:

- define the Spanish mackerel scoring methodology
- approve score dimensions, factor contributions, missing-input behavior,
  confidence treatment, explanation rules, and validation scenarios
- implement the bounded Spanish mackerel score only after that methodology is
  approved
- evaluate additional species models before selecting an overall aggregation
  method

## Alternatives considered

### Scoreless categorical assessment

This would provide labels such as aligned, constrained, or uncertain without a
numeric index. It was rejected as the primary product direction because it does
not provide the comparable species and overall conditions assessment that
SaltBytes is intended to deliver.

### Catch or bite probability

This was rejected because SaltBytes lacks the direct observations, catch
history, and validation data needed to support a calibrated probability.

### Opaque AI-generated score

This was rejected because users could not inspect the assumptions, factor
contributions, or methodology changes.

### Define the overall score now

This was deferred because one species model cannot establish a defensible
cross-species aggregation rule.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Roadmap: [Roadmap](../roadmap.md)
- Requirements: [Species conditions scoring](../requirements/species-condition-scoring.md)
- Research: [North Carolina shore-fishing species research package](../research/nc-shore-species-research.md)
- Earlier decision: [First-release user and fishing-context boundary](0001-first-release-user-and-fishing-context.md)
- Earlier decision: [First-release environmental requirement baseline](0003-first-release-environmental-requirement-baseline.md)
