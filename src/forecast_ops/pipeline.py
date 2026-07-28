import logging
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

logger = logging.getLogger(__name__)

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

    logger.info(
        "pipeline started run_id=%s environment=%s locations=%s",
        run_id,
        environment,
        len(locations),
    )

    initialize_database(database_path)

    insert_pipeline_run(
        database_path=database_path,
        run_id=run_id,
        environment=environment,
        started_at=started_at,
    )

    try:
        for location in locations:
            logger.info(
                "forecast processing started run_id=%s location=%s",
                run_id,
                location["id"],
            )

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

            logger.info(
                "quality checks passed run_id=%s location=%s checks=%s",
                run_id,
                location["id"],
                len(quality_results),
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

            location_rows_loaded = insert_forecast_hourly(
                database_path=database_path,
                snapshot_id=metadata["snapshot_id"],
                location_id=location["id"],
                payload=payload,
            )

            rows_loaded += location_rows_loaded
            snapshots_written += 1

            logger.info(
                "forecast processing completed run_id=%s location=%s rows=%s",
                run_id,
                location["id"],
                location_rows_loaded,
            )

    except Exception as error:
        logger.exception(
            "pipeline failed run_id=%s environment=%s",
            run_id,
            environment,
        )

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

    logger.info(
        "pipeline completed run_id=%s environment=%s snapshots=%s rows=%s",
        run_id,
        environment,
        snapshots_written,
        rows_loaded,
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