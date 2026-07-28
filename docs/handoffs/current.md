# Current handoff

## Handoff metadata

- Branch: `docs/ai-workflow-governance`
- Work package: initial repository AI workflow and governance
- Roadmap stage: 1, establish repository AI workflow and governance

The branch name was verified from Git before drafting this handoff.

## Objective

Create the six approved governance files without modifying existing
documentation, source code, tests, configuration, scripts, CI, or repository
skills.

## Drafting completed

- all six governance files were created
- the charter and scope register were reviewed and revised
- the roadmap and decision process were reviewed and revised
- `AGENTS.md` and this current handoff are undergoing final review

The governance package is a draft. It is not yet validated, accepted, merged,
or complete.

## Files created

- `AGENTS.md`
- `docs/project-charter.md`
- `docs/roadmap.md`
- `docs/scope-register.md`
- `docs/decisions/README.md`
- `docs/handoffs/current.md`

## Validation

An earlier command was run:

```powershell
git status --short
```

That command ran before later revisions and does not validate the current
drafts. No complete diff review has occurred.

The following remain pending:

- tests
- Ruff
- relative-link checks
- formatting and whitespace checks
- complete unstaged diff review
- staging
- staged patch review
- commit
- push
- pull request
- merge
- linked issue closure

## Known documentation drift

The existing inconsistencies found during repository inspection are recorded
in the [scope register](../scope-register.md). No existing documentation was
corrected in this package.

## Open decisions

Product, data-source, scoring, publication, scheduling, retention, Azure,
service-level, cost, and success-metric choices listed in the
[scope register](../scope-register.md) remain intentionally deferred.

No decision records exist.

## Immediate remaining sequence

1. Approve all six governance file contents.
2. Inspect the complete unstaged diff.
3. Run the required validation.
4. Stage the files and inspect the staged patch.
5. Commit and push the branch.
6. Open a pull request linked to the issue.
7. Merge after review.
8. Close the issue after its acceptance criteria are met.

Documentation reconciliation becomes the next work package only after this
governance package is validated, merged into `main`, and its linked issue is
closed.

That separate work package must not begin product implementation or resolve
deferred decisions.

## Review cautions

- Confirm that each governance file stays within its distinct responsibility.
- Confirm that the known-drift list is factual and complete enough for the next
  work package.
- Confirm that the stage completion language does not imply unapproved
  architecture, providers, metrics, or product behavior.
- Confirm that the complete diff contains only the six authorized governance
  files.
