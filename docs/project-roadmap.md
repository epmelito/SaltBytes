# Project roadmap

This roadmap explains the long range direction of SaltBytes. It records the main
phases of the project, the important changes in direction, and the ideas that
still need evidence or a decision.

The [project charter](project-charter.md) defines the project's lasting purpose
and boundaries. The [current roadmap](roadmap.md) lists the next few pieces of
work.

## 1. Build the coastal data foundation

**Status: Complete**

SaltBytes began as a local data pipeline for upcoming conditions at North
Carolina fishing locations. It learned to collect weather, waves, water
temperature, and tide predictions without treating one failed source as a
failure of the whole run.

The project preserves accepted source responses, stores cleaned records with
their source and run history, and combines available conditions by location and
forecast hour. It also keeps earlier forecasts so users can see how a prediction
changed over time.

This phase established the core rule that SaltBytes should keep data, missing
information, and failures visible instead of hiding them.

## 2. Run and publish SaltBytes reliably

**Status: Complete**

SaltBytes moved from a local pipeline to scheduled hosted runs with durable
storage. It can recover its saved state, keep partial results when one source
fails, and publish the latest usable output without erasing earlier history.

The project now publishes text and HTML reports, a public data export, and an
interactive dashboard. Operations views make run health, source problems,
forecast changes, and source history available for inspection.

This phase kept the hosted design small. SaltBytes did not add services or
infrastructure only to imitate a larger production platform.

## 3. Add fishing context backed by research

**Status: Complete**

SaltBytes expanded beyond raw forecast values so the data could support fishing
questions without making unsupported claims.

The project added:

- tide timing and phase
- shoreline direction and how wind and waves approach each site
- recent rain and whether required source data is available
- daylight, twilight, cloud, and solar context
- a shared set of conditions ready for scoring and comparison
- a reviewed fishing factor registry
- research for a selected group of North Carolina shore fishing species

These additions created a stronger base for explainable species assessments.
They did not turn general weather relationships into universal fishing rules.

## 4. Build and publish the first species score

**Status: Complete**

Spanish mackerel became the first species pilot because the available research
and SaltBytes data supported a useful, limited assessment.

SaltBytes now calculates and publishes an explainable score from 0 to 100 for
Spanish mackerel conditions. The result shows what supports the score, what
limits it, what remains unknown, and how much confidence the available evidence
supports.

The score is calculated when dashboard data is exported and is not stored in
the database. It describes how well forecast conditions match the approved
method. It does not claim that fish are present, within casting range, or likely
to be caught.

The original plan expected several species scores before showing them in the
public dashboard. SaltBytes changed course and published the first complete
score earlier, then used that result to improve the reports before adding more
species.

## 5. Make the reports clear and useful

**Status: Complete**

SaltBytes made its reports and dashboard into a coherent desktop product for two
different needs:

- anglers need a clear view of coastal conditions and species assessments
- maintainers need clear evidence about pipeline health, forecast changes, and
  source traceability

The public landing page and dashboard now provide direct routes for those
audiences. Conditions presents coastal conditions and species assessments;
Operations presents pipeline health, forecast changes, and source traceability.
The desktop views use plain language, useful summaries, and deeper evidence only
when needed.

Mobile refinement and static HTML report redesign remain later work.

## 6. Establish the location-first assessment foundation

**Status: Likely next direction**

SaltBytes will shift from treating numeric scores as the required form for every
species to location-first, species-aware assessments. These assessments combine
reusable statewide species knowledge, recent fishing observations, and forecast
and site conditions while keeping their evidence scope and uncertainty visible.

Fishing observations must remain distinct from source advice, forecasts, and
environmental observations used later for forecast verification. A report not
mentioning a species is not evidence of absence. Observation scope and strength
must remain distinguishable, and no one publisher may become necessary for the
assessment model to work.

The next product foundation is a source-risk classification and a
source-independent observation product contract. The project risk assessment
uses `green`, `yellow`, and `red` suitability rather than treating written
permission from every source as a development prerequisite. It is not legal
advice; a bounded legal review remains a future commercialization gate.

## 7. Expand locations and observations with evidence

**Status: Later, with decisions still required**

After the observation contract is established, SaltBytes may define bounded
observational ingestion work and expand locations through normal feasibility
decisions. The current roadmap owns the near-term location sequence.

Observational richness is one location-selection criterion alongside habitat,
geographic diversity, cross-species value, and environmental representativeness.
SaltBytes will not favor ocean piers solely because they publish convenient
reports. Longer term, supported locations may cover coastal, sound, inlet,
estuarine, and other North Carolina saltwater contexts without prematurely
fixing a statewide taxonomy.

## 8. Mature evidence and platform capability when justified

**Status: Conditional**

Hosted telemetry, deterministic replay and backfill, environmental observation
ingestion, and forecast verification remain possible platform work when their
original need applies. Environmental observations and fishing observations have
separate purposes and must not be conflated. Catch-based validation remains a
separate, harder research direction after forecast verification and other
evidence mature.

SaltBytes will reassess storage and batch execution only when measured
limitations justify it. DuckDB, GitHub Actions, and the existing hosted design
remain valid until then. Analytical storage, dedicated batch compute,
infrastructure as code, and deeper cloud telemetry remain conditional on
demonstrated need.

SaltBytes will add metrics only when an approved method, verification need, data
quality need, or demonstrated product requirement consumes them. It will add
external forecast sources only when an approved method or important shared
capability requires them.

## 9. Resume broader assessment and product work

**Status: Later, with decisions still required**

After the observational and location foundations mature, SaltBytes may resume
additional species assessments and cross-species product work. A numeric species
method remains optional and requires its own explicit approval. The deterministic
red drum score path is paused; its research remains useful for a later
location-first assessment.

A general fishing-conditions or fishability score is a deep future possibility.
Its inputs, meaning, weighting, confidence treatment, and evidence requirements
remain deferred. Individual species scores are not prerequisites, and it will
not become catch probability.

SaltBytes may later improve mobile use, static reports, alerts, or delivery
options through bounded work. It remains focused on North Carolina coastal
fishing conditions; broader geographic expansion is not an approved goal.
