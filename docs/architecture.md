# Architecture

## Purpose

This document describes the current local atmospheric forecast implementation.
The [project charter](project-charter.md) defines the broader approved North
Carolina coastal fishing conditions platform.

## High-level flow

1. Load a local environment configuration.
2. Initialize DuckDB and start a pipeline run.
3. Request an Open-Meteo `ncep_nbm_conus` forecast for each location's weather
   request coordinate.
4. Validate and persist the complete location result.
5. Skip raw and normalized storage when that result fails quality checks.
6. Continue processing unrelated locations after a quality rejection.
7. Write a passing response unchanged to immutable raw storage.
8. Store snapshot provenance and 168 normalized UTC hourly rows.
9. Complete the run after every location or abort on an operational failure.
10. Compare consecutive forecasts through the revision view.

API, raw-storage, and database failures abort immediately. Quality rejection is
location-specific, but any rejected location makes the final run status
`failed`. Successfully stored unrelated locations are not rolled back.

## Configuration

All three environments configure the five approved locations and distinguish:

- display coordinate
- weather request coordinate
- expected returned NBM coordinate
- fishing context
- static coastal regime

The atmospheric API contract is:

- `models=ncep_nbm_conus`
- `forecast_days=7`
- `timezone=auto`
- the five accepted hourly fields

Configuration validation rejects other selectors, horizons, fields, incomplete
spatial relationships, invalid coordinates, unsupported fishing contexts, and
empty coastal regimes.

## Ingestion and raw storage

One Open-Meteo response is treated as one complete location result. Quality
checks run before storage. Passing responses are preserved unmodified as
immutable JSON. Failed responses produce quality evidence but no raw snapshot
or normalized rows.

The pipeline retains the configured model and request coordinate as request
provenance. Returned coordinates, response timezone, and UTC offset remain
attributable to the captured response.

## Normalization

The response timezone is used to convert local hourly labels to UTC. Passing
results contain exactly 168 unique, strictly ascending hourly UTC instants.
DuckDB stores the five accepted atmospheric values for each instant.

## Revision history

`forecast_revision_changes` partitions rows by stable location ID and
normalized valid time, then orders snapshots by capture time and snapshot ID.
It compares consecutive wind speed, wind direction, wind gust, precipitation
probability, and precipitation forecasts.

Wind direction exposes current and previous values only. No circular or signed
directional difference is defined.

## Environments

`dev`, `test`, and `prod` run the same application and seven-day atmospheric
contract using separate local storage paths. Automated tests replace live
forecast fetching with deterministic responses and temporary storage.

These names do not represent deployed cloud environments.

## Current boundary

Marine, sea-surface-temperature, tide, scoring, scheduling, publication, and
cloud infrastructure are outside the current implementation.
