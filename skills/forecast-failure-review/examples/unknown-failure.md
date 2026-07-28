# Sample failure evidence

## Pipeline run metadata

- Run ID: `sample-run-002`
- Environment: `prod`
- Status: `failed`
- Rows loaded: `168`
- Error message: `unexpected pipeline failure`

## Quality results

| Location | Check | Status | Details |
| --- | --- | --- | --- |
| prague | all configured checks | passed | 168 rows validated |

## Structured logs

```text
2026-07-28 21:00:00 INFO forecast_ops.pipeline pipeline started run_id=sample-run-002 environment=prod locations=2
2026-07-28 21:00:00 INFO forecast_ops.pipeline forecast processing started run_id=sample-run-002 location=prague
2026-07-28 21:00:01 INFO forecast_ops.pipeline quality checks passed run_id=sample-run-002 location=prague checks=5
2026-07-28 21:00:01 INFO forecast_ops.pipeline forecast processing completed run_id=sample-run-002 location=prague rows=168
2026-07-28 21:00:01 INFO forecast_ops.pipeline forecast processing started run_id=sample-run-002 location=ocracoke
2026-07-28 21:00:02 ERROR forecast_ops.pipeline pipeline failed run_id=sample-run-002 environment=prod
RuntimeError: unexpected pipeline failure
```

# Expected review

# ForecastOps failure review

## Run summary
- Run ID: `sample-run-002`
- Environment: `prod`
- Status: `failed`
- Affected location: `ocracoke`
- Last successful stage: Prague forecast records loaded
- Failed stage: unknown stage during Ocracoke processing

## Confirmed evidence
- Prague completed successfully and loaded 168 rows.
- Ocracoke processing started.
- No Ocracoke quality result or completion log was recorded.
- The exception message does not identify the failed operation.

## Likely cause
The failure category is `unknown`. The available evidence only shows that the failure occurred after Ocracoke processing started and before its quality checks completed.

## Recommended next check
Review the complete exception traceback for `sample-run-002` and identify the first ForecastOps function shown above the error.

## Missing evidence
- complete traceback
- Ocracoke API response status
- Ocracoke quality results
- raw snapshot write status