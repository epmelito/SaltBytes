---
name: github-workflow
description: Create, update, and finalize ForecastOps GitHub issues, branches, commits, pushes, and pull requests. Use when repository work requires labels, assignees, issue comments, branch setup, commits, pull request creation, issue linking, metadata verification, or other routine GitHub workflow actions.
---

# GitHub workflow

## Responsibility

Complete authorized ForecastOps GitHub workflow actions accurately and with
minimal user interaction.

Discover the repository and GitHub state, perform the complete bounded workflow,
verify the resulting state, fix routine omissions, and return one concise
report.

## Autonomous workflow

When the requested outcome is clear:

1. Read the active issue and applicable repository guidance.
2. Inspect the current branch, working tree, remote, available labels, and
   relevant GitHub state.
3. Perform the authorized issue, branch, commit, push, or pull request actions.
4. Apply metadata appropriate to the specific work.
5. Verify the resulting GitHub and repository state.
6. Fix routine omissions caused by the workflow.
7. Return one completion report.

Do not ask for confirmation before routine inspection, issue comments, applying
an existing appropriate label, assigning the repository owner, pushing the
authorized branch, or creating a requested pull request.

## Dynamic labels

- Inspect the available repository labels and the active work package.
- Apply the smallest set of existing labels that accurately describes the work.
- Do not reuse labels merely because they were used on a previous issue or pull
  request.
- Do not use fixed labels for every workflow.
- Create a new label only when no existing label fits and the category is
  expected to recur.
- Give a new label a short factual description.
- Ask before creating a label when its category is questionable, overly narrow,
  or likely to be used only once.
- Apply matching labels to the pull request when they remain accurate for the
  delivered work.

## Issues and pull requests

- Assign newly created issues and pull requests to the repository owner unless
  instructed otherwise.
- Link completed work using `Closes #<issue>` when the pull request should close
  the active issue.
- Preserve existing issue or pull request content unless a change is authorized.
- After creating or updating a pull request, verify:
  - target branch
  - source branch
  - changed files
  - included commits
  - labels
  - assignee
  - issue closing linkage
  - pull request URL
- Do not imply that metadata was applied unless the resulting GitHub state
  confirms it.

## Branches and commits

- Follow repository branch and commit conventions.
- Stage only files authorized by the active work package.
- Do not include unrelated working tree changes.
- Confirm the commit contains the intended paths before pushing.
- Do not force push.
- Do not delete branches unless explicitly requested.

## Human decision gates

Stop and request input only when:

- the requested outcome is materially ambiguous
- the target or base branch cannot be determined safely
- unrelated working tree changes create a conflict
- a new label would represent a questionable or one time category
- the action would merge, close, reopen, delete, overwrite, or otherwise make a
  destructive or difficult to reverse change
- required permissions are unavailable
- an external action falls outside the authorized work package

State the exact decision or permission needed.

## Boundaries

- Do not merge pull requests unless explicitly requested.
- Do not modify repository files unless the task includes repository changes.
- Do not change unrelated issue or pull request content.
- Do not repeat actions that have already been completed and verified.
- Do not report success based only on command completion.
- Do not hide incomplete or failed GitHub actions.

## Completion report

Report only:

- result
- issue or pull request links
- branch and commit details
- changed paths
- labels and assignee
- issue closing linkage
- validation and resulting state verified
- unresolved permissions, risks, or blocked actions

Keep the report concise.
