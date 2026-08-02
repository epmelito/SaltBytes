---
name: reporting-engineering
description: Implement or review bounded SaltBytes changes to deterministic reports, public reporting data, interactive dashboards, browser behavior, responsive layout, or published reporting routes. Use when correctness must be proven in the rendered artifact, not only in source or build output.
---

# Reporting engineering

## Responsibility

Implement or review bounded reporting changes so the rendered result is
accurate, usable, visually coherent, and supported by proportionate evidence.

Do not turn reporting work into a general frontend redesign or broad user
interface test program.

When asked only to review, do not edit files or perform mutations.

## Workflow

1. Read the active issue and applicable repository guidance.
2. Identify the changed reporting contract and what the user must understand or
   do.
3. Inspect the minimum data contract, source, and built output needed to verify
   that behavior.
4. Preserve existing report roles, public data contracts, and routes unless the
   issue explicitly changes them.
5. Keep database queries and reporting data shaping outside browser presentation
   code unless an accepted design requires otherwise.
6. Implement the bounded change and build the production artifact.
7. Serve and validate the built artifact in a browser, or validate the deployed
   artifact when hosted verification is required:
   - load a meaningful default state
   - exercise changed controls and dependent content
   - check direct route loading and refresh
   - synchronize checks on the exact rendered state or value being asserted
   - fail on browser errors, unresolved modules, or leaked source expressions
8. Inspect relevant wide and narrow layouts for hierarchy, density, readability,
   grouping, and usable table or chart overflow.
9. Fix blocking defects and report optional visual improvements separately.

## Reporting rules

A successful build or HTTP response does not prove browser correctness.

Browser checks must wait for the exact user visible state under test. Do not
rely on elapsed time or a surrogate readiness condition that can pass before
dependent content settles. Do not hide synchronization defects with sleeps,
retries, or larger timeouts.

Controls must initialize with valid options and visible data. Dependent content
must update after meaningful interaction, and direct routes must remain usable.

Prioritize a clear page purpose, visible hierarchy, readable labels and units,
and enough spacing to distinguish related information. Avoid repeated content
and competing elements that make the primary information difficult to find.

Treat runtime errors, broken controls, empty default states, misleading or
leaked content, unreadable overlap, and unusable overflow as blocking.

Treat minor spacing, styling, and density improvements as nonblocking unless
they materially prevent understanding or use.

## Boundaries

Do not require a design system, component library, screenshot regression,
multiple browser engines, exhaustive accessibility auditing, or a broad browser
test suite unless the active issue requires it.

Do not encode framework specific recipes, exact routes, selectors, commands, or
page layouts as permanent guidance.

Python export and query logic remains under `python-engineering`. Public data
exposure and publication security remain under `security-engineering`. GitHub
operations remain under `github-workflow`. Final issue conformance remains
under `work-package-review`.

## Completion report

Report only:

- result
- files changed
- rendered behavior implemented or reviewed
- browser and visual validation performed
- blocking and nonblocking findings
- unresolved risks or missing evidence

## Validation and review

Run:

`git diff --check`

Inspect the complete diff and confirm:

- only the new skill file changed
- the trigger is clear
- the skill does not duplicate `AGENTS.md` or existing skills
- the guidance is general and not overfit to issue #89
- production artifact validation is explicit
- browser synchronization requires exact rendered evidence
- blocking defects and optional polish remain distinct
- the skill remains concise

Do not run Python tests, Ruff, dashboard builds, or browser tests because this
work package changes only skill documentation.

Do not commit, push, or open a pull request yet.

Return only:

- issue number and URL
- branch and worktree path
- changed file
- concise skill review
- `git diff --check` result
- working tree status
- any blocker or scope concern
