# Environments

ForecastOps uses `dev`, `test`, and `prod` as local environment configurations.
They do not represent deployed cloud environments.

## Shared atmospheric contract

Every environment configures:

- the five approved North Carolina coastal locations
- Open-Meteo model `ncep_nbm_conus`
- seven forecast days
- `timezone=auto` request behavior
- the same five atmospheric fields
- display, weather-request, and expected returned weather coordinates
- fishing context and static coastal regime

The locations are:

- Jennette's Pier
- Beach Access Ramp 72, Ocracoke Island
- Fort Macon State Park, ocean side
- Bogue Inlet Pier
- Fort Fisher State Recreation Area

## Environment differences

| Environment | Storage | Logging | Purpose |
| --- | --- | --- | --- |
| `dev` | Local development raw and DuckDB paths | `DEBUG` | Development and manual validation |
| `test` | Local test paths | `INFO` | Test configuration |
| `prod` | Separate local production-style paths | `INFO` | Local production-style execution |

The same application and transformation behavior run in each environment.

Automated tests do not depend on the live endpoint in `config/test.yml`. They
replace forecast fetching with deterministic responses and use temporary
storage through the test harness.

## Promotion flow

1. Create one focused feature branch.
2. implement and validate the authorized change.
3. Open a pull request.
4. Run automated checks.
5. Merge reviewed changes into `main`.
6. Run production-style local workflows from the tested version when
   authorized.

The repository does not maintain separate long-lived environment branches.

## Configuration boundary

Configuration supplies source, field, location, spatial-relationship, storage,
and logging values. It does not select alternate implementations, fallbacks,
quality thresholds, marine or tide sources, scheduling, or cloud deployment.
