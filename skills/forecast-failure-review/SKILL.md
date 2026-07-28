---
name: forecast-failure-review
description: Review a failed ForecastOps pipeline run using run metadata, quality results, and logs, then produce a concise diagnostic summary without changing data or rerunning the pipeline.
---

# Forecast failure review

Review evidence from a failed ForecastOps pipeline execution and produce a concise operational summary.

## Purpose

Use this skill when a ForecastOps pipeline run has failed and the user wants help understanding:

- what failed
- where it failed
- what evidence supports the conclusion
- what should be checked next

The skill is diagnostic only.

## Required inputs

Use only the evidence provided by the user or retrieved from the ForecastOps repository and generated runtime data.

The review should use as many of these inputs as are available:

- pipeline run metadata
- failed quality results
- structured pipeline logs
- environment name
- run ID
- affected location
- exception message
- row and snapshot counts
- relevant configuration values

Do not invent missing values.

## Workflow

1. Identify the run ID and environment.
2. Confirm the final run status.
3. Identify the last successful pipeline stage.
4. Identify the first recorded failure.
5. Review failed quality checks and exception details.
6. Compare the evidence across metadata, logs, and quality results.
7. State the most likely failure category.
8. Recommend the smallest useful next check.
9. Separate confirmed facts from interpretation.
10. State which evidence is missing when a conclusion cannot be reached.

## Failure categories

Classify the failure using one primary category:

- configuration
- API connection
- API response
- data quality
- raw storage
- database write
- timezone conversion
- unknown

Use `unknown` when the available evidence does not support a more specific category.

## Output format

Use this structure:

```markdown
# ForecastOps failure review

## Run summary
- Run ID:
- Environment:
- Status:
- Affected location:
- Last successful stage:
- Failed stage:

## Confirmed evidence
- ...

## Likely cause
...

## Recommended next check
...

## Missing evidence
- ...
```

Keep the result concise. Omit `Missing evidence` when the available evidence is sufficient.

## Rules

- Do not modify source data.
- Do not write to DuckDB.
- Do not rerun the pipeline.
- Do not change configuration.
- Do not make deployment decisions.
- Do not claim a root cause without supporting evidence.
- Do not treat warnings as failures unless the pipeline recorded them as failures.
- Do not expose credentials, tokens, or secret values.
- Do not include unrelated HTTP client debug messages.
- Prefer one recommended next check over a long troubleshooting list.