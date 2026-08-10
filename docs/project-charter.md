# Project charter

## Purpose

SaltBytes is a lightweight portfolio project for exploring upcoming coastal
conditions at North Carolina fishing locations.

The [project roadmap](project-roadmap.md) explains the long range direction.
The [current roadmap](roadmap.md) lists the next few pieces of work.

## Product direction

SaltBytes should:

- collect a focused set of coastal environmental data
- combine it into deterministic and inspectable data products
- provide location-first, species-aware fishing assessments from reusable
  species knowledge, recent observations, and forecast and site conditions
- keep assessment confidence and evidence scope separate from the assessment
- identify positive, limiting, and unknown factors behind each assessment
- use an explainable numeric species method only when a separately approved
  methodology supports it
- preserve missing or rejected source data instead of hiding uncertainty
- keep factual observations, source advice, forecasts, and environmental
  observations for forecast verification distinct
- consider a future general fishing-conditions or fishability score only after
  the evidence foundation matures
- demonstrate practical ingestion, validation, persistence, modeling, and
  reporting
- present reports, dashboards, metrics, explanations, and warnings in clear,
  natural language for recreational anglers and other general users
- remain simple enough to maintain

A location-first species assessment explains which species may be realistic
targets in the available context, when the evidence supports that interpretation,
and why. It is not a prediction of catch or fish presence. Recent observations
can strengthen an assessment, but cannot be its only basis.

The project should preserve the smallest hosted architecture that keeps data,
failures, provenance, scoring methodology, and publication behavior
inspectable.

## Boundaries

SaltBytes does not:

- guarantee fishing success
- provide catch or bite probabilities
- claim fish are present because conditions are favorable
- replace official marine or safety guidance
- provide navigation or emergency information
- use opaque AI-generated fishing recommendations
- replace missing local biology with unsupported proxies
- claim production readiness

## Principles

- Prefer a simple working result over speculative refinement.
- Preserve deterministic, traceable behavior.
- Make assessment assumptions, material contributions, and uncertainty visible.
- Keep internal research technically precise, but translate user-facing output
  into familiar everyday language without weakening accuracy, limitations, or
  safety meaning.
- Address real defects and immediate risks.
- Defer architecture that current approved work does not require.
- Use AI to accelerate reviewed work, not to invent requirements or process.
