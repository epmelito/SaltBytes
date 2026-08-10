# Location-first species-assessment direction

## Status

Accepted

Supersedes [decision 0010](0010-research-backed-fishing-score-direction.md).

## Context

The Spanish mackerel score established that an explicit, explainable numeric
method can be useful for a bounded species context. It does not establish that a
single 0 to 100 model is the right product shape for every species or fishing
location.

SaltBytes needs a durable direction for answering a location-first question:
what species can an angler realistically target at or near this location, when,
and why? The completed statewide observational-source investigation found enough
useful reporting to continue designing that foundation.

## Decision

SaltBytes will develop location-first, species-aware assessments from three
distinct evidence layers:

- reusable statewide species knowledge
- recent fishing observations
- forecast and site conditions

An assessment must preserve uncertainty and the scope of its evidence. Recent
observations can strengthen an assessment, but cannot by themselves make a
species targetable. Factual catch observations, source advice, and forecasts
remain distinct; a source not mentioning a species is not evidence of absence.
Future observation work must preserve spatial scope and observation strength as
separate dimensions.

SaltBytes will not depend on one observational publisher. Candidate sources use
a project risk assessment of `green`, `yellow`, or `red`; it is not a legal
conclusion. Production work must avoid unacceptable dependencies, including
authentication or technical-control circumvention, and future commercialization
requires a bounded legal review of the completed source and collector design.

Reusable species knowledge should support North Carolina saltwater contexts
without prematurely fixing the statewide taxonomy. Future locations should be
classified by relevant context and source relationships rather than requiring
new species research for every location.

Numeric species scores are optional, not the universal product model. Spanish
mackerel remains a valid earlier numeric experiment governed by its approved
methodology. Any later numeric species method requires its own explicit approval
and methodology.

## Consequences

The roadmap first establishes a source-independent observation product contract
and location foundations before resuming species-assessment implementation. The
current roadmap owns the near-term location sequence.

The deterministic red drum score path is paused. Its existing research remains
useful for a later location-first assessment.

A general fishing-conditions or fishability score remains a deep future
possibility. Its inputs, meaning, and method are deferred; individual numeric
species scores are not prerequisites for it.

## Alternatives considered

### Mandatory numeric scores for every species

This is superseded because the available evidence supports different assessment
forms across species and locations. A numeric method remains available when a
separate approved methodology justifies it.

### Observations as the sole targetability signal

This was rejected because source coverage can change and report silence does not
show absence. Observations strengthen, rather than replace, species knowledge
and forecast or site context.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Roadmap: [Current roadmap](../roadmap.md) and [project roadmap](../project-roadmap.md)
- Numeric methods: [Species conditions scoring requirements](../requirements/species-condition-scoring.md)
- Earlier decision: [Research backed species conditions scoring direction](0010-research-backed-fishing-score-direction.md)
