# First-release user and fishing-context boundary

## Status

Accepted

## Context

SaltBytes needs a bounded first-release audience and fishing context before
location and environmental requirements can guide later data work.

The project charter calls for representative North Carolina coastal fishing
locations and explainable environmental data. It does not select fishing modes
or a species boundary.

Research considered surf, publicly accessible fixed fishing pier,
shore-accessed inlet, vessel-based nearshore, and offshore contexts. These
contexts have different access, environmental, marine, and safety
relationships. Directly comparing all of them would require requirements and
data relationships that are not yet defined.

Species-specific recommendations would also require biological evidence and
scoring choices beyond the current stage.

## Decision

The first release will serve general recreational coastal anglers.

It will include:

- surf fishing
- fishing from publicly accessible fixed fishing piers
- general environmental conditions rather than species-specific recommendations
- comparison of windows only within the same fishing context

It will defer:

- shore-accessed inlet fishing
- vessel-based nearshore fishing
- offshore fishing
- species-specific use cases and recommendations

The first release will not compare a surf window directly with a pier window.

## Consequences

Benefits:

- bounds the first release to two shore-based environmental contexts
- supports geographic variety without introducing vessel or offshore
  requirements
- permits ingestion, spatial relationships, and later metrics to distinguish
  surf and pier conditions
- avoids unsupported species and catch claims
- provides a clear comparison boundary

Costs and limitations:

- users cannot compare all coastal fishing modes
- the first release will not answer species-specific questions
- future contexts may require different data, safety, and scoring decisions
- context identity must be retained through modeling and publication

Follow-up work:

- document the context of every first-release location
- preserve the context in normalized and published data
- evaluate any future inlet, vessel, offshore, or species-specific expansion as
  separately authorized work

## Alternatives considered

### Surf only

This would provide the narrowest initial boundary but would not demonstrate
environmental comparison for publicly accessible fixed fishing piers.

### Publicly accessible fixed fishing piers only

This would simplify access identity but would omit the approved surf use case
and reduce geographic and environmental variety.

### Surf and publicly accessible fixed fishing piers

This is the accepted choice. It provides two bounded shore-based contexts while
requiring comparisons to remain within context.

### Include shore-accessed inlet fishing

This would introduce current, inlet geometry, access, and safety relationships
that have not been selected for the first release.

### Include vessel-based nearshore or offshore fishing

This would introduce vessel safety, navigation, offshore forecast, and broader
marine requirements. The research did not establish a compelling reason to
include them in the first release.

### Species-specific recommendations

This would require biological evidence and scoring decisions that remain
deferred.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Scope: [Scope register](../scope-register.md)
- Roadmap stage: [Stage 3](../roadmap.md#3-define-coastal-locations-and-fishing-condition-requirements)
- Requirements: [Coastal location requirements](../requirements/coastal-locations.md)
- Requirements: [Fishing-condition requirements](../requirements/fishing-conditions.md)
