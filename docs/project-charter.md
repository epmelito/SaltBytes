# Project charter

## Purpose

SaltBytes is a lightweight portfolio project for exploring upcoming coastal
conditions at a small set of North Carolina fishing locations.

The [project roadmap](project-roadmap.md) explains the long range direction.
The [current roadmap](roadmap.md) lists the next few pieces of work.

## Product direction

SaltBytes should:

- collect a focused set of coastal environmental data
- combine it into deterministic and inspectable data products
- produce explainable 0 to 100 species conditions scores
- keep score confidence separate from the score itself
- identify positive, limiting, and unknown factors behind each score
- preserve missing or rejected source data instead of hiding uncertainty
- develop a future overall fishing conditions score after multiple species
  models exist
- demonstrate practical ingestion, validation, persistence, modeling, and
  reporting
- present reports, dashboards, metrics, explanations, and warnings in clear,
  natural language for recreational anglers and other general users
- remain simple enough to maintain

A species conditions score represents how favorable the available location,
seasonal, habitat, environmental, and practical fishability conditions are for
targeting a species according to approved research. It is a conditions
alignment index, not a prediction of catch or fish presence.

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
- Make scoring assumptions, material contributions, and uncertainty visible.
- Keep internal research technically precise, but translate user-facing output
  into familiar everyday language without weakening accuracy, limitations, or
  safety meaning.
- Address real defects and immediate risks.
- Defer architecture that current approved work does not require.
- Use AI to accelerate reviewed work, not to invent requirements or process.
