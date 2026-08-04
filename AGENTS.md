# SaltBytes agent guidance

## Goal

Deliver the current roadmap milestone using the smallest safe change.

The active delivery sequence is owned by `docs/roadmap.md`. Do not expand scope
unless explicitly approved.

The active issue defines the work package scope. Applicable accepted decisions
define durable constraints. Current code and tests establish implementation
behavior. Do not let stale documentation, handoffs, or older prompts override
them.

## Default context

For normal work, read only:

- the active task
- this file
- affected code and focused tests
- directly relevant configuration or documentation

For species research tasks, first read `docs/research/README.md`, then only the
linked authoritative package sections needed for the task. Species research
remains nondefault context.

Do not load the full documentation set, research, requirements, decision index,
or unrelated ADRs by default.

## Working rules

- Implement the smallest complete change.
- Preserve working ingestion behavior unless the task requires a change.
- Fix observed problems, not hypothetical future problems.
- Do not refactor stable code solely to remove duplication.
- Do not add frameworks, abstractions, dependencies, providers, locations,
  scoring, fallbacks, scheduling, or deployment work without a current need.
- Preserve secrets, immutable accepted raw data, provenance, stable location
  identity, UTC persistence, visible source failures, and required source
  isolation.
- Do not modify unrelated files.
- Do not describe planned behavior as implemented.
- Follow the [user-facing language requirements](docs/requirements/user-facing-language.md)
  whenever work creates or changes text shown to anglers or general users. Keep
  internal research, schemas, field names, logs, and technical documentation
  precise, but translate them at the presentation boundary.

For the MVP, safe means avoiding exposed secrets, destructive persistence,
silent data corruption, hidden source failures, and unreadable failures. It
does not mean solving every future production concern.

## Implementation and validation

For meaningful application, persistence, or schema behavior changes:

1. inspect the affected behavior and focused tests
2. implement the smallest complete solution
3. add or update tests only for changed behavior
4. use focused checks while developing
5. run the full repository checks once when stable
6. inspect the final affected diff

For mechanical, dependency, documentation, formatting, configuration-only,
and narrow test-only changes, run focused checks for the affected contract
instead. GitHub Actions is the authoritative full-suite pull-request gate for
those low-risk changes.

Choose the smallest validation scope that still protects correctness, data
integrity, and the affected contracts. Reuse recorded validation evidence; do
not rerun broad checks redundantly after that evidence exists.

Full checks:

```powershell
python -m pytest
python -m ruff check .
```

Rerun them only when later changes could invalidate the result.

For documentation-only changes, inspect the changed files and run:

```powershell
git diff --check
```

## Documentation and decisions

Update documentation only when current instructions or behavior would otherwise
be wrong.

Use an ADR only for a durable blocking decision that cannot be resolved from
existing behavior and evidence. Do not create ADRs for routine implementation,
reversible local choices, speculative architecture, or deferred features.

Documents under `docs/decisions`, `docs/research`, and `docs/requirements` are
supporting references, not default context.

## Review and GitHub

Self-review the complete affected diff.

Use `work-package-review` only for high-risk or genuinely uncertain changes,
such as destructive persistence, major schema changes, security-sensitive work,
or complex source-failure isolation.

Use an issue and branch for meaningful code changes. Small low-risk manual
documentation edits may be committed directly after review.

Reuse recorded validation evidence. Do not rerun unchanged checks during
finalization. Do not merge unless explicitly requested.

## Handoffs

Update `docs/handoffs/current.md` only when work is interrupted, blocked, or
cannot be reconstructed cheaply from Git and GitHub.
