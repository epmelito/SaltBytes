# Coastal location requirements

## Status

This document defines the approved geographic requirements for roadmap stage 3.
It does not select data providers, coordinates, storage schemas, or
implementation architecture.

Roadmap stage 3 remains in progress until its completion evidence is satisfied.

## Purpose

SaltBytes needs a representative and bounded set of North Carolina coastal
locations for comparing upcoming fishing windows.

The first release is intended for general recreational coastal anglers. It
covers surf fishing and fishing from publicly accessible fixed fishing piers.
Windows may be compared only with other windows in the same fishing context.

Shore-accessed inlet, vessel-based nearshore, offshore, and species-specific
uses remain deferred.

## Geographic modeling unit

The geographic modeling unit is a composite coastal location.

A composite coastal location represents a named fishing destination together
with the geographic and operational relationships needed to collect and
interpret environmental data for that destination. It is not limited to one
coordinate.

Each location must eventually document:

| Attribute | Requirement |
| --- | --- |
| Stable identity | A stable identifier and public-facing name |
| Fishing context | `surf` or `pier` for the first release |
| Region | Northern, central, or southern North Carolina coast |
| Display or destination coordinate | A representative coordinate used to identify and publish the destination |
| Weather request coordinate | The coordinate used for weather requests |
| Marine sampling coordinate | The offshore or water-grid coordinate used for marine conditions |
| Water-level relationship | The local tide or water-level reference applicable to the destination |
| Observation relationship | Any observation station used for validation or recent context |
| Forecast relationships | Applicable forecast, warning, and safety zones |
| Source-resolution limitations | Known limits in the spatial or temporal resolution of related sources |
| Spatial-representativeness limitations | Known differences between the destination and its request, sampling, station, or zone relationships |

The stable identity, public-facing name, fishing context, and representative
region are stage 3 requirements. Exact display or destination coordinates,
weather request coordinates, marine sampling coordinates, tide or water-level
references, observation relationships, and forecast or warning-zone mappings
may be resolved during stage 4 before source ingestion is implemented.

## Selection criteria

The first-release set should:

- represent the northern, central, and southern North Carolina coast
- use documented publicly accessible fishing locations
- include both approved fishing contexts
- include distinct coastal settings
- provide enough geographic spread to demonstrate the platform
- remain small enough for bounded source evaluation and implementation
- avoid implying exhaustive coverage of the North Carolina coast

## Initial location set

| Location | Region | Context | Inclusion rationale |
| --- | --- | --- | --- |
| Jennette’s Pier | Northern | Pier | An identifiable Atlantic fishing pier representing the northern Outer Banks |
| Beach Access Ramp 72, Ocracoke Island | Northern | Surf | A named National Park Service location at the southern end of Ocracoke Island representing an ocean-side surf context |
| Fort Macon State Park, ocean side | Central | Surf | An identifiable ocean-side fishing location representing the central coast |
| Bogue Inlet Pier | Central | Pier | An identifiable publicly accessible fixed fishing pier representing the central coast |
| Fort Fisher State Recreation Area | Southern | Surf | An identifiable ocean-side surf-fishing location representing the southern coast |

Bogue Inlet Pier is classified only as a pier for the first release. Its name
and proximity to Bogue Inlet do not introduce inlet-current requirements,
inlet scoring, or an inlet fishing context.

Beach Access Ramp 72 is classified only as surf. The first-release location
represents the ocean shoreline reached through the ramp, not Ocracoke Inlet or
the sound shoreline.

## Location evidence

### Jennette’s Pier

Direct evidence:

- The North Carolina Aquariums describes Jennette’s Pier as a 1,000-foot
  concrete fishing pier extending over the Atlantic Ocean.

Inference:

- It provides northern pier representation that is geographically separated
  from the central and southern locations.

Known limitations:

- Exact display, weather, marine, water-level, observation, and warning-zone
  relationships remain unresolved.

Sources:

