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

## 6. Grow species assessments and establish operating evidence

**Status: Likely next direction**

SaltBytes may next develop a second reviewed species assessment while establishing
a minimal hosted workflow telemetry baseline. These independent efforts may
advance in parallel. Telemetry should establish measured evidence about hosted
execution, state movement, and reliability; its implementation, schema, exact
metrics, and migration thresholds require separate bounded work.

Each species will need its own approved method. A new score should use only
factors supported by the species research, keep confidence separate from the
number, and clearly mark local biological information that SaltBytes cannot
observe as unknown.

After the second species assessment, SaltBytes will evaluate whether a
demonstrated historical reprocessing need justifies replay sooner. Research and
feasibility work for a third species may proceed independently while replay is
evaluated or implemented. After the third total species assessment, SaltBytes
will pause additional species breadth for platform maturation.

## 7. Mature the data foundation before broader product work

**Status: Later, with decisions still required**

SaltBytes will complete deterministic historical replay and backfill before
observation ingestion and forecast verification if replay has not already been
required. Environmental observations are the first intentional major new data
family after the initial species expansion. SaltBytes will then reconcile
forecasts with later observations.

Only after that evidence exists may SaltBytes evaluate species score behavior
against responsibly collected fishing or catch results. Catch based validation
remains a separate, harder future research direction.

After replay, observations, and verification, SaltBytes will reassess storage
and batch execution against measured limitations. That checkpoint may conclude
that no migration is needed: DuckDB, GitHub Actions, and the existing hosted
design remain valid while they are effective. Analytical storage, dedicated
batch compute, infrastructure as code, and deeper cloud telemetry remain
conditional on demonstrated need.

SaltBytes will add metrics only when an approved species method, verification
need, data quality need, or demonstrated product requirement consumes them. It
will add external forecast sources only when an approved method or important
shared capability requires them.

## 8. Resume species and cross species product work

**Status: Later, with decisions still required**

After the first platform maturation cycle, SaltBytes may resume additional
species assessments and cross species product work.

Several species scores could support clearer comparisons across upcoming times
and fishing opportunities. SaltBytes may later help users see which species and
time periods have the strongest supported conditions.

An overall fishing conditions score also remains part of the product direction.
Its method cannot be chosen responsibly from one species model. Future work must
decide how seasonal relevance, unavailable scores, strong single species
opportunities, confidence, and explanations should affect the result.

No ranking method, fishing window method, or overall score formula is approved
yet. SaltBytes will not turn these comparisons into catch probability.

## 9. Expand coverage when justified

**Status: Conditional**

After the platform foundation is stronger, SaltBytes may expand through reviewed
North Carolina coastal locations. Mapped user selected points remain later work;
fully automatic coordinate resolution remains conditional on later evidence.

SaltBytes may also later improve its evidence and reach through work such as:

- improving mobile use or the static reports
- adding alerts or other delivery options

These are possible directions, not a fixed sequence. Each one needs a clear
user benefit, suitable evidence, and a bounded decision before implementation.

SaltBytes remains focused on North Carolina coastal fishing conditions. Broader
geographic expansion is not an approved goal.
