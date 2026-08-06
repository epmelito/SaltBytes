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

**Status: Current**

SaltBytes is turning its reports and dashboard from technical output into a
coherent product for two different needs:

- anglers need a clear view of coastal conditions and species assessments
- maintainers need clear evidence about pipeline health, forecast changes, and
  source traceability

The Conditions page, Pipeline Monitoring, and Forecast Revisions have already
been reorganized around plain language, useful summaries, and deeper evidence
only when needed.

The remaining work is tracked in the [current roadmap](roadmap.md). This phase
must finish before SaltBytes starts another major product expansion.

## 6. Add scores for more species

**Status: Likely next direction**

After the reporting phase, SaltBytes is likely to develop scores for more of the
reviewed shore fishing species.

Each species will need its own approved method. A new score should use only
factors supported by the species research, keep confidence separate from the
number, and clearly mark local biological information that SaltBytes cannot
observe as unknown.

The next species has not been selected. This phase is a likely direction, not an
active implementation promise.

## 7. Help users compare fishing opportunities

**Status: Later, with decisions still required**

Several species scores could support clearer comparisons across upcoming times
and fishing opportunities. SaltBytes may later help users see which species and
time periods have the strongest supported conditions.

An overall fishing conditions score also remains part of the product direction.
Its method cannot be chosen responsibly from one species model. Future work must
decide how seasonal relevance, unavailable scores, strong single species
opportunities, confidence, and explanations should affect the result.

No ranking method, fishing window method, or overall score formula is approved
yet. SaltBytes will not turn these comparisons into catch probability.

## 8. Expand evidence and coverage when justified

**Status: Conditional**

SaltBytes may later improve its evidence and reach through work such as:

- comparing forecasts with later observations
- checking score behavior against responsibly collected fishing results
- adding more reviewed North Carolina fishing locations
- improving mobile use or the static reports
- adding alerts or other delivery options
- changing the hosted design when the current approach shows a real limit

These are possible directions, not a fixed sequence. Each one needs a clear
user benefit, suitable evidence, and a bounded decision before implementation.

SaltBytes remains focused on North Carolina coastal fishing conditions. Broader
geographic expansion is not an approved goal.
