from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forecast_ops.api import fetch_forecast
from forecast_ops.database import (
    complete_pipeline_run,
    initialize_database,
    insert_forecast_hourly,
    insert_forecast_snapshot,
    insert_pipeline_run,
    insert_quality_result,
)
from forecast_ops.quality import run_payload_quality_checks
from forecast_ops.storage import create_run_id, write_raw_snapshot


# run the configured forecast pipeline for every location
def run_pipeline(config: dict[str, Any]) -> dict[str, Any]:
    environment = config["environment"]
    locations = config["locations"]
    api_config = config["api"]
    storage_config = config["storage"]

    database_path = Path(storage_config["database_path"])
    raw_data_path = Path(storage_config["raw_data_path"])

    run_id = create_run_id()
    started_at = datetime.now(timezone.utc)
    rows_loaded = 0
    snapshots_written = 0

    initialize_database(database_path)

    insert_pipeline_run(
        database_path=database_path,
        run_id=run_id,
        environment=environment,
        started_at=started_at,
    )

    try:
        for location in locations:
            payload = fetch_forecast(
                location=location,
                api_config=api_config,
            )

            quality_results = run_payload_quality_checks(
                payload=payload,
                expected_hourly_fields=api_config["hourly_fields"],
            )

            for quality_result in quality_results:
                insert_quality_result(
                    database_path=database_path,
                    run_id=run_id,
                    check_name=f"{location['id']}:{quality_result['check_name']}",
                    status=str(quality_result["status"]),
                    observed_value=str(quality_result["observed_value"]),
                    expected_value=str(quality_result["expected_value"]),
                    checked_at=quality_result["checked_at"],
                )

            failed_checks = [
                quality_result
                for quality_result in quality_results
                if quality_result["status"] == "fail"
            ]

            if failed_checks:
                failed_check_names = ", ".join(
                    str(quality_result["check_name"])
                    for quality_result in failed_checks
                )
                raise ValueError(
                    f"forecast quality checks failed for {location['id']}: "
                    f"{failed_check_names}"
                )

            metadata = write_raw_snapshot(
                payload=payload,
                location_id=location["id"],
                raw_data_path=raw_data_path,
                run_id=run_id,
            )

            insert_forecast_snapshot(
                database_path=database_path,
                metadata=metadata,
            )

            rows_loaded += insert_forecast_hourly(
                database_path=database_path,
                snapshot_id=metadata["snapshot_id"],
                location_id=location["id"],
                payload=payload,
            )

            snapshots_written += 1

    except Exception as error:
        complete_pipeline_run(
            database_path=database_path,
            run_id=run_id,
            completed_at=datetime.now(timezone.utc),
            status="failed",
            rows_loaded=rows_loaded,
            error_message=str(error),
        )
        raise

    completed_at = datetime.now(timezone.utc)

    complete_pipeline_run(
        database_path=database_path,
        run_id=run_id,
        completed_at=completed_at,
        status="success",
        rows_loaded=rows_loaded,
    )

    return {
        "run_id": run_id,
        "environment": environment,
        "status": "success",
        "started_at": started_at,
        "completed_at": completed_at,
        "snapshots_written": snapshots_written,
        "rows_loaded": rows_loaded,
    }