---
name: security-engineering
description: Implement or review bounded SaltBytes changes involving credentials, authentication, authorization, workflow permissions, untrusted input, dependencies, infrastructure, destructive operations, or canonical state security.
---

# Security engineering

## Responsibility

Complete bounded security-sensitive work using the smallest safe solution.

Identify credible exploit or failure paths, preserve accepted security and data
contracts, implement authorized fixes, validate the affected behavior, and
return one concise report.

Do not turn routine engineering work into a general security audit.

## Workflow

1. Read the active issue and applicable repository guidance.
2. Inspect the minimum context needed to identify affected assets, identities,
   trust boundaries, inputs, permissions, and destructive operations.
3. Trace each suspected risk from its source to a concrete impact.
4. Separate confirmed vulnerabilities from optional hardening.
5. Implement the smallest complete fix within scope.
6. Add focused tests or validation for the affected security behavior.
7. Return one completion report.

Discover repository facts before asking the user. Stop only when a genuine
security, architecture, permission, cost, or destructive action decision
remains unresolved.

## Security rules

- Treat external input, configuration, files, workflow values, and API responses
  as untrusted where they cross a security boundary.
- Prevent untrusted values from reaching commands, paths, queries,
  deserialization, or privileged operations without appropriate validation.
- Use the narrowest practical identity, permission, token, and resource scope.
- Do not hardcode or expose credentials, tokens, keys, connection strings, or
  other sensitive values.
- Do not weaken authentication, authorization, transport security, or failure
  behavior for convenience.
- Treat third party workflow code and new dependencies as supply chain risk.
- Protect canonical state from unsafe fallback, partial publication,
  conflicting writers, unintended overwrite, and deletion.
- Require explicit authorization for destructive actions or privilege
  expansion.
- Tie every finding to a credible exploit or failure path. Generic security
  advice is not a finding.

## SaltBytes hosted ingestion

When work affects Azure hosted ingestion, read and enforce the active issue and
accepted project decisions.

Preserve identity based authentication, least privilege access, private
authenticated storage, minimal workflow permissions, immutable raw state, safe
canonical state publication, concurrency protection, and secret free logging.

Do not introduce excluded enterprise controls unless the active issue requires
them.

## Assessment

Treat a finding as blocking only when evidence shows a credible path to
unauthorized access, credential exposure, attacker controlled execution,
privilege expansion, protected data exposure, or corruption, deletion, or
unsafe replacement of canonical state.

Treat defense in depth improvements without a demonstrated exploit path as
nonblocking.

## Boundaries

- Do not broaden the task into a repository wide security audit.
- Do not add compliance frameworks, penetration testing frameworks, security
  registries, mandatory threat model documents, or speculative architecture.
- Do not duplicate general implementation or GitHub workflow responsibilities.
- Do not claim a vulnerability or mitigation without evidence.
- Do not claim success when required validation has not passed.

## Completion report

Report only:

- result
- files changed
- risks assessed
- implemented behavior
- validation and results
- unresolved decisions or risks
