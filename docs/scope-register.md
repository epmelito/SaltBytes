# Scope register

## Purpose

This file defines the current proof-of-concept boundary.

It separates:

- current capability
- active proof-of-concept work
- deferred work
- excluded work

Detailed implementation history remains in GitHub issues, pull requests, code,
tests, and accepted decision records.

## Current capability

ForecastOps currently provides a local Python pipeline for five approved North
Carolina coastal locations.

Implemented source families:

- atmospheric conditions from Open-Meteo
- wave conditions from Open-Meteo
- sea-surface temperature from Open-Meteo
- NOAA tide predictions and binary tide phase

Implemented platform behavior includes:

- configuration-driven execution
- independent source processing and rejection
- immutable passing raw snapshots
- normalized UTC data
- request, response, source, run, and quality metadata
- provenance and stable location relationships
- forecast and tide-phase revision history
- structured logging
- automated tests and GitHub Actions validation

The current `dev`, `test`, and `prod` configurations are local environments, not
deployed cloud environments.

## Active proof-of-concept scope

The active scope is limited to:

1. Live validation of the existing four-source pipeline across all five
   configured locations.
2. Corrections required for reliable execution or correct usable data.
3. One integrated coastal-conditions dataset using the existing normalized
   atmospheric, wave, sea-surface-temperature, and tide data.
4. One simple usable output for inspecting upcoming coastal conditions.

The integrated result must:

- preserve location and fishing-context identity
- align existing source values to a common forecast time
- preserve visible source and quality context
- remain deterministic and inspectable
- avoid unsupported scoring or recommendations

The proof of concept is complete when the existing pipeline runs, all four
source families appear in one usable integrated result, failures remain visible,
and repository validation passes.

## Deferred scope

Defer until after the proof of concept:

- additional providers or source families
- additional locations
- observed water levels
- tidal-current predictions
- warning and forecast-zone products
- source accuracy and bias validation
- fallback and precedence rules
- alternative marine models
- marine run-history reconstruction
- scoring formulas, thresholds, and weights
- fishing-window ranking
- species-specific recommendations
- scheduling changes
- retention policy design
- publication contracts
- API design
- dashboard architecture
- authentication
- Azure services and deployment
- infrastructure as code
- production monitoring and service levels
- cost and final success metrics
- additional agents or skills
- generalized platform frameworks

Accepted decisions remain valid where they govern implemented behavior, but
deferred topics should not be resolved merely to future-proof the proof of
concept.

## Excluded scope

The proof of concept does not:

- guarantee fishing success
- provide predicted catch probabilities
- replace official marine or beach-safety guidance
- provide navigation guidance
- use opaque AI-generated fishing scores
- provide species recommendations
- compare surf and pier windows as equivalent fishing contexts
- operate as a real-time commercial service

## Scope control

For proof-of-concept work:

- implement only the smallest change required by the active task
- do not add unrelated improvements
- do not resolve deferred decisions unless they block the proof of concept
- use an ADR only when a durable unresolved choice must be made
- update this file only when the active, deferred, or excluded boundary changes

Current implementation details should be verified from code, configuration, and
tests rather than repeated here.