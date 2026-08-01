# Site orientation review

## Purpose

This document records the manual orientation review for the five SaltBytes
locations.

The metadata provides a stable local reference frame for later deterministic
wind and wave direction transformations. It does not classify conditions,
estimate nearshore refraction, or assign fishing value.

## Convention

Azimuths use degrees clockwise from true north.

`shore_normal_azimuth_degrees` points from the reviewed shoreline segment
toward open Atlantic water.

`pier_seaward_azimuth_degrees` follows the pier axis from land toward its
seaward end. It is null for surf locations.

Values are rounded to the nearest 5 degrees. They are reviewed analytical
metadata, not survey measurements.

## Review method and source

Each location was reviewed from north up Google Maps satellite imagery supplied
by the project owner on 2026-08-01.

The local shoreline tangent was estimated across the beach segment surrounding
the configured display coordinate. The tangent was rotated 90 degrees toward
open water to obtain the shore normal. Pier alignments were reviewed separately
from the visible landfall to the seaward end.

The screenshots were used as review evidence but are not committed because they
contain third party map imagery.

## Jennette's Pier

- Configured coordinate: `35.9096355, -75.5966537`
- Selected segment: Atlantic shoreline immediately north and south of the pier
- Shore normal: `75`
- Pier seaward azimuth: `70`
- Review confidence: moderate
- Limitation: The shoreline is mildly curved. The pier axis points slightly
  north of the local shore normal, and the landward pier section is partly
  obscured by the map marker.

## Beach Access Ramp 72, Ocracoke Island

- Configured coordinate: `35.0868922, -75.9844152`
- Selected segment: Oceanfront beach surrounding Ramp 72
- Shore normal: `135`
- Pier seaward azimuth: null
- Review confidence: high
- Limitation: The value applies to the reviewed oceanfront segment, not the
  migrating inlet spit, Ocracoke Inlet, or nearby channel margins.

## Fort Macon State Park, ocean side

- Configured coordinate: `34.6949437, -76.697391`
- Selected segment: Ocean beach west of the Beaufort Inlet shoreline bend
- Shore normal: `185`
- Pier seaward azimuth: null
- Review confidence: high
- Limitation: The shoreline turns toward Beaufort Inlet east of the configured
  point. This value does not represent the inlet edge.

## Bogue Inlet Pier

- Configured coordinate: `34.6601236, -77.0337424`
- Selected segment: Ocean beach immediately surrounding the pier
- Shore normal: `165`
- Pier seaward azimuth: `175`
- Review confidence: moderate
- Limitation: The pier axis is more southerly than the local shore normal.
  Neither value represents Bogue Inlet or nearby channel geometry.

## Fort Fisher State Recreation Area

- Configured coordinate: `33.9534, -77.929`
- Selected segment: Atlantic beach surrounding the configured point
- Shore normal: `105`
- Pier seaward azimuth: null
- Review confidence: moderate
- Limitation: The Atlantic shoreline curves through the recreation area. This
  value does not represent the Cape Fear River, The Basin, or more sharply
  curved shoreline farther north or south.

## Use boundary

These values support deterministic conversion of existing compass directions
into site relative angles and components.

They do not model:

- wave refraction or breaking
- bathymetry or bars
- dunes, buildings, or vegetation shelter
- inlet currents
- shoreline change after the review date
- safety, fishability, or fishing quality
