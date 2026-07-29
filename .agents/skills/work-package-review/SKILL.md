---
name: work-package-review
description: Perform a focused, read-only conformance review of one completed ForecastOps GitHub issue from its base and head revisions. Use when asked to verify that a completed ForecastOps work package satisfies its issue, remains within scope, follows relevant accepted decisions, has sufficient validation evidence, and leaves implementation or lifecycle documentation consistent.
---

# ForecastOps work-package review

## Inputs

Require:

- issue number
- base revision
- head revision

Ask only for a missing input. Discover the repository, remote, and relevant
context from the working directory. Confirm that both revisions resolve before
reviewing.

## Workflow

1. Retrieve and read the completed GitHub issue using read-only access.
2. Read the applicable `AGENTS.md`.
3. Inspect the exact `base..head` diff and changed paths.
4. Identify only the governance files and accepted ADRs needed to evaluate the
   issue or changed behavior.
5. Map the issue requirements, acceptance criteria, and exclusions to the
   changed code, configuration, tests, scripts, and documentation.
6. Review recorded test, lint, diff, CI, and manual-review evidence. Run the
   narrowest relevant non-live check only when recorded evidence is missing,
   stale, contradictory, or insufficient. Distinguish recorded results from
   checks run during the review.
7. Inspect the affected current implementation and documentation for contradictions, stale lifecycle state, or claims unsupported by the head revision. Report post-head drift separately, and do not attribute it to the original work package unless it existed at the head revision.
8. Report only findings supported by cited repository, revision, issue, or
   validation evidence.
9. Separate confirmed defects from evidence that is unavailable or
   insufficient.
10. Stop without editing files.

Use the current working tree only to assess post-head consistency or drift. Do
not treat unrelated current changes as part of the work-package diff.

## Assessment rules

- Use `fail` when at least one blocking finding prevents issue conformance.
- Use `pass with findings` when there are no blocking findings but there are
  nonblocking findings or material missing evidence.
- Use `pass` when there are no findings and no material missing evidence.
- Treat an observation as blocking only when evidence shows that it violates a
  requirement, acceptance criterion, explicit exclusion, accepted decision, or
  required validation boundary.
- Do not invent findings or promote optional improvements into requirements.
- Do not treat absent review comments, historical defect notes, or other
  optional records as material missing evidence unless the issue, repository
  governance, or acceptance criteria explicitly require them.

For each finding include:

- **Severity:** blocking or nonblocking
- **Evidence:** precise issue, file, line, revision, diff, or validation evidence
- **Impact:** the demonstrated consequence
- **Required action:** the smallest action needed for conformance

## Boundaries

- Do not edit repository files or rerun live pipelines.
- Do not broaden the review into a general architecture or code review.
- Do not restate repository governance or require new process artifacts.
- Do not inspect unrelated repository areas or resolve deferred decisions.
- Do not recommend speculative abstractions or extensibility.

## Output

Use exactly these sections and keep them concise:

```markdown
# Work package review

## Result
pass | pass with findings | fail

## Blocking findings
None.

## Nonblocking findings
None.

## Missing evidence
None.

## Scope assessment
...

## Validation reviewed
...

## Review summary
...
```

Use `None.` when a findings section is empty.
