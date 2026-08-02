# Roadmap

## Current milestone

SaltBytes has completed hosted periodic ingestion, forecast history retention,
the fishing-factor registry, the first research-backed attributes, the static
HTML portfolio report site, and automated GitHub Pages publication. The committed
sample site remains a fixed reviewed snapshot.

Analysis-ready feature preparation is current. It should define deterministic
derived features and missing-data rules without introducing scoring weights or
unsupported fishing recommendations.

The interactive Observable dashboard is complete and hosted. `/dashboard/`,
`/conditions/`, and `/operations/` are published using curated static data.
The dashboard has passed browser runtime and live hosted verification.

## 1. Run hosted periodic ingestion

Run SaltBytes automatically without relying on a personal laptop.

Initial implementation:

- schedule ingestion every six hours with GitHub Actions
- support manual workflow execution
- prevent overlapping ingestion runs
- use Azure Blob Storage for durable DuckDB and raw-snapshot state
- download current state before execution
- upload updated state after execution
- keep secrets outside the repository
- preserve failed and partial runs for inspection

Do not add Container Apps, Functions, virtual machines, alerting systems,
complex retries, or enterprise orchestration in this milestone.

### Exit criteria

- scheduled and manual workflow runs both work
- state survives between hosted runners
- overlapping writers are prevented
- source failures remain visible
- the workflow does not depend on a local machine

## 2. Accumulate forecast history

Build a useful archive of forecast snapshots and revisions through repeated
hosted runs.

The archive should support analysis of:

- forecast vintages
- revisions for the same valid time
- source reliability
- location coverage
- run completeness
- partial and failed ingestion over time

This is forecast history, not historical observations.

### Exit criteria

- multiple forecast vintages are retained
- revisions can be compared by run, source, location, and forecast hour
- historical runs remain queryable
- storage growth is understood and manageable

## 3. Complete the fishing-factor registry

Consolidate species-agnostic coastal fishing research into:

`docs/research/fishing-factor-registry.md`

Classify each factor by:

- expected fishing value
- evidence strength
- species dependence
- public data availability
- source stability
- spatial and temporal resolution
- implementation effort
- scoring suitability
- current SaltBytes coverage

The registry should identify the strongest 2 to 3 near-term attribute additions.

Do not define scoring weights or unsupported thresholds.

### Exit criteria

- researched factors are classified consistently
- biological effects remain separate from fishability and safety
- public data feasibility is documented
- near-term candidates are justified
- deferred and species-specific factors remain recorded for later use

## 4. Add the first research-backed attributes

Add only the highest-value feasible attributes selected from the factor registry.

Use small, bounded implementation packages.

Each attribute addition must:

- have a clear analytical purpose
- use an appropriate public source
- preserve raw evidence and provenance
- include quality validation
- maintain source-level failure isolation
- integrate at the correct grain
- avoid unnecessary refactoring

The current leading candidates are:

- predicted water level, time to tide extrema, and predicted tidal range
- reviewed shoreline-orientation metadata
- wind-to-shore and wave-to-shore relationships derived from existing
  direction fields

These candidates remain subject to final registry review and implementation
scoping.

### Exit criteria

- selected attributes are ingested and stored reliably
- integrated conditions expose the new values where appropriate
- missing data remains distinguishable from bad conditions
- each addition is documented and tested

## 5. Build and publish the first portfolio report

Status: Complete.

SaltBytes generates separate self contained HTML reports from stored DuckDB
data. The coastal conditions report presents current conditions and forecast
trends. The pipeline operations report presents revisions, source completeness,
pipeline history, provenance, freshness, and limitations.

After successful ingestion and canonical state publication, the hosted workflow
generates a landing page plus `site/conditions/index.html` and
`site/operations/index.html`, uploads only the generated site, and deploys it
through GitHub Pages. Failed ingestion or report publication leaves the
previously published site available. The site follows the six hour ingestion
cadence and is not real time. This publication path has been verified from
`main`.

The committed `docs/sample-report/` site remains the fixed reviewed portfolio
snapshot.

Do not present fishing scores, catch predictions, or optimal fishing windows
before the research and scoring work support those claims.

### Exit criteria

- both reports can be regenerated from stored SaltBytes data
- the public conditions report uses the latest successful run
- the operations report uses retained hosted history and provenance
- freshness and limitations are visible in both report contexts
- failed ingestion or publication does not replace the previous site

## 6. Prepare the analysis-ready feature layer

After hosted ingestion, research consolidation, and initial attribute expansion,
define the derived features needed for later deterministic scoring.

Potential work includes:

- pressure trends
- time relative to tide changes
- daylight categories
- rolling or lagged weather context
- completeness indicators
- scoring eligibility
- separation of biological conditions, fishability, and safety

Do not create scoring weights in this milestone.

### Exit criteria

- feature definitions are documented
- derived features are deterministic and reproducible
- missing-data rules are explicit
- the hourly grain remains suitable for later scoring
- scoring readiness can be evaluated honestly

## Immediate sequence

Completed:

Hosted periodic ingestion
→ fishing-factor registry
→ tidal-state completion
→ site-orientation metadata
→ wind and wave directional interactions
→ static portfolio report site
→ automated report publication verification

→ interactive Observable dashboard

Current:

Analysis-ready feature preparation
