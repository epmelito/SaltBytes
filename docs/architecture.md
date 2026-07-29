# Architecture

## Purpose

This document describes the current local atmospheric, wave, and
sea-surface-temperature forecast implementation.
The [project charter](project-charter.md) defines the broader approved North
Carolina coastal fishing conditions platform.

## High-level flow

1. Load a local environment configuration.
2. Initialize DuckDB and start a pipeline run.
3. Request independent Open-Meteo `ncep_nbm_conus` atmospheric,
   `meteofrance_wave` wave, and `meteofrance_currents` SST results using their
   source-specific coordinates.
4. Validate and persist each complete source result independently.
5. Skip raw and normalized storage for a rejected source result.
6. Continue with the other sources and unrelated locations after a quality
   rejection.
7. Write each passing response unchanged to a separate immutable raw snapshot.
8. Store source-specific snapshot provenance and 168 normalized UTC hourly
   rows in the corresponding atmospheric, wave, or SST table.
9. Complete the run after every location or abort on an operational failure.
10. Compare consecutive forecasts through separate atmospheric, wave, and SST
    revision views.

API, raw-storage, and database failures abort immediately. Any rejected source
result makes the final run status `failed`, while successfully stored results
from other sources or unrelated locations are retained.

## Configuration

All three environments configure the five approved locations and distinguish:

- display coordinate
- weather request coordinate
- expected returned NBM coordinate
- `meteofrance_wave` request coordinate
- expected returned `meteofrance_wave` coordinate
- `meteofrance_currents` SST request coordinate
- expected returned `meteofrance_currents` SST coordinate
- fishing context
- static coastal regime

The atmospheric API contract is:

- `models=ncep_nbm_conus`
- `forecast_days=7`
- `timezone=auto`
- the five accepted hourly fields

The wave API contract is:

- `models=meteofrance_wave`
- `forecast_days=7`
- `timezone=auto`
- `wave_height`, `wave_direction`, and `wave_period`

The SST API contract is:

- `models=meteofrance_currents`
- `forecast_days=7`
- `timezone=auto`
- `sea_surface_temperature` only

Configuration validation rejects other selectors, horizons, fields, incomplete
atmospheric or wave relationships, invalid display, atmospheric, or wave
coordinates, unsupported fishing contexts, and empty weather coastal regimes.
SST relationship, coordinate, and coastal-regime prerequisites are checked as
source-qualified results before an SST request.

## Ingestion and raw storage

Each Open-Meteo response is treated as one complete, independent source result.
Source-qualified quality checks run before storage. Passing responses are
preserved unmodified as separate immutable JSON snapshots. Failed results
produce quality evidence but no raw snapshot or normalized rows for that
source.

The pipeline retains each configured model and source-specific request
coordinate as request provenance. Returned coordinates, response timezone, and
UTC offset remain attributable to the corresponding captured response.

## Normalization

The response timezone is used to convert local hourly labels to UTC. Passing
results contain exactly 168 unique, strictly ascending hourly UTC instants.
DuckDB stores the five accepted atmospheric values in `forecast_hourly`, the
three accepted wave values in `wave_hourly`, and sea-surface temperature in
`sst_hourly`.

## Revision history

`forecast_revision_changes` partitions rows by stable location ID and
normalized valid time, then orders snapshots by capture time and snapshot ID.
It compares consecutive wind speed, wind direction, wind gust, precipitation
probability, and precipitation forecasts.

Wind direction exposes current and previous values only. No circular or signed
directional difference is defined.

`wave_revision_changes` applies the same stable-location and normalized-time
matching to `meteofrance_wave` snapshots. Wave height and period include
differences; wave direction exposes current and previous values only.

`sst_revision_changes` applies the same matching to
`meteofrance_currents` snapshots and exposes current, previous, and scalar
sea-surface-temperature changes.

## Environments

`dev`, `test`, and `prod` run the same application and seven-day atmospheric,
wave, and SST contracts using separate local storage paths. Automated tests
replace live source fetching with deterministic responses and temporary
storage.

These names do not represent deployed cloud environments.

## Current boundary

Ocean-current, sea-level-height, tide, scoring, scheduling, publication,
agents, and cloud infrastructure are outside the current implementation.
