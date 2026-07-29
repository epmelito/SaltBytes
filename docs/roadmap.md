# Roadmap

## Purpose

This roadmap defines the shortest approved path from the current repository
state to a working ForecastOps proof of concept.

The long-term product direction remains documented in the project charter.
This file controls near-term delivery order only.

## Current state

ForecastOps already implements local ingestion for:

- atmospheric conditions
- wave conditions
- sea-surface temperature
- NOAA tide predictions and tide phase

The pipeline supports five approved North Carolina coastal locations and
preserves normalized data, quality results, provenance, run metadata, immutable
passing raw snapshots, and revision history.

The ingestion foundation is complete enough to begin proof-of-concept work.

## Proof-of-concept sequence

### 1. Validate the existing pipeline live

Run the complete four-source pipeline for all five configured locations.

Fix only defects that:

- prevent reliable execution
- produce incorrect data
- prevent source failures from remaining isolated
- make the resulting data unusable

Do not add new providers, locations, fallback logic, or generalized
infrastructure during this stage.

### 2. Build one integrated coastal-conditions dataset

Create the smallest useful integrated result from the existing atmospheric,
wave, sea-surface-temperature, and tide data.

The result should:

- retain location and fishing-context identity
- align source values to a common forecast time
- preserve source and quality context
- avoid unsupported scoring or ranking
- remain inspectable and deterministic

Do not build a generalized semantic layer or broad modeling framework.

### 3. Expose one usable output

Present the integrated result through the simplest useful interface.

Acceptable proof-of-concept outputs include:

- a CLI report
- a generated HTML report
- a small local application

Choose the simplest option that demonstrates the data clearly.

Do not add cloud deployment, authentication, a public API, or production service
architecture at this stage.

### 4. Confirm proof-of-concept viability

The proof of concept is complete when:

- the existing pipeline runs successfully for the five configured locations
- the four source families are represented in one integrated result
- source or quality failures remain visible
- a user can inspect upcoming coastal conditions in a usable output
- repository validation passes

## Deferred until after the proof of concept

Defer:

- additional data sources
- additional locations
- deterministic scoring and ranking
- species-specific recommendations
- observation and bias validation
- source fallback and precedence
- scheduling changes
- retention policy design
- Azure infrastructure
- public deployment
- API design
- authentication
- production monitoring and service levels
- generalized platform abstractions
- further agent or skill development

## Later direction

After the proof of concept works, evaluate the next step based on demonstrated
value.

Possible later work includes:

- deterministic and explainable scoring
- fishing-window ranking
- consumer-ready datasets
- scheduled execution
- Azure deployment
- a public portfolio display
- broader coastal coverage

Do not begin later work until the proof of concept is complete and reviewed.