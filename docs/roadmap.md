# Current roadmap

This roadmap owns the current SaltBytes delivery sequence and the next few
pieces of work. See the [project roadmap](project-roadmap.md) for the larger
project direction and completed phases.

## Current position

SaltBytes has completed its coastal data foundation, hosted publishing,
research backed fishing context, and the first published species conditions
score.

Spanish mackerel results are calculated when dashboard data is exported and are
published through the dashboard. They are not stored in the database. SaltBytes
does not provide catch probability, ranked fishing windows, or an overall
fishing conditions score.

The reporting phase is complete. The public landing page and the desktop
Conditions and Operations views are organized for their different audiences and
ready for ordinary use and investigation.

## Next work

### 1. Complete the location foundation

The source-independent fishing observation contract and the initial observation
ingestion and hosted observation feedback loop are established. Sunset Beach
Pier is implemented as SaltBytes location 6 across environmental ingestion,
Spanish mackerel applicability, observations, hosted operation, and reporting.

Little Bridge Sound Access is the approved seventh SaltBytes location and first
`sound-side` location. Its bounded environmental and source evaluation is
complete in [Decision 0014](decisions/0014-little-bridge-seventh-location-contract.md).
Implementation of location 7 is the next location-foundation work.
Resume species-assessment implementation after the location foundation is
complete.

The deterministic red drum score path is paused; its research remains useful
for later location-first assessment work.

## Later work

Fishing opportunity comparisons and a general fishing-conditions or fishability
score remain later work. Their methods will not be selected until the evidence
foundation matures.

Forecast Sources spatial presentation remains deferred outside the active work
sequence.

Hosted telemetry, replay and backfill, environmental observation ingestion,
forecast verification, storage evolution, and compute evolution remain possible
or conditional work where their original need applies. They do not displace the
observational and location foundation above.
