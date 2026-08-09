---
name: reporting-engineering
description: Implement or review SaltBytes reports, dashboards, published pages, navigation, reporting flow, information architecture, visual presentation, responsive layout, browser behavior, accessibility basics, and user-facing language. Use for bounded reporting changes, bounded read-only reviews, or project-wide read-only reporting audits.
---

# Reporting engineering

## Purpose

Treat reporting as product design, not data serialization.

A successful reporting experience must be:

- accurate
- understandable
- easy to navigate
- visually coherent
- responsive
- intentionally structured around what the user needs to understand or do

Correct data displayed without hierarchy, restraint, navigation, or thoughtful
presentation is not sufficient.

This skill supports three modes:

1. bounded implementation of one reporting change
2. bounded read-only review of one reporting surface or change
3. project-wide read-only reporting audit

When the requested mode is read only, do not modify repository files, GitHub
state, generated artifacts, or deployed content.

Do not turn bounded work into an unfocused redesign or a collection of unrelated
cosmetic changes.

## Product standard

Reports and dashboards should feel like a polished public product, not a
database export, debug page, internal operations screen, or collection of
default components.

Every visible element should support:

- the page purpose
- the user's understanding
- the user's next action
- necessary context, evidence, uncertainty, provenance, or safety meaning

Do not display information merely because it is available.

Reject:

- arbitrary card grids
- endless tables or historical lists
- repeated information
- equal visual weight for every metric
- unexplained technical labels
- excessive scrolling without structure
- bland layouts with no clear hierarchy
- decorative elements that do not improve comprehension
- information placed on the wrong page
- desktop layouts merely compressed into mobile width

Prefer clear prioritization, controlled density, progressive disclosure, and
purposeful separation between primary information and deeper technical detail.

## Reporting flow

Review the reporting system as a connected user journey, not only as isolated
pages.

Assess whether:

- the entry point explains what SaltBytes provides
- the primary action or destination is obvious
- users can move between major reporting surfaces
- deep pages provide a clear path onward or back
- direct links and refreshed routes remain understandable
- conditions, history, provenance, and operations are separated appropriately
- recent information is prioritized over growing archives
- technical detail is available without dominating the default experience
- the page and section sequence matches the user's likely questions

Recommend removing, condensing, grouping, relocating, or separating content when
the current structure does not support the reporting flow.

## Language and meaning

Follow the
[user-facing language requirements](../../../docs/requirements/user-facing-language.md)
for reports, dashboards, charts, tables, controls, notices, metrics, warnings,
and explanations.

Use natural everyday wording for the default experience. Translate internal
field names, enum values, pipeline terms, and academic phrasing where a clear
user-facing alternative exists.

Preserve:

- material uncertainty
- safety meaning
- provenance limitations
- the distinction between measured, forecast, derived, unavailable, unknown,
  failed, and not applicable information

Do not simplify language in ways that create unsupported claims about fish
presence, catch likelihood, success, recommendations, or safety.

## Review focus

### Information and visual design

Review:

- page composition and content sequence
- typography and visual hierarchy
- whitespace, alignment, and visual rhythm
- grouping and consistency of sections, cards, and controls
- color and contrast where they affect meaning
- chart choice and whether a chart is warranted
- table necessity, density, scanning, and overflow
- progressive disclosure of secondary detail
- unavailable, empty, loading, and error states
- navigation prominence
- wide and narrow layouts
- whether responsive layouts restructure content appropriately

Prefer polished, approachable, restrained, and coherent design over animation,
novelty, or decoration.

### Functional correctness

Identify:

- what the surface is for
- what the user must understand or do
- which data contract, generated artifact, route, or deployed page supports it
- whether the rendered result communicates the intended meaning accurately

Verify as applicable:

- correct values, formatting, labels, and units
- meaningful default states
- working controls and dependent content
- direct route loading and refresh
- clear navigation
- readable charts, tables, and supporting detail
- usable overflow and responsive behavior
- correct unavailable and failure states
- absence of runtime errors, unresolved modules, leaked expressions, or internal
  identifiers
- consistency between source data, generated output, and rendered presentation

### Accessibility basics

Check:

- keyboard access for interactive controls
- visible focus where interaction requires it
- meaningful labels for controls
- logical heading structure
- contrast where it affects readability or meaning

This is a functional baseline, not an exhaustive accessibility audit.

## Bounded implementation

For implementation work:

1. Read the active issue and applicable repository guidance.
2. Identify the changed reporting contract and user outcome.
3. Inspect the minimum relevant data contract, source, and generated output.
4. Preserve public contracts and routes unless the issue changes them.
5. Keep query and export logic outside browser presentation code unless an
   accepted design requires otherwise.
6. Implement the smallest complete change.
7. Build the production artifact.
8. Serve and inspect the built artifact, or inspect the deployed artifact when
   hosted verification is required.
