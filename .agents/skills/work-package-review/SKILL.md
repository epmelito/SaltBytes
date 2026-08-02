---
name: work-package-review
description: Perform a focused, read-only conformance review of one SaltBytes work package using either current working-tree changes or immutable base and head revisions. Use when asked to verify issue conformance, scope, accepted decisions, validation evidence, and directly affected documentation.
---

# SaltBytes work-package review

## Inputs

Require an issue number.

In working-tree mode, treat all staged, unstaged, and untracked changes as the
proposed work package. Stop when unrelated local changes make the review target
ambiguous.

Discover the base, head, target branch, and review mode from repository and
GitHub state when unambiguous. Ask only when they cannot be determined safely.

In working-tree mode, identify every staged, unstaged, and untracked path before
reviewing.

## Workflow

1. Retrieve and read the governing GitHub issue using read-only access.
2. Read the applicable `AGENTS.md`.
3. Inspect the exact review target and changed paths:
   - in revision mode, inspect the immutable `base..head` diff
   - in working-tree mode, inspect staged, unstaged, and untracked changes
     relative to the resolved base
4. Identify only the governance files and accepted ADRs needed to evaluate the
   issue or changed behavior.
5. Map the issue requirements, acceptance criteria, and exclusions to the
   changed code, configuration, tests, scripts, and documentation.
6. Review recorded test, lint, diff, CI, and manual-review evidence. Run the
   narrowest relevant non-live check only when recorded evidence is missing,
   stale, contradictory, or insufficient. Distinguish recorded results from
   checks run during the review.
7. In revision mode, inspect directly affected current implementation or
   documentation only when needed to identify confirmed post-head drift. In
   working-tree mode, treat the working tree as the proposed state and do not
   perform separate post-head drift analysis.
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
- Review the complete target diff, but trace beyond changed paths only when the
  issue behavior, uncertainty, or risk requires it. Use deeper tracing for
  persistence, schemas, security, transactions, failure isolation, source
  independence, and data integrity. Keep isolated documentation, test,
  metadata, and mechanical changes narrow.

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
- Use this skill for high-risk or uncertain work packages, not as a mandatory
  stage for every routine change.

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
