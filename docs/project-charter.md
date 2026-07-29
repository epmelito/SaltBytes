# Project charter

## Purpose

ForecastOps is a lightweight portfolio project for exploring upcoming coastal
conditions at a small set of North Carolina fishing locations.

The immediate objective is to prove the idea end to end with a system that can
be run locally, understood from the repository, and extended later if the MVP
demonstrates value.

## Product direction

ForecastOps should:

- collect a focused set of coastal environmental data
- combine it into a deterministic and inspectable result
- make missing or rejected source data visible
- demonstrate practical ingestion, validation, persistence, and modeling
- remain simple enough to maintain

The project should reach a working local MVP before pursuing production
architecture or broad feature coverage.

## Boundaries

ForecastOps does not:

- guarantee fishing success
- provide catch probabilities
- replace official marine or safety guidance
- provide navigation or emergency information
- use opaque AI-generated fishing recommendations
- claim production readiness

The first MVP presents environmental conditions. Scoring, ranking,
recommendations, additional coverage, scheduling, cloud deployment, APIs,
authentication, and production operations are later decisions.

## Principles

- Prefer a simple working result over speculative refinement.
- Preserve deterministic, traceable behavior.
- Address real defects and immediate risks.
- Defer architecture that the current milestone does not require.
- Use AI to accelerate reviewed work, not to invent requirements or process.