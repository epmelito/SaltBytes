# Analysis-ready feature contract

## Decision

The first analysis-ready feature work will add recent precipitation
accumulation, source completeness or availability indicators, and technical
eligibility for later deterministic calculations. This is the smallest
coherent set available from current stored data without a new provider or a
location-provenance precursor.

The contract defines feature meaning and boundaries. It does not define a
storage layout, query, score, weight, favorable threshold, ranking,
recommendation, or species-specific rule.

## Layer boundary

The source grain remains `run_id`, `location_id`, and UTC `forecast_time`.
Derived features must preserve that grain and the run and source provenance of
their inputs.

Features must not interpolate, carry values forward, substitute sources, or mix
runs. A feature value remains separate from whether its source was available
and from any confidence or eligibility statement about the row.

## Current state

The integrated hourly model already exposes:

- hourly precipitation and source status and snapshot provenance
- tide phase, minutes since and until adjacent extrema, and predicted tidal
  range
- wind and wave angles relative to the persisted shore normal

These implemented tide and site-relative fields are inputs available for later
analysis; they are not future feature work under this contract.

Barometric pressure and pressure trend are not stored and remain excluded from
the species-agnostic model. The fishing-factor evidence does not support using
them as general bite modifiers.

Solar timing or daylight state is supported as future context, but historical
derivation is not yet reproducible. The configured display coordinate and
display timezone are not persisted with each run location, so immutable
location and timezone provenance must be established first.

## First implementation-ready set

### Recent precipitation accumulation

Recent precipitation accumulation may describe environmental context, such as
recent rainfall that could contribute to runoff where a defensible local
relationship is later established. It must not imply that rainfall is
universally favorable or unfavorable for fishing.

The implementation must choose and document explicit trailing windows and the
behavior of incomplete windows. Each accumulation must use precipitation from
the same run and source provenance as the target hourly row.

### Source completeness and availability

Completeness indicators describe data confidence, not environmental quality.
They must distinguish at least:

- successful source with all required values
- successful source with unavailable derived context
- failed or unavailable source
- incomplete historical window
- not applicable when a future context-specific feature does not apply

A missing value must remain distinguishable from a recorded source failure,
unavailable derived context, an incomplete window, and a not-applicable state.
None of these states means bad fishing conditions.

### Technical eligibility

Technical eligibility means only that the required inputs for a future
deterministic calculation are present and valid at the target grain. It does
not mean good fishing, safe conditions, or a positive score.

Eligibility must be derived from explicit input requirements and the associated
availability states. It must not replace source provenance or collapse missing,
failed, unavailable, incomplete, and not-applicable states into fishing
quality.

## Deferred precursor

Solar timing or daylight category remains a supported future candidate after
immutable display-coordinate and timezone provenance is available for each run
location. This contract does not decide the eventual persistence schema.

## Interpretation boundaries

Features must retain their supported role:

- environmental or biological context describes conditions that may matter to
  habitat or fishing context without assigning universal direction
- practical fishability describes conditions affecting access, casting, line
  control, or exposure without asserting catch quality
- data confidence or eligibility describes whether evidence is available and
  technically usable
- safety information communicates hazards independently of fishing quality

Safety information must remain separate and must not be converted into fishing
quality. Missing, failed, unavailable, incomplete, or ineligible data must not
be interpreted as unfavorable conditions.
