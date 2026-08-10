---
name: documentation-governance-review
description: Review bounded SaltBytes documentation for unclear authority, duplication, stale or speculative content, poor scalability, and unnecessary maintenance burden.
---

# Documentation governance review

## Responsibility

Perform a focused, read-only review and recommend the smallest correction needed
to keep documentation authoritative, current, proportional, and maintainable.

Preserve distinct decisions, contracts, boundaries, research evidence,
operating procedures, unresolved decisions, and temporary handoffs. Prefer code,
tests, configuration, schemas, and generated output for discoverable behavior or
mutable state.

## Triggers and inputs

Use this skill when a permanent document is proposed, documentation overlaps or
conflicts, a material project boundary changes, a major roadmap stage completes,
completion of a meaningful work package may leave authoritative documentation
stale, or a deliberate documentation review is requested.

Do not use it automatically for routine code changes.

Require a clear target: a proposed document, documentation diff, revision range,
bounded document set, or work package and its directly affected documentation.
Stop when unrelated changes make the target ambiguous.

## Workflow

1. Read the applicable `AGENTS.md` and the request defining the target.
2. Inspect only enough repository context to understand the affected authority,
   contract, behavior, or history.
3. Discover the repository's actual authority relationships.
4. For each document, determine:
   - its distinct purpose, audience, and authoritative content
   - whether its purpose, status, authority, and lifecycle statements remain true
   - whether content with different update triggers is combined
   - whether temporal language or completed-stage state is stale
   - whether rules, decisions, requirements, status, or discoverable behavior
     are duplicated elsewhere
   - whether speculative or temporary state is presented as approved or current
   - whether it should be shortened, referenced, merged, archived, or deleted
5. For growable sets such as locations, species, providers, metrics, routes, or
   scoring factors, distinguish one authoritative current inventory from frozen
   history, research evidence, examples, fixtures, and bounded scope.
6. Flag copied mutable lists, hardcoded counts, or update fan out likely to drift.
7. Keep README and index files navigational rather than duplicate authorities.
8. Identify conflicts rather than silently reconciling them.
9. Order findings by maintenance risk and stop without editing files.

Chat history is not authoritative when it conflicts with the repository.

## Assessment rules

Classify each actionable finding as `shorten`, `reference instead`, `merge`,
`archive`, `delete`, or `conflict requiring decision`.

Do not use `keep` as a finding. Put justified documents under
`No change required`.

Use severities:

- `blocking`: false or conflicting authority is likely to cause incorrect work
- `important`: duplication, stale scope, speculation, update fan out, or
  maintenance burden is likely to worsen
- `minor`: worthwhile cleanup with low immediate risk

Use verdicts:

- `Pass`: no actionable findings
- `Pass with cleanup`: only important or minor findings
- `Decision required`: an authority conflict cannot be resolved from repository
  evidence
- `Fail`: documentation materially misstates or duplicates an authoritative
  contract and the correction is clear

Ignore editorial preferences unless they create ambiguity or maintenance risk.

## Review rules

- Give each permanent document one authoritative purpose.
- Keep content with similar update triggers together.
- Separate durable boundaries, current status, temporary handoffs, and history.
- Do not update historical decisions to track later additions.
- Preserve nonobvious invariants, contracts, failure behavior, and procedures.
- Prefer references over copied substance.
- Do not add a document when an existing authority can hold the content cleanly.
- Treat deletion, consolidation, and archiving as valid outcomes.
- A review that only adds documentation is suspect.

## Boundaries

- Do not edit files or perform a general code or pull request review.
- Do not rewrite the documentation tree.
- Do not create registries, manifests, ownership matrices, review calendars,
  dependency graphs, or a separate documentation roadmap.
- Do not require dates, owners, lifecycle metadata, or documentation changes for
  every work package.
- Do not introduce generators or synchronization without demonstrated need.
- Do not resolve product, architecture, or authority conflicts without an
  accepted decision.
- Do not invent findings or promote optional cleanup into requirements.

## Output

Use exactly:

```markdown
# Documentation governance review

## Verdict
Pass | Pass with cleanup | Decision required | Fail

## Findings
None.

### [severity] Brief finding title

- **Documents:**
- **Classification:** shorten | reference instead | merge | archive | delete |
  conflict requiring decision
- **Problem:**
- **Why it matters:**
- **Smallest effective correction:**

## Documents reviewed

- ...

## No change required

- ...
```

Use `None.` for empty sections.
