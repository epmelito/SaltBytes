# ForecastOps agent guidance

## Purpose

This file defines the minimum working rules for contributors and AI agents.

ForecastOps is currently focused on reaching a working coastal-conditions proof
of concept using the existing atmospheric, wave, sea-surface-temperature, and
tide pipeline.

## Default context

For normal implementation work, read only:

- the active issue or task
- this file
- the affected code and tests
- the selected skill, when applicable
- directly relevant documentation or ADRs

Do not read the full charter, roadmap, scope register, handoff, decision index,
or unrelated ADRs unless the task requires product, scope, architecture, or
historical context.

If sources conflict, stop and identify the conflict rather than silently
choosing one.

## Working rules

- Implement the smallest complete change that satisfies the active task.
- Inspect only the repository context needed to understand the affected
  behavior and risks.
- Do not modify unrelated files or absorb unrelated pre-existing problems.
- Do not invent providers, locations, scoring rules, architecture, fallbacks,
  schedules, retention policies, or product behavior.
- Preserve secrets, data integrity, provenance, source identity, safe reruns,
  and required failure isolation.
- Do not describe planned behavior as implemented.
- Prefer existing project patterns and dependencies.
- Add abstractions or dependencies only when the current task demonstrates a
  real need.
- Do not optimize, generalize, or future-proof beyond what is required for a
  working proof of concept.
- Use an issue and branch for meaningful code changes. Small manual
  documentation or instruction edits may be committed directly when reviewed
  and low risk.

## Implementation

For code, configuration, test, script, or CI changes:

1. Read the active task and affected code.
2. Implement the smallest complete solution.
3. Add or update focused tests for changed behavior.
4. Use focused checks while developing.
5. Run the repository-required broad checks once when the change is stable.
6. Inspect the final diff for scope and correctness.

Fix failures introduced by the change or required for task conformance. Report
unrelated failures separately.

## Validation

The standard broad checks are:

```powershell
python -m pytest
python -m ruff check .
```

Run them once after a meaningful code change stabilizes.

Do not rerun unchanged broad checks merely to reconfirm them. Rerun affected
checks after corrections, and rerun broad checks only when later changes could
invalidate the recorded result.

For documentation-only changes:

- inspect the changed paths and complete diff
- run `git diff --check`
- verify links or commands only when the change affects them

Application tests are not required for isolated documentation or instruction
changes.

## Documentation and decisions

Update documentation only when the task changes documented behavior or leaves
current instructions incorrect.

Read or update:

- the charter only for durable product intent
- the roadmap only for delivery sequencing
- the scope register only for active, deferred, or excluded scope
- an ADR only for a durable decision or when its accepted contract applies
- the handoff only for genuinely interrupted work that cannot be reconstructed
  cheaply

Do not repeat issue, ADR, roadmap, scope, or skill content in prompts or other
documents.

## Review

Self-review the complete affected diff before finalization.

Use `work-package-review` only for high-risk, uncertain, or suspicious work,
including security-sensitive changes, destructive persistence changes,
migrations, major schema changes, or complex failure isolation.

Routine work does not require an independent review stage.

## GitHub workflow

When finalizing approved work:

- stage only authorized files
- commit, push, create or update the pull request, apply metadata, and verify the
  result in one workflow
- reuse recorded validation evidence
- do not rerun application checks unless evidence is missing, stale,
  contradictory, or invalidated
- do not merge unless explicitly requested
- safely reconcile merged local and remote feature branches before starting new
  mutation-based work

## Handoffs

Do not update `docs/handoffs/current.md` for routine completed work.

Use it only when work is interrupted, blocked, or must continue in another
session and the state cannot be reconstructed cheaply from Git and GitHub.