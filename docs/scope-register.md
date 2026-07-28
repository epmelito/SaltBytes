# Scope register

## Purpose

This register separates verified current capability, approved future direction,
deferred decisions, and exclusions. It controls the scope of active work
without replacing the product charter or roadmap.

## Scope states

| State | Meaning |
| --- | --- |
| Current | Verified as implemented in the repository |
| Approved future | Part of the approved product direction but not necessarily implemented |
| Deferred | A recognized choice that has not been decided |
| Excluded | Outside the approved product boundary |
| Drift | Existing documentation differs from verified implementation |

## Current implementation

The current repository provides:

- a local Python weather forecast pipeline
- `dev`, `test`, and `prod` local YAML configurations
- Open-Meteo hourly forecast ingestion
- immutable raw JSON snapshots for payloads that pass pipeline quality checks
- normalized hourly weather forecasts in DuckDB
- pipeline run, snapshot, and quality metadata
- forecast revision calculations for implemented weather fields
- structured logging and manual inspection scripts
- pytest coverage and GitHub Actions validation
- a bounded, diagnostic forecast failure review skill

The configured locations are currently Prague and Ocracoke, North Carolina.
Implemented forecast fields are air temperature, precipitation probability,
and wind speed. These facts describe the current foundation and do not define
the future coastal location set or fishing-condition requirements.

## Initial governance work package

The initial governance work package created:

- `AGENTS.md`
- `docs/project-charter.md`
- `docs/roadmap.md`
- `docs/scope-register.md`
- `docs/decisions/README.md`
- `docs/handoffs/current.md`

Pull request #13 introduced all six governance files after content review and a
successful required `test and lint` check. A follow-up correction aligned the
lifecycle records with the completed state.

The initial governance work package and roadmap stage 1 are complete.

## Completed documentation reconciliation work package

Issue #15 authorized the roadmap stage 2 documentation reconciliation work
package.

The work package modified only:

- `readme.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/environments.md`
- `docs/scope-register.md`
- `docs/roadmap.md`
- `docs/handoffs/current.md`

It reconciled verified documentation drift without changing application
behavior, repository skills, product direction, deferred decisions, or roadmap
stages 3 through 9. A follow-up lifecycle-state correction aligned the
governance records with the completed work package.

The documentation reconciliation work package and roadmap stage 2 are
complete. Roadmap stage 3 is next in sequence but remains unauthorized and
unstarted.

## Approved future scope

Approved future scope is grouped into:

- North Carolina coastal condition data and retained forecast history
- deterministic scoring, fishing-window ranking, and consumer-ready data
- a reusable personal Azure portfolio platform and public display
- bounded AI-assisted engineering workflows

The full durable product direction is defined in the
[project charter](project-charter.md). These categories approve capability
areas, not their deferred product or architecture details.

Delivery order is controlled by the [roadmap](roadmap.md).

## Exclusions

Excluded scope is defined by the
[product boundaries in the charter](project-charter.md#product-boundaries).
It covers fishing-success or safety-authority claims, opaque scoring, an
initial real-time commercial service, exhaustive first-release coverage or
variables, and product feature implementation before the governance lifecycle
above is complete.

## Deferred decisions

The following decisions are intentionally open:

| Topic | Status |
| --- | --- |
| Exact coastal locations | Deferred |
| Marine and tide providers | Deferred |
| Final source authority rules | Deferred |
| Score variables and weights | Deferred |
| Species-specific or general scoring | Deferred |
| Inshore, surf, pier, offshore, or inlet segmentation | Deferred |
| Forecast and observation retention periods | Deferred |
| Publication format | Deferred |
| Dashboard or API design | Deferred |
| Scheduling frequency | Deferred |
| Azure service selection | Deferred |
| Infrastructure as code approach | Deferred |
| Service levels | Deferred |
| Cost limits | Deferred |
| Final success metrics | Deferred |

These topics should remain open until a roadmap stage requires a durable choice.
Accepted choices should be recorded through the
[decision process](decisions/README.md).

## Known documentation drift

One verified documentation inconsistency remains unresolved:

- The failure-review example recommends inspecting a raw response for a failed
  quality check, although the current pipeline does not store a payload that
  fails those checks. Issue #15 does not authorize changes under `skills/`, so
  this correction requires a separate authorized work package.

The other drift recorded for issue #15 was resolved by the completed
documentation reconciliation work package and is no longer treated as
unresolved.

## Scope changes

A proposed change should:

1. identify the charter outcome it supports
2. identify the affected roadmap stage
3. state whether it changes current, future, deferred, or excluded scope
4. use a decision record when a durable choice or tradeoff requires rationale
5. update this register after approval

The [current handoff](handoffs/current.md) may report scope status but cannot
approve a scope change.
