# Analysis-ready feature contract

## Decision

Analysis-ready features provide recent precipitation accumulation, source
completeness or availability indicators, and technical eligibility for
deterministic calculations.

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

## Feature contract

### Recent precipitation accumulation

Recent precipitation accumulation may describe environmental context, such as
recent rainfall that could contribute to runoff where a defensible local
relationship is later established. It must not imply that rainfall is
universally favorable or unfavorable for fishing.

The feature view exposes 6-hour (target hour plus preceding 5 hours) and
24-hour (target hour plus preceding 23 hours) trailing precipitation windows.
Each window requires every exact hourly timestamp from the same run, location,
and atmospheric snapshot, with a non-null precipitation value. A complete
window exposes its total; an incomplete window exposes a null total and a
separate false completeness indicator. These windows are operational context,
not favorable or unfavorable fishing signals.

### Source completeness and availability

Completeness indicators describe data confidence, not environmental quality.
They must distinguish at least:

- successful source with all required values
- successful source with unavailable derived context
- failed or unavailable source
- incomplete historical window
- not applicable when a future context-specific feature does not apply

A missing value must remain distinguishable from a recorded source failure,
unavailable derived context, and an incomplete window. This contract does not
use a not-applicable state.
None of these states means bad fishing conditions.

### Technical eligibility

Technical eligibility means only that the required inputs for a deterministic
calculation are present and valid at the target grain. It does not mean good
fishing, safe conditions, or a positive score.

Eligibility must be derived from explicit input requirements and the associated
availability states. It must not replace source provenance or collapse missing,
failed, unavailable, incomplete, and not-applicable states into fishing
quality.

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
