# Sound-side location expansion

## Status

Accepted

## Context

SaltBytes' first-release location model covers ocean-side surf and publicly
accessible fixed fishing piers. The active location-first species-assessment
direction requires future locations to be classified by relevant context and
source relationships rather than forcing every location into the original
first-release contexts.

The current roadmap identifies Little Bridge Sound Access as the leading
seventh-location candidate and requires the sound-side expansion decision before
bounded observational ingestion work is defined.

The Town of Nags Head
[lists Little Bridge Sound Access](https://www.nagsheadnc.gov/facilities/facility/details/Little-Bridge-Sound-Access-14)
as a public fishing facility with parking, restrooms, and water, accessed
2026-08-12.

Little Bridge represents a materially different fishing environment from the
existing Atlantic-facing surf and pier locations. Existing SaltBytes
location-source decisions also establish that a destination coordinate cannot be
treated as a universal sampling point and that environmental relationships must
be approved by source and product.

The current evidence does not establish that the existing ocean-facing marine
relationships are representative of Little Bridge. No Little Bridge water
temperature, wave, water-level, current, or other marine relationship has yet
been approved.

Observation value and environmental-source feasibility are separate questions.
Useful fishing reports associated with Little Bridge do not establish that an
environmental product is representative of the location.

## Decision

SaltBytes will expand its location model to support a `sound-side` fishing
context.

`Sound-side` is the minimum new context needed for the current expansion. This
decision does not create a general estuary, inlet, river, marsh, or statewide
habitat taxonomy.

Little Bridge Sound Access is approved as the first planned SaltBytes location
representing the sound-side context and remains the planned seventh location in
the current sequence.

Approval of the location does not approve its environmental-source
relationships.

Before Little Bridge is implemented with environmental conditions, bounded
location-source work must establish any required relationships independently,
including where applicable:

- weather
- water temperature
- water level or tide
- currents
- waves

A source or product may be unavailable or not applicable to the sound-side
context. SaltBytes must preserve that limitation rather than substitute an
ocean-facing relationship or imply unsupported representativeness.

Existing Atlantic-facing marine request or returned-grid relationships must not
be reused for Little Bridge without separate evidence.

Little Bridge observational evidence remains governed independently by the
fishing observation contract and source-suitability research. Approval of the
location does not change the current suitability classification of any
observation publisher.

## Consequences

SaltBytes can represent a shore-accessible sound fishing destination without
misclassifying it as surf or pier.

The location-first product gains a materially different coastal context useful
for later species assessments, including species and life stages whose
shore-accessible habitat is not limited to the Atlantic shoreline.

The expansion creates additional location-source work. Little Bridge cannot
inherit the five existing locations' marine relationships merely because those
sources are already implemented.

Missing or unsuitable environmental relationships may reduce what SaltBytes can
publish for Little Bridge until supported sources are established. That
limitation must remain visible rather than being hidden through fallback data.

This decision does not require Little Bridge implementation to occur before the
planned sixth location, Sunset Beach Pier. The current roadmap continues to own
delivery sequencing.

## Alternatives considered

### Keep SaltBytes limited to surf and pier contexts

Rejected. The active location-first direction is intended to support relevant
North Carolina shore-accessible fishing contexts. Restricting every future
location to the original first-release categories would prevent a useful
sound-side expansion.

### Treat Little Bridge as surf or pier

Rejected. Neither label describes the fishing context accurately enough, and
doing so would make observational and environmental evidence appear more
comparable than the current evidence supports.

### Defer Little Bridge until every environmental relationship is solved

Rejected. Location suitability and environmental-source feasibility are
separate decisions. The location and context can be approved while unsupported
source relationships remain explicitly unresolved.

### Reuse nearby ocean-facing marine relationships

Rejected. Existing SaltBytes spatial policy requires source relationships to
preserve their actual geographic meaning. No evidence supports treating an
Atlantic-facing marine relationship as representative of Little Bridge solely
because it is nearby.

## Related governance

- [Location-first species-assessment direction](0011-location-first-species-assessment-direction.md)
- [Composite geographic model and initial locations](0002-composite-geographic-model-and-initial-locations.md)
- [Final first-release location-to-source relationships](0007-final-location-source-relationships.md)
- [Coastal location requirements](../requirements/coastal-locations.md)
- [Fishing observation requirements](../requirements/fishing-observations.md)
- [Fishing observation source suitability assessment](../research/fishing-observation-source-suitability.md)
- [Current roadmap](../roadmap.md)