- [Jennette’s Pier visit information](https://www.ncaquariums.com/visit-jennettes-pier),
  publication or update date not shown, accessed 2026-07-28

### Beach Access Ramp 72, Ocracoke Island

Direct evidence:

- The National Park Service identifies Beach Access Ramp 72 as the farthest
  south ramp in Cape Hatteras National Seashore.
- It is an NPS-managed named location providing access to the southern end of
  Ocracoke Island.
- Its availability can be affected by temporary NPS closures.

Inference:

- The ocean shoreline reached through Ramp 72 provides a distinct northern-coast
  surf location.
- Ramp 72 is preferred over Ramp 59 because product-owner direction favors the
  southern point and the reviewed evidence did not establish a material
  geographic or environmental-modeling advantage for Ramp 59.

Known limitations:

- Temporary NPS closures can affect whether the location is currently usable.
- This location must not be interpreted as an inlet or sound fishing context.
- Exact display, weather, marine, water-level, observation, and warning-zone
  relationships remain unresolved.

Sources:

- [NPS Beach Access Ramp 72](https://www.nps.gov/places/000/beach-access-ramp-72.htm),
  last updated 2021-11-07, accessed 2026-07-28
- [NPS Cape Hatteras alerts and beach-access conditions](https://www.nps.gov/caha/planyourvisit/conditions.htm),
  beach-access mileage last updated 2026-07-23, accessed 2026-07-28

### Fort Macon State Park, ocean side

Direct evidence:

- North Carolina State Parks lists fishing as an activity.
- The park provides both ocean and inlet beach access.

Inference:

- Restricting the first-release location to the ocean side provides central
  coastal surf representation without introducing an inlet context.

Known limitations:

- The park-level location does not identify an environmental sampling point.
- Exact display, weather, marine, water-level, observation, and warning-zone
  relationships remain unresolved.

Source:

- [Fort Macon State Park](https://www.ncparks.gov/state-parks/fort-macon-state-park),
  publication or update date not shown, accessed 2026-07-28

### Bogue Inlet Pier

Direct evidence:

- The facility operator identifies Bogue Inlet Pier as a publicly accessible
  fixed fishing pier in Emerald Isle.

Inference:

- The pier provides central-coast publicly accessible fixed fishing pier
  representation.

Known limitations:

- The location is classified as a pier only.
- No inlet-current requirement follows from the facility name.
- Exact display, weather, marine, water-level, observation, and warning-zone
  relationships remain unresolved.

Sources:

- [Bogue Inlet Pier](https://www.bogueinletpier.com/),
  publication or update date not shown, accessed 2026-07-28

### Fort Fisher State Recreation Area

Direct evidence:

- North Carolina State Parks identifies surf fishing, public ocean access, and
  an identifiable ocean-side location at Fort Fisher State Recreation Area.

Inference:

- Fort Fisher provides southern-coast surf representation and geographic
  separation from the Outer Banks and central Crystal Coast locations.

Known limitations:

- Temporary closures can affect whether the location is currently usable.
- Exact display, weather, marine, water-level, observation, and warning-zone
  relationships remain unresolved.

Sources:

- [Fort Fisher State Recreation Area](https://www.ncparks.gov/state-parks/fort-fisher-state-recreation-area),
  publication or update date not shown, accessed 2026-07-28

## Geographic coverage

The initial set provides:

- northern pier representation at Jennette’s Pier
- northern surf representation on Ocracoke Island
- central surf representation at Fort Macon
- central pier representation at Bogue Inlet Pier
- southern surf representation at Fort Fisher

The regional labels are project classifications for representative coverage.
They are not official North Carolina coastal-region designations.

## Comparison boundary

SaltBytes may compare upcoming windows only between locations with the same
fishing context:

- surf with surf
- pier with pier

The first release must not rank a surf window directly against a pier window.

The location identity and context must remain visible in modeled and published
data so that downstream consumers can preserve this boundary.

## Deferred geographic scope

The following remain deferred:

- shore-accessed inlet fishing
- vessel-based nearshore fishing
- offshore fishing
- species-specific location suitability
- additional North Carolina locations
- exhaustive statewide coverage
- inlet-current requirements
- navigation suitability
- implementation coordinates and source relationships listed as stage 4 work

## Evidence rules

Location evidence must:

- come from an authoritative public agency or the facility operator
- establish that the selected location is an identifiable, publicly accessible
  recreational fishing destination
- identify whether the statement is direct evidence or project inference
- include the source URL
- include a publication or update date when available
- include the access date
- record a brief closure caveat when dynamic closure status affects current use
- avoid fishing-success claims

## Related governance

- [Project charter](../project-charter.md)
- [Roadmap](../roadmap.md)
- [Scope register](../scope-register.md)
- [Fishing-condition requirements](fishing-conditions.md)
- [First-release user and fishing-context decision](../decisions/0001-first-release-user-and-fishing-context.md)
- [Composite geographic model and initial locations decision](../decisions/0002-composite-geographic-model-and-initial-locations.md)
