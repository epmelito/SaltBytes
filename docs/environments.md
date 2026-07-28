# Environments
ForecastOps uses dev, test, and prod to separate development, automated validation, and production-style execution.

The same application code runs in every environment. Current configuration
controls locations, API request settings, output paths, and logging level. It
does not select a fixture input mode or environment-specific quality
thresholds.

## dev
Development uses the live API with a two-day forecast horizon.

Current settings:
- Prague and Ocracoke
- two-day forecast horizon
- local development database and raw data paths
- debug logging

The purpose is fast feedback while building and debugging.

## test
The test configuration uses the same live API endpoint and two-day forecast
horizon as dev, with separate local test paths.

Automated tests do not rely on that live input. They replace forecast fetching
with controlled responses or fixed JSON fixtures and use temporary storage.
This substitution is implemented in the test harness, not selected by
`config/test.yml`.

The environment name identifies test runs, while pytest provides deterministic
input and assertions.

## prod
Prod uses the live API with a seven-day forecast horizon.

Current settings:
- Prague and Ocracoke
- seven-day forecast horizon
- separate production-style database and raw data paths
- info logging

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
- location scope
- API endpoint
- forecast horizon
- requested hourly fields, subject to required-field validation
- database path
- raw data path
- logging level

Environment configuration must not change core transformation logic.
