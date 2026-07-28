# Current handoff

## Handoff metadata

- Branch: `docs/define-coastal-requirements`
- Issue: #20
- Work package: define first-release coastal location and fishing-condition
  requirements
- Roadmap state: stage 3 authorized and in progress

This handoff records the current state of the roadmap stage 3 research and
decision work package. It does not mark stage 3, the pull request, or issue #20
complete.

## Objective

Define the first-release coastal location and fishing-condition requirements
needed before later source evaluation and ingestion work.

## Research and evidence review

Research and evidence review are complete for:

- the first-release audience and fishing-context boundary
- the composite geographic model
- the representative initial North Carolina coastal location set
- the environmental requirement classifications
- the current Open-Meteo implementation and its potential additional coverage
- provider, spatial, safety, and evidence limitations

Sources are recorded with direct evidence and inference distinguished.
Open-Meteo remains the baseline source to evaluate but is not accepted as the
authoritative marine, tide, current, or safety provider.

The documentation was tightened around environmental data ingestion, spatial
source relationships, forecast history, data quality, and support for later
deterministic and explainable scoring. Access evidence is limited to
establishing each selected location as an identifiable recreational fishing
destination, with brief closure caveats where relevant.

## Accepted decisions

The decision owner accepted:

- the first-release audience and fishing-context boundary
- the composite geographic model and initial location set
- the first-release environmental requirement baseline

The accepted decisions are recorded in:

- `docs/decisions/0001-first-release-user-and-fishing-context.md`
- `docs/decisions/0002-composite-geographic-model-and-initial-locations.md`
- `docs/decisions/0003-first-release-environmental-requirement-baseline.md`

## Accepted first-release boundary

The first release serves general recreational coastal anglers in:

- surf contexts
- publicly accessible fixed fishing pier contexts

Fishing windows may be compared only within the same context. Environmental
conditions remain general rather than species-specific.

Shore-accessed inlet, vessel-based nearshore, offshore, and species-specific
uses remain deferred.

## Accepted initial locations

- Jennette’s Pier
- Beach Access Ramp 72, Ocracoke Island
- Fort Macon State Park, ocean side
- Bogue Inlet Pier
- Fort Fisher State Recreation Area

Bogue Inlet Pier is treated only as a pier context. Beach Access Ramp 72 is
treated only as an ocean-side surf context.

## Stage 3 documentation

The stage 3 documentation is now present:

- `docs/requirements/coastal-locations.md`
- `docs/requirements/fishing-conditions.md`
- `docs/decisions/0001-first-release-user-and-fishing-context.md`
- `docs/decisions/0002-composite-geographic-model-and-initial-locations.md`
- `docs/decisions/0003-first-release-environmental-requirement-baseline.md`

The decision index, scope register, roadmap, and current handoff contain the
approved stage 3 updates.

## Files changed

- `docs/requirements/coastal-locations.md`
- `docs/requirements/fishing-conditions.md`
- `docs/decisions/0001-first-release-user-and-fishing-context.md`
- `docs/decisions/0002-composite-geographic-model-and-initial-locations.md`
- `docs/decisions/0003-first-release-environmental-requirement-baseline.md`
- `docs/decisions/README.md`
- `docs/scope-register.md`
- `docs/roadmap.md`
- `docs/handoffs/current.md`

## Validation

Validation for this documentation-only work package completed successfully:

- `git status --short`: reviewed
- `git diff --name-only`: reviewed
- complete diff: reviewed, including all five new untracked documents
- changed-path review: exactly the nine files authorized by issue #20
- heading and relative-link review: passed
- content-consistency review: passed
- `git diff --check`: passed with LF-to-CRLF normalization warnings
- `.\.venv\Scripts\python.exe -m pytest`: 49 tests passed
- `.\.venv\Scripts\python.exe -m ruff check .`: all checks passed

Stage 3 must not be described as complete until required validation and its
remaining lifecycle conditions are satisfied.

## Stage 4 relationships

The following relationships remain unresolved for evaluation before ingestion
work:

- display or destination and weather-request coordinates
- marine sampling coordinates
- tide and water-level references
- observation-station relationships
- warning and forecast-zone mappings
- provider fitness and source authority
- source resolution and spatial representativeness

No provider has been selected for marine, tide, current, or safety data.

## Deferred work

The following remain deferred:

- scoring variables, formulas, thresholds, and weights
- retention
- scheduling
- publication
- API and dashboard design
- Azure and deployment architecture
- shore-accessed inlet use cases
- vessel-based nearshore use cases
- offshore use cases
- species-specific use cases and recommendations

## Next checkpoint

Validate and inspect the complete documentation-only diff. Do not begin product
implementation or mark roadmap stage 3, the pull request, or issue #20 complete
at this checkpoint.
