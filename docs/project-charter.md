# Project charter

## Status

This charter records the approved product direction for ForecastOps. It
describes durable intent, not detailed architecture or current implementation
claims.

## Product purpose

ForecastOps is evolving into a North Carolina coastal fishing conditions data
platform. It should help identify and compare upcoming coastal fishing windows
using explainable environmental data.

The platform is intended first as a portfolio data engineering platform, not as
a commercial fishing product. It should demonstrate practical platform
engineering, orchestration, data modeling, data quality, publication, and
AI-assisted engineering workflows.

## Current foundation

The repository currently contains a local, configuration-driven weather
forecast snapshot pipeline using Open-Meteo, immutable raw JSON storage,
DuckDB, quality checks, run metadata, structured logging, automated tests,
GitHub Actions, and a bounded forecast failure review skill.

This implementation is the technical foundation. It is not yet a fishing
conditions platform. The current `dev`, `test`, and `prod` environments are
local configurations rather than deployed cloud environments.

## Approved long-term capabilities

The platform should eventually:

- collect weather, marine, tide, and related coastal condition data
- cover a representative set of North Carolina coastal fishing locations
- retain source data and forecast history
- model how forecasts and recommendations change over time
- calculate deterministic and explainable fishing condition scores
- rank upcoming fishing windows
- publish consumer-ready datasets
- run on a reusable personal Azure data platform
- expose a public portfolio display
- demonstrate bounded AI-assisted planning, implementation, review,
  diagnostics, and handoff

These capabilities describe approved direction, not current behavior or a
detailed implementation commitment.

## Architecture principles

Future work should favor:

- the simplest evidence-based design that fully satisfies confirmed
  requirements without weakening integrity, validation, or reliable operation
- reusable ingestion and orchestration patterns
- environment-aware configuration
- immutable raw data
- normalized and curated data layers
- traceable forecast revisions
- deterministic transformations
- explainable scores
- automated quality checks
- observable pipeline runs
- consumer-ready published datasets
- infrastructure that can support later portfolio projects

Azure is the approved future cloud direction. Exact services and deployment
architecture remain undecided.

## Product boundaries

ForecastOps is not intended to:

- guarantee fishing success
- replace marine safety guidance or official forecasts
- use opaque AI-generated fishing scores
- begin as a real-time commercial service
- support every North Carolina fishing location in its first release
- implement every possible weather, marine, tide, biological, or fishing
  variable
- begin product feature implementation before the governance package has been
  reviewed, validated, merged into `main`, and its linked GitHub issue has been
  closed

## AI-assisted engineering

AI assistance should be bounded, reviewable, and evidence-based. It may support
planning, implementation, review, diagnostics, and handoff. It must not turn
unsupported assumptions into product requirements, obscure deterministic
scoring logic, or bypass scope and decision controls.

AI-assisted engineering is distinct from adding AI-generated product outputs.
AI-generated product outputs require explicit future scope approval and defined
evidence and review boundaries.

## Product progress

Progress is measured against the approved roadmap stages and their completion
evidence. Final product success metrics remain deferred.

## Deferred decisions

Specific product, source, scoring, publication, scheduling, cloud architecture,
retention, service-level, cost, and success-metric choices remain open. They are
tracked in the [scope register](scope-register.md) and should be resolved
through the [decision process](decisions/README.md) when required.

## Related governance

- [Roadmap](roadmap.md) sequences delivery outcomes.
- [Scope register](scope-register.md) controls current and deferred scope.
- [Decision process](decisions/README.md) governs durable choices.
- [Agent guidance](../AGENTS.md) governs repository working behavior.
- [Current handoff](handoffs/current.md) reports transient work state.
