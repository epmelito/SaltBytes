# Composite geographic model and initial locations

## Status

Accepted

## Context

A fishing destination can require several geographic relationships. A display
or destination coordinate identifies the location, while weather, marine, tide,
observation, warning, and forecast products may apply at different coordinates,
stations, datums, or zones.

A single point would conceal those relationships. A location name without
structured relationships would be easier to create but would not provide enough
traceability for later ingestion and interpretation.

The first release also needs a representative but bounded location set covering
the approved surf and publicly accessible fixed fishing pier contexts.

## Decision

SaltBytes will use a composite coastal location as its geographic modeling
unit.

A composite coastal location will identify:

- a stable location identity
- a public-facing name
- a fishing context
- a representative coastal region
- a display or destination coordinate
- a weather request coordinate
- a marine sampling coordinate or coordinates
- a tide or water-level reference relationship
- an observation-station relationship when applicable
- warning and forecast-zone mappings
- source-resolution limitations
- spatial-representativeness limitations

The initial location set will be:

| Location | Context |
| --- | --- |
| Jennette’s Pier | Pier |
| Beach Access Ramp 72, Ocracoke Island | Surf |
| Fort Macon State Park, ocean side | Surf |
| Bogue Inlet Pier | Pier |
| Fort Fisher State Recreation Area | Surf |

Bogue Inlet Pier will be treated only as a pier. Its name and proximity to
Bogue Inlet do not introduce an inlet fishing context, inlet-current
requirements, or inlet scoring.

Beach Access Ramp 72 will represent the ocean-side surf context reached from
the ramp. It will not represent Ocracoke Inlet or the sound shoreline.

The stable identities, public-facing names, fishing contexts, and
representative regions are part of this decision. Exact display or destination
coordinates, weather request coordinates, marine sampling coordinates, tide or
water-level references, observation relationships, and warning or forecast-zone
mappings will be documented before stage 4 ingestion is implemented.

## Consequences

Benefits:

- separates destination identity from environmental sampling relationships
- supports traceable source and zone mappings
- preserves fishing context as part of location identity
- provides northern, central, and southern coastal representation
- keeps the first-release location set bounded
- includes both approved fishing contexts

Costs and limitations:

- each location requires more documentation than a single coordinate
- multiple source relationships may need independent maintenance
- display or destination and environmental sampling points may not be spatially
  interchangeable
- the selected set is representative rather than exhaustive
- temporary closures can affect whether a selected location is currently usable

Follow-up work:

- document the display or destination coordinate for each location
- select and document weather and marine sampling coordinates
- establish tide or water-level reference relationships
- establish observation, warning, and forecast-zone relationships
- evaluate source resolution and spatial representativeness
- validate that each selected source represents the intended fishing context
- retain shore-accessed inlet, vessel-based nearshore, and offshore locations as
  deferred scope

## Alternatives considered

### Single coordinate

A single point is simple but cannot clearly represent separate access, marine,
tide, observation, and forecast relationships.

### Named fishing location

A named location improves interpretation but remains incomplete when
environmental products apply at different spatial or reference units.

### Composite coastal location

This is the accepted choice. It preserves user-facing identity while making
source relationships and limitations explicit.

### Larger candidate set

A larger set could increase coverage but would expand source evaluation and
implementation before the initial patterns are established.

### Ramp 59 instead of Ramp 72

Product-owner direction preferred the southern point unless the northern point
was materially better for the approved location criteria. Reviewed evidence did
not establish a material geographic or environmental-modeling advantage for
Ramp 59, so Ramp 72 was selected. Temporary NPS closures can affect whether
Ramp 72 is currently usable.

## Related governance

- Charter: [Project charter](../project-charter.md)
- Roadmap: [Roadmap](../roadmap.md)
- Requirements: [Coastal location requirements](../requirements/coastal-locations.md)
- Requirements: [Fishing-condition requirements](../requirements/fishing-conditions.md)
- Related decision: [First-release user and fishing-context boundary](0001-first-release-user-and-fishing-context.md)
