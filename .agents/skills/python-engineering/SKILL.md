---
name: python-engineering
description: Implement Python changes in ForecastOps involving application code, external data access, configuration, validation, persistence, orchestration, operational scripts, or tests. Use for bounded implementation that must preserve interfaces, data integrity, reliability, security, and maintainability.
---

# Python engineering

## Responsibility

Complete bounded Python engineering work accurately and efficiently.

Inspect the relevant repository context, implement the smallest complete
solution, validate it proportionately, fix failures introduced by the change or
required for issue conformance, and return one concise completion report.

## Autonomous workflow

When requirements are clear:

1. Read the active issue and applicable repository guidance.
2. Inspect the minimum repository context needed to understand the affected
   contract. Expand into callers, configuration, schemas, tests, or
   documentation only when the change or uncertainty requires it.
3. Identify the smallest complete implementation that satisfies the confirmed
   requirement.
4. Implement the change using existing project patterns unless evidence
   justifies changing them.
5. Add or update focused tests and directly affected documentation.
6. Use focused checks while developing. Run repository-required broad checks
   once after the implementation stabilizes.
7. Fix failures introduced by the change or required for issue conformance.
   Rerun affected checks first, and rerun broad checks only when later changes
   could invalidate the recorded result.
8. Return one completion report.

Discover available repository facts before asking the user. Do not request
approval for routine inspection, focused implementation, tests, validation, or
fixing errors introduced by the change.

Do not rerun unchanged broad checks merely to reconfirm them. Report unrelated
pre-existing failures instead of absorbing them into the work package.

## Engineering rules

- Verify function signatures, configuration keys, data fields, schemas, paths,
  names, and downstream references across every affected boundary.
- Treat external responses, files, configuration, and user-controlled values as
  untrusted inputs. Validate required structure, types, nullability, timestamps,
  units, completeness, and provider-specific behavior where relevant.
- Trace required failure behavior end to end before placing validation.
  Distinguish application-invalid configuration from source-result-invalid
  input; when requirements call for retained run or source evidence,
  affected-work isolation, or independent continuation, do not rely only on
  pre-run rejection. Verify each supported entry point affected by the required
  failure contract, including command-line and direct function use where
  applicable, with focused tests of the complete failure path.
- Preserve required raw evidence, source identity, retrieval metadata,
  provenance, stable keys, and revision history.
- Design writes and orchestration for safe reruns. Check duplicate processing,
  partial writes, transaction boundaries, cleanup, and independent failure
  handling against the confirmed requirements.
- Use explicit failure behavior. Preserve useful exception context and do not
  silently substitute data, ignore failures, or introduce fallback behavior
  without authorization.
- Keep responsibilities and control flow clear. Add abstraction only for
  demonstrated duplication, variation, isolation, or scale.
- Prefer existing dependencies and the standard library. Add a dependency only
  when its value exceeds its maintenance, security, and context cost.
- Protect credentials and sensitive values. Do not hardcode secrets, expose
  them in logs, disable transport security casually, or broaden permissions
  without need.
- Consider batching, memory use, network calls, database round trips,
  serialization, concurrency, and caching only when expected scale or observed
  behavior makes them relevant.
- Write tests that verify meaningful behavior, including applicable failure,
  boundary, mismatch, rerun, and partial-result cases. Do not add tests that
  merely execute code without proving an outcome.

## Human decision gates

Stop and request input only when an unresolved choice materially affects:

- product behavior or approved scope
- architecture or durable interfaces
- data integrity or destructive behavior
- security, credentials, permissions, or sensitive external writes
- a meaningful tradeoff with no accepted repository decision
- work that would exceed the authorized issue

State the decision needed, the available evidence, and the smallest viable
options. Do not silently choose.

## Boundaries

- Do not broaden the task into unrelated refactoring or architecture work.
- Do not introduce frameworks, retries, caching, asynchronous execution,
  parallelism, dependency injection, strict typing tools, coverage thresholds,
  or new project structure without demonstrated need.
- Do not duplicate instructions already maintained in `AGENTS.md`.
- Do not claim success when required validation has not passed or cannot be
  verified.

## Completion report

Report only:

- result
- files changed
- implemented behavior
- validation performed and results
- external actions taken
- unresolved decisions, risks, or blocked checks

Keep the report concise and do not narrate routine commands.
