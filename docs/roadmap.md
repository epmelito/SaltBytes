# Roadmap

## Purpose

This roadmap defines the approved delivery sequence for ForecastOps. It
describes outcomes and dependencies without assigning dates or selecting
deferred implementation details.

The [project charter](project-charter.md) defines product intent. The
[scope register](scope-register.md) distinguishes approved work from deferred
decisions and authorizes active work packages.

## Current state

ForecastOps is a tested local weather forecast snapshot pipeline. It is the
technical foundation for the approved North Carolina coastal fishing
conditions data platform, but it does not yet implement that product.

Roadmap stage 1 is complete. Pull request #13 introduced the six governance
files after review and a successful required `test and lint` check. The
lifecycle records reflect the completed stage.

Roadmap stage 2 is complete. The documentation reconciliation work package
aligned the authorized technical documentation with verified repository
behavior while retaining the out-of-scope failure-review skill drift.

Roadmap stage 3 is next in sequence but remains unauthorized and unstarted.

## Delivery stages

### 1. Establish repository AI workflow and governance

Create the initial governance package, define distinct sources of truth,
establish scope and decision controls, and provide a repeatable handoff
practice.

Status: Complete.

Completion evidence:

- all six governance files exist
- their responsibilities and cross-links were reviewed
- the required `test and lint` pull request check completed successfully
- pull request #13 introduced the governance files into `main`
- the lifecycle records reflect the completed stage

### 2. Reconcile existing documentation

Review the known drift in the [scope register](scope-register.md) and update
existing technical documentation to match verified repository behavior and
approved product direction.

Status: Complete.

Completion evidence requires:

- each recorded drift item is reviewed against repository evidence
- affected documentation is corrected, or the drift item is explicitly retained
  with rationale
- resolved drift entries are removed or updated in the scope register
- repository validation passes

### 3. Define coastal locations and fishing-condition requirements

Select a representative North Carolina coastal location set and define the
environmental requirements needed for comparable fishing windows.

This stage must resolve only the deferred decisions needed for subsequent data
work.

Completion evidence requires:

- the representative location set and fishing-condition requirements are
  documented
- each selection and requirement is traceable to reviewed evidence
- decisions needed for subsequent data work are accepted and indexed
- remaining deferred topics stay identified in the scope register
- no product implementation is included in the stage

### 4. Extend coastal data-source ingestion

Add reusable ingestion for approved coastal sources while retaining source data
and preserving observable pipeline behavior.

Completion evidence requires:

- ingestion is implemented and tested for only the approved sources
- retained source data is traceable to its source and pipeline run
- quality results and operational metadata cover the added ingestion
- repository validation passes
- unresolved source decisions remain deferred

### 5. Build normalized and historical coastal data models

Model approved coastal data consistently across locations and time, including
the history needed to trace forecast changes.

Completion evidence requires:

- the approved normalized and historical models are documented and tested
- source-to-model lineage is documented
- forecast history and revision behavior can be demonstrated from retained data
- repository validation passes
- unresolved retention choices remain deferred unless required and accepted

### 6. Implement deterministic scoring

Calculate fishing-condition scores from approved variables and weights using
deterministic, inspectable transformations.

Completion evidence requires:

- the scoring requirements and any required decisions are accepted
- scoring transformations are deterministic, documented, and tested
- each score can be explained through its component inputs
- score inputs are traceable to modeled source conditions
- repository validation passes

### 7. Rank and publish fishing windows

Compare upcoming windows and publish consumer-ready datasets without presenting
the results as guarantees or official safety guidance.

Completion evidence requires:

- rankings are reproducible from approved scores and inputs
- the publication contract is approved
- published datasets conform to that contract
- outputs preserve the charter's fishing-success and safety boundaries
- repository validation passes

### 8. Migrate to reusable Azure infrastructure

Move the solution to a reusable personal Azure data platform that can support
later portfolio projects.

This stage is not implementation-ready until the required deferred Azure
architecture and operational decisions are resolved and its completion evidence
is approved.

### 9. Add a public portfolio display

Present the platform's data, explanations, lineage, and engineering qualities
as a public portfolio experience.

This stage is not implementation-ready until the required deferred publication
and display decisions are resolved and its completion evidence is approved.

## Dependencies

Stages are ordered because later work depends on earlier governance,
requirements, data, and publication contracts. A stage may be refined before it
becomes active, but product implementation should not bypass unresolved
decisions required by that stage.

The roadmap sequences outcomes. It does not authorize active work packages;
authorization belongs in the scope register.

## Roadmap changes

Roadmap changes must remain consistent with the charter and be reflected in the
scope register. Durable product or architecture choices should follow the
[decision process](decisions/README.md). Do not add dates or select deferred
details without approval.

Current work status and the next recommended action belong in the
[current handoff](handoffs/current.md).