9. Exercise changed routes, controls, layouts, unavailable states, and
   accessibility basics.
10. Inspect the complete affected diff.

Browser checks must wait for the exact user-visible state being asserted. Do not
use sleeps, arbitrary delays, or unrelated readiness signals to hide reactive
timing defects.

When deployed behavior differs from the source or local artifact, compare the
source, production build, and deployed result before assigning the defect. Do
not assume a repository change is live.

## Bounded read-only review

For a bounded review:

- inspect the affected source, generated artifact, browser behavior, and deployed
  page as needed
- verify the reporting contract and user outcome
- evaluate both functional correctness and presentation quality
- distinguish defects from optional improvements
- provide reproducible evidence for each finding
- do not edit files or perform GitHub mutations
- do not broaden the review unless a related defect prevents a valid conclusion

## Project-wide read-only audit

Before auditing, define:

- included reporting surfaces
- representative routes and states
- wide and narrow viewport coverage
- generated, local, or deployed environments being assessed
- explicit exclusions

Project-wide means all maintained user-facing reporting surfaces within the
agreed scope. It does not require inspecting every archived artifact when
representative coverage proves the same maintained behavior.

Review:

- landing pages
- static reports
- dashboards
- direct routes and deep links
- navigation paths
- growing historical views
- language and information architecture
- content hierarchy and visual design
- responsive behavior and overflow
- charts, tables, controls, and unavailable states
- representative wide and narrow layouts
- deployed behavior when hosted output is in scope

Describe the target reporting experience, not only isolated defects.

Identify content that should be removed, condensed, grouped, relocated, or
separated.

Convert supported findings into bounded follow-up packages. Do not prescribe one
giant cleanup change.

## Finding standard

Every finding must include:

- **Severity:** blocking or nonblocking
- **Classification**
- **Evidence**
- **Affected surface or files**
- **Problem**
- **Impact**
- **Smallest effective correction**

Use exact routes, screenshots, viewport conditions, controls, rendered values,
source files, runtime errors, or observed behavior as evidence.

Use `missing evidence` when a conclusion cannot be verified.

Do not present personal visual preference as a defect.

Useful classifications include:

- correctness defect
- language defect
- navigation problem
- information architecture problem
- reporting flow problem
- visual hierarchy or density problem
- responsive or overflow problem
- accessibility problem
- missing evidence
- optional polish

## Blocking standard

Treat a finding as blocking when it materially affects understanding or use.

Examples include:

- incorrect or misleading values
- runtime errors or unresolved modules
- broken controls or reactive updates
- empty or invalid default states
- inaccessible direct routes
- navigation traps
- leaked expressions or internal identifiers
- unreadable overlap or unusable overflow
- missing distinctions between unavailable, unknown, failed, and not applicable
- language that misrepresents certainty, safety, provenance, or meaning
- presentation that hides the primary information or prevents the intended
  action
- controls or navigation that cannot be operated through their intended input
  methods
- missing labels, focus behavior, or contrast that prevents understanding or use

Treat minor spacing, styling, density, and polish improvements as nonblocking
unless they materially affect comprehension, navigation, or usability.

## Validation

Validation must match the active mode and risk.

For implementation work, validate:

- representative production shaped data when chart density, table growth,
  history length, or responsive behavior depends on scale
- small deterministic fixtures alone are not sufficient visual review evidence
  in those cases
- use deterministic fixtures for correctness and representative data for visual
  review; record the scale and states inspected, then restore committed fixtures
  before final validation and commit
- affected source behavior
- generated production artifact
- browser behavior
- relevant wide and narrow layouts
- changed routes and controls
- unavailable and error states
- deployed output when required
- complete affected diff

Run focused application checks required by the change and applicable skills.

For read-only review, gather enough source, generated, deployed, browser, and
visual evidence to support each finding. Do not mutate files or GitHub state.

For documentation-only changes to this skill:

- inspect the complete diff
- confirm the guidance remains concise, general, and nonduplicative
- confirm the three operating modes remain distinct
- run `git diff --check`

Do not run unrelated application tests for documentation-only changes.

## Boundaries

Do not require a design system, component library, screenshot regression system,
multiple browser engines, exhaustive accessibility audit, or broad browser test
suite unless the active issue requires it.

Do not encode framework-specific recipes, current routes, selectors, commands,
or page layouts as permanent guidance.

Python export and query logic remains under `python-engineering`.

Public data exposure and publication security remain under
`security-engineering`.

GitHub operations remain under `github-workflow`.

Final issue conformance remains under `work-package-review`.

## Completion report

Report:

- result
- mode used
- surfaces or files changed or reviewed
- reporting flow and user journey assessed
- rendered and browser behavior implemented or inspected
- blocking findings
- nonblocking findings
- missing evidence
- validation or review evidence
- recommended bounded follow-up packages
- unresolved risks
