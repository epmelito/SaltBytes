# Sample failure evidence

## Pipeline run metadata

- Run ID: `sample-run-001`
- Environment: `dev`
- Status: `failed`
- Rows loaded: `0`
- Error message: `forecast quality checks failed for prague: hourly_temperature_2m_count_matches`

## Quality results

| Location | Check | Status | Details |
| --- | --- | --- | --- |
| prague | hourly_section_exists | passed | hourly section found |
| prague | hourly_time_not_empty | passed | 48 timestamps found |
| prague | hourly_temperature_2m_exists | passed | field found |
| prague | hourly_temperature_2m_count_matches | failed | 47 values for 48 timestamps |
| prague | hourly_precipitation_probability_count_matches | passed | 48 values for 48 timestamps |

## Structured logs

```text
2026-07-28 20:00:00 INFO forecast_ops.pipeline pipeline started run_id=sample-run-001 environment=dev locations=2
2026-07-28 20:00:00 INFO forecast_ops.pipeline forecast processing started run_id=sample-run-001 location=prague
2026-07-28 20:00:01 ERROR forecast_ops.pipeline pipeline failed run_id=sample-run-001 environment=dev
ValueError: forecast quality checks failed for prague: hourly_temperature_2m_count_matches
```

# Expected review

# ForecastOps failure review

## Run summary
- Run ID: `sample-run-001`
- Environment: `dev`
- Status: `failed`
- Affected location: `prague`
- Last successful stage: API response received and payload structure validated
- Failed stage: payload quality checks

## Confirmed evidence
- The payload contained 48 forecast timestamps.
- The `temperature_2m` field contained 47 values.
- The temperature record count check failed.
- No forecast rows were loaded.

## Likely cause
The API payload contained an incomplete `temperature_2m` value list for the requested timestamps. This is a data quality failure rather than a database or storage failure.

## Recommended next check
Review the failed quality result for `sample-run-001` to identify the mismatched
field counts. Confirm the failed run in `pipeline_runs`. Do not look for a raw
snapshot: the payload was not stored because quality checks run before snapshot
writing.
