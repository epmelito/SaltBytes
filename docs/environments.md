# Environments
ForecastOps uses dev, test, and prod to separate development, automated validation, and production-style execution.

The same application code runs in every environment. Configuration controls the input source, output paths, and validation behavior.

## dev
Development uses the live API with limited scope.

Typical settings:
- one or two locations
- shorter forecast horizon
- local development database
- local raw data path
- verbose logging

The purpose is fast feedback while building and debugging.

## test
Test uses fixed JSON fixtures instead of the live API.

Typical settings:
- controlled input data
- temporary DuckDB database
- repeatable expected results
- no dependency on network availability
- stricter assertions

The purpose is deterministic automated testing.

## prod
Prod uses the live API with the full configured scope.

Typical settings:
- all configured locations
- full forecast horizon
- separate production-style database
- separate raw data path
- standard logging
- stricter failure behavior

The first release runs prod locally. It does not deploy to cloud infrastructure.

## Promotion flow
Code moves through the following path:
1. create a feature branch
2. run and validate changes in dev
3. open a pull request
4. run automated tests
5. merge approved changes into `main`
6. run the production-style workflow from the tested version

The project does not use separate long-lived branches for dev, test, and prod. That would duplicate code paths and create unnecessary drift.

## Configuration boundaries
Environment configuration may change:
- input source
- location scope
- forecast horizon
- database path
- raw data path
- logging level
- validation thresholds

Environment configuration must not change core transformation logic.