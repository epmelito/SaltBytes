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
Pier is approved for implementation as SaltBytes location 6 with a documented
implementation contract; it is not yet implemented. Issue #182 is the next
Sunset implementation package.

Sound-side expansion is approved, with Little Bridge Sound Access as the planned
seventh SaltBytes location. Its environmental source relationships remain
unresolved and require bounded evaluation before implementation; existing
ocean-facing marine relationships must not be reused without supporting
evidence. Resume species-assessment implementation after the location
foundation is complete.

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
