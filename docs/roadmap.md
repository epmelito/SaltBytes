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

### 1. Evaluate Spanish mackerel applicability at Little Bridge

The planned observation and location foundation is complete. Little Bridge Sound
Access is SaltBytes location 7 and the first `sound-side` location, with its
bounded environmental and location relationships implemented.

GitHub issue [#189](https://github.com/epmelito/SaltBytes/issues/189),
`Evaluate Spanish mackerel applicability at Little Bridge`, is the immediate
next approved work. It is an evidence and methodology decision package; it does
not authorize adding Little Bridge to Spanish mackerel scoring.

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
#189 decision package above.
