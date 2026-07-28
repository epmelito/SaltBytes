# ForecastOps agent guidance

## Purpose

This file governs how contributors and AI agents work in this repository.

ForecastOps is evolving from a local weather forecast pipeline into a North
Carolina coastal fishing conditions data platform. Read the
[project charter](docs/project-charter.md) before proposing product or
architecture changes, and use the
[scope register](docs/scope-register.md) to distinguish current, authorized,
deferred, and excluded scope.

## Sources of truth

Each governance file is authoritative within its own responsibility:

- [Project charter](docs/project-charter.md): product purpose, approved direction,
  principles, and durable boundaries
- [Roadmap](docs/roadmap.md): approved delivery sequence
- [Scope register](docs/scope-register.md): current, future, deferred, and excluded
  scope, including known documentation drift
- [Decision records](docs/decisions/README.md): accepted choices and their rationale
- [Current handoff](docs/handoffs/current.md): transient work state and next steps

Source code, configuration, and tests are the evidence for current implemented
behavior. Existing descriptive documentation may contain known drift.

These sources have distinct responsibilities rather than forming one universal
hierarchy. This file governs working behavior, but it does not override the
charter's product intent or accepted decision records. If sources conflict,
identify the conflict and seek resolution instead of silently choosing one.

## Current implementation boundary

The repository currently implements a local, configuration-driven weather
forecast snapshot pipeline. The current `dev`, `test`, and `prod` settings are
local configurations rather than deployed cloud environments. The
[project charter](docs/project-charter.md) defines future product intent, and
the [scope register](docs/scope-register.md) records the verified implementation
and current boundaries.

## Required workflow

Follow this sequence for every work package:

1. **Inspect.** Read the issue, current handoff, scope register, and relevant
   source, tests, configuration, and documentation before changing files.
2. **Plan.** Create a bounded plan before editing. Identify:
   - the verified current state
   - the authorized scope
   - the files expected to change
   - decisions or assumptions that must not be made silently
   - intended validation
   - the checkpoint where work must stop
3. **Implement.** Make only the changes authorized by the plan and active work
   package. Add or update tests when implemented behavior changes.
4. **Validate.** Follow the change-type requirements below and any narrower
   limits in the issue. Record any temporarily deferred validation.
5. **Review.** Before handoff:
   - inspect the complete diff
   - compare the diff with the issue and scope register
   - confirm no unrelated files or unsupported decisions were introduced
   - confirm documentation reflects the resulting repository state
6. **Hand off.** Update the current handoff with the verified branch, work
   status, files changed, validation results, deferred checks, open issues, and
   next checkpoint.

Do not resolve deferred product or architecture decisions as an implementation
convenience. Use the decision process when a durable choice is required.

## Change boundaries

- Do not invent or silently select providers, locations, scoring rules, Azure
  services, retention periods, schedules, service levels, costs, metrics, or
  architecture details. Introduce them only through authorized work, reviewed
  evidence, and the decision process when required.
- Do not describe planned capabilities as implemented.
- Product implementation requires an authorized work package in the scope
  register, alignment with the applicable roadmap stage, and resolution of any
  decisions required before implementation.
- Preserve unrelated work and ignored runtime data.
- Do not expose secrets or commit generated data, databases, logs, caches, or
  environment files.
- Treat live API calls and local production-style runs as operations that may
  create runtime data.
- Follow narrower limits in the active task or handoff.
- Use one issue, one branch, and one focused implementation thread for each work
  package.

## Repository conventions

- Use Python 3.11 or later and the existing `src/` package layout.
- Keep environment-specific values in `config/`; do not fork transformation
  logic by environment.
- Preserve immutable raw-data behavior unless an accepted decision changes it.
- Use type annotations and keep Python lines within the configured 100-character
  limit.
- Follow the existing Ruff rules and function-oriented pytest style.
- Keep Markdown concise, factual, and organized with descriptive headings,
  short lists, and tables where useful.
- Use short-lived branches and pull requests rather than separate long-lived
  environment branches.

## Implementation simplicity

Apply these rules across Python, SQL, configuration, data models,
orchestration, tests, validation, and architecture:

- Start with the simplest implementation that fully satisfies confirmed
  requirements. Keep it robust for verified source behavior, real edge cases,
  failure modes, and platform constraints.
- Do not add abstractions, helper layers, fallbacks, tie breakers, defensive
  branches, generalized frameworks, or extra metadata for hypothetical risks.
  Every material part must have an evidence-based purpose.
- Before adding complexity, explain the verified problem it solves, why the
  simpler solution is insufficient, and what happens if the complexity is
  omitted.
- Simplicity must not compromise validation, data integrity, idempotency,
  failure handling, or protection against incorrect data, duplication, data
  loss, or unstable behavior.
- Prefer familiar, readable patterns when they are equally correct.

Use an MVP-first documentation and design boundary:

- Document and design only what is needed to unblock the next implementation
  step.
- Reserve decision records for durable, meaningful decisions.
- Defer speculative edge cases and exhaustive contracts.
- Let implementation, tests, and verified source behavior justify added detail.
- Strengthen governance iteratively when evidence shows it is needed.

## Validation

For documentation-only changes:

- inspect `git status --short`
- inspect the complete diff
- check changed paths against the authorized scope
- verify headings, relative links, formatting, and whitespace
- run the repository standard checks before merge unless the issue documents
  why a check is inapplicable

For code, configuration, test, script, or CI changes:

- run targeted checks for the changed behavior
- run `python -m pytest`
- run `python -m ruff check .`
- inspect `git status --short` and the complete diff

The repository standard checks are:

```powershell
python -m pytest
python -m ruff check .
```

If validation is temporarily deferred by the issue or a review checkpoint,
record each deferred check in the current handoff. Do not describe work as
complete until all required validation passes.

## Documentation and decisions

- Update the charter only when approved product intent or durable boundaries
  change.
- Update the roadmap when approved sequencing or stage status changes.
- Update the scope register when work enters, leaves, or is deferred from scope,
  or when known drift is discovered or resolved.
- Create a decision record for a durable product, data, or architecture choice
  that requires rationale. Follow
  [the decision process](docs/decisions/README.md).
- Do not create retrospective rationale unsupported by repository evidence.
- Keep transient status in the current handoff, not in durable governance files.

## Handoffs

Before ending a substantive work package, update
[docs/handoffs/current.md](docs/handoffs/current.md) with the verified branch,
objective, current status, files changed, validation performed, deferred
validation, known issues, deferred decisions, and next checkpoint. A handoff
reports state but does not approve scope, accept work, or resolve decisions.
