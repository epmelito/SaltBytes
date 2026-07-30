# Roadmap

## MVP milestone

The MVP is complete when another person can install the project, run the
pipeline for the five configured locations, inspect one integrated hourly
coastal-conditions result, and reproduce one readable local output.

Missing or rejected source data must remain visible, and repository validation
must pass.

## 1. Validate live ingestion

Run:

```powershell
forecast-ops
```

Confirm that atmospheric, wave, sea-surface-temperature, and tide processing
produce usable normalized data for the configured locations.

Fix only observed problems that block execution, produce incorrect or unusable
data, hide source failures, break required source isolation, or risk
destructive persistence.

## 2. Build the integrated hourly result

Create the downstream DuckDB view `coastal_conditions_hourly` using the existing
normalized tables.

It should:

- use exact run, stable location identity, and UTC forecast-hour keys
- include values from the four existing source families
- retain source status and snapshot provenance while unavailable values remain null
- remain deterministic and inspectable

Do not add scoring, ranking, recommendations, interpolation, carry-forward, or
source substitution.

## 3. Expose one readable local output

Present the integrated result through the smallest useful local interface, such
as a CLI table, text report, or generated HTML report.

Choose based on implementation cost and readability. Public hosting, APIs,
authentication, dashboards, and cloud infrastructure are not part of this
milestone.

## 4. Stabilize the MVP

- add or update only tests needed to protect the new behavior
- document the supported run and output commands
- remove temporary debugging artifacts
- run the full tests and Ruff once
- confirm a clean local setup can reproduce the result

After this checkpoint, choose the next milestone from demonstrated needs rather
than speculative future requirements.
