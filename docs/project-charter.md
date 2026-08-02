# Project charter

## Purpose

SaltBytes is a lightweight portfolio project for exploring upcoming coastal
conditions at a small set of North Carolina fishing locations.

The current objective is to operate a small hosted data pipeline and public
static report, then prepare deterministic analysis-ready features without
introducing unsupported scoring or recommendations.

## Product direction

SaltBytes should:

- collect a focused set of coastal environmental data
- combine it into a deterministic and inspectable result
- make missing or rejected source data visible
- demonstrate practical ingestion, validation, persistence, and modeling
- remain simple enough to maintain

The project should preserve the smallest hosted architecture that keeps data,
failures, provenance, and publication behavior inspectable.

## Boundaries

SaltBytes does not:

- guarantee fishing success
- provide catch probabilities
- replace official marine or safety guidance
- provide navigation or emergency information
- use opaque AI-generated fishing recommendations
- claim production readiness

The current platform includes local execution, scheduled hosted ingestion,
durable cloud state, and static report publication. Scoring, ranking,
recommendations, additional coverage, APIs, authentication, and production
operations remain later decisions.

## Principles

- Prefer a simple working result over speculative refinement.
- Preserve deterministic, traceable behavior.
- Address real defects and immediate risks.
- Defer architecture that the current milestone does not require.
- Use AI to accelerate reviewed work, not to invent requirements or process.