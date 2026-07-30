import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forecast_ops.api import (
    SST_API,
    TIDE_API,
    WAVE_API,
    WEATHER_API,
    build_tide_params,
    fetch_forecast,
    fetch_sst_forecast,
    fetch_tide_predictions,
    fetch_wave_forecast,
)
from forecast_ops.database import (
    complete_pipeline_run,
    initialize_database,
    insert_forecast_hourly,
    insert_forecast_snapshot,
    insert_pipeline_run,
    insert_source_result,
    insert_sst_hourly,
    insert_tide_events,
    insert_tide_phase_hourly,
    insert_tide_snapshot,
    insert_wave_hourly,
)
from forecast_ops.quality import (
    build_tide_forecast_times,
    derive_tide_phases,
    normalize_tide_events,
    run_payload_quality_checks,
    run_tide_quality_checks,
)
from forecast_ops.storage import create_run_id, write_raw_snapshot

logger = logging.getLogger(__name__)

# run the configured forecast pipeline for every location
def run_pipeline(config: dict[str, Any]) -> dict[str, Any]:
    locations = config["locations"]
    storage_config = config["storage"]

    database_path = Path(storage_config["database_path"])
    raw_data_path = Path(storage_config["raw_data_path"])

    run_id = create_run_id()
    started_at = datetime.now(timezone.utc)
    rows_loaded = 0
    snapshots_written = 0
    location_failures: list[str] = []

    logger.info(
        "pipeline started run_id=%s locations=%s",
        run_id,
        len(locations),
    )

    initialize_database(database_path)

    insert_pipeline_run(
        database_path=database_path,
        run_id=run_id,
        started_at=started_at,
    )

    try:
        tide_forecast_times = build_tide_forecast_times(
            started_at,
            TIDE_API["forecast_days"],
        )

        for location in locations:
            weather_request_coordinate = location["weather"][
                "request_coordinate"
            ]

            logger.info(
                "weather processing started run_id=%s location=%s",
                run_id,
                location["id"],
            )

            weather_payload = None
            weather_quality_results: list[dict[str, Any]] = []
            try:
                weather_payload = fetch_forecast(
                    location=location,
                    api_config=WEATHER_API,
                )
            except Exception as error:
                location_failure = (
                    f"weather API fetch failed for {location['id']}: {error}"
                )
                location_failures.append(location_failure)
                logger.exception(
                    "weather API fetch failed run_id=%s location=%s",
                    run_id,
                    location["id"],
                )
                insert_source_result(
                    database_path=database_path,
                    run_id=run_id,
                    location_id=location["id"],
                    source="weather",
                    status="fetch_failed",
                    detail=str(error),
                    recorded_at=datetime.now(timezone.utc),
                )

            if weather_payload is not None:
                weather_quality_results = run_payload_quality_checks(
                    payload=weather_payload,
                    expected_hourly_fields=WEATHER_API["hourly_fields"],
                    model_selector=WEATHER_API["model"],
                    expected_returned_coordinate=location["weather"][
                        "expected_returned_coordinate"
                    ],
                    source_label="weather",
                )

            failed_weather_checks = [
                quality_result
                for quality_result in weather_quality_results
                if quality_result["status"] == "fail"
            ]

            if weather_payload is not None and failed_weather_checks:
                failed_check_names = ", ".join(
                    str(quality_result["check_name"])
                    for quality_result in failed_weather_checks
                )
                location_failure = (
                    f"weather quality checks failed for {location['id']}: "
                    f"{failed_check_names}"
                )
                location_failures.append(location_failure)
                logger.error(
                    "weather quality checks failed run_id=%s location=%s "
                    "checks=%s",
                    run_id,
                    location["id"],
                    failed_check_names,
                )
                insert_source_result(
                    database_path=database_path,
                    run_id=run_id,
                    location_id=location["id"],
                    source="weather",
                    status="validation_failed",
                    detail=failed_check_names,
                    recorded_at=datetime.now(timezone.utc),
                )
            elif weather_payload is not None:
                insert_source_result(
                    database_path=database_path,
                    run_id=run_id,
                    location_id=location["id"],
                    source="weather",
                    status="success",
                    detail=None,
                    recorded_at=datetime.now(timezone.utc),
                )
                logger.info(
                    "weather quality checks passed run_id=%s location=%s "
                    "checks=%s",
                    run_id,
                    location["id"],
                    len(weather_quality_results),
                )

                weather_metadata = write_raw_snapshot(
                    payload=weather_payload,
                    location_id=location["id"],
                    raw_data_path=raw_data_path,
                    run_id=run_id,
                )
                weather_metadata.update(
                    {
                        "model_selector": WEATHER_API["model"],
                        "request_latitude": weather_request_coordinate[
                            "latitude"
                        ],
                        "request_longitude": weather_request_coordinate[
                            "longitude"
                        ],
                        "returned_latitude": weather_payload["latitude"],
                        "returned_longitude": weather_payload["longitude"],
                    }
                )

                insert_forecast_snapshot(
                    database_path=database_path,
                    metadata=weather_metadata,
                )

                weather_rows_loaded = insert_forecast_hourly(
                    database_path=database_path,
                    snapshot_id=weather_metadata["snapshot_id"],
                    location_id=location["id"],
                    payload=weather_payload,
                )

                rows_loaded += weather_rows_loaded
                snapshots_written += 1

                logger.info(
                    "weather processing completed run_id=%s location=%s "
                    "rows=%s",
                    run_id,
                    location["id"],
                    weather_rows_loaded,
                )

            logger.info(
                "wave processing started run_id=%s location=%s",
                run_id,
                location["id"],
            )

            wave_request_coordinate = location["wave"]["request_coordinate"]
            wave_payload = None
            wave_quality_results: list[dict[str, Any]] = []
            try:
                wave_payload = fetch_wave_forecast(
                    location=location,
                    wave_api_config=WAVE_API,
                )
            except Exception as error:
                location_failure = (
                    f"wave API fetch failed for {location['id']}: {error}"
                )
                location_failures.append(location_failure)
                logger.exception(
                    "wave API fetch failed run_id=%s location=%s",
                    run_id,
                    location["id"],
                )
                insert_source_result(
                    database_path=database_path,
                    run_id=run_id,
                    location_id=location["id"],
                    source="wave",
                    status="fetch_failed",
                    detail=str(error),
                    recorded_at=datetime.now(timezone.utc),
                )

            if wave_payload is not None:
                wave_quality_results = run_payload_quality_checks(
                    payload=wave_payload,
                    expected_hourly_fields=WAVE_API["hourly_fields"],
                    model_selector=WAVE_API["model"],
                    expected_returned_coordinate=location["wave"][
                        "expected_returned_coordinate"
                    ],
                    expected_model_selector="meteofrance_wave",
                    source_label="wave",
                )

            failed_wave_checks = [
                quality_result
                for quality_result in wave_quality_results
                if quality_result["status"] == "fail"
            ]

            if wave_payload is not None and failed_wave_checks:
                failed_check_names = ", ".join(
                    str(quality_result["check_name"])
                    for quality_result in failed_wave_checks
                )
                location_failure = (
                    f"wave quality checks failed for {location['id']}: "
                    f"{failed_check_names}"
                )
                location_failures.append(location_failure)
                logger.error(
                    "wave quality checks failed run_id=%s location=%s checks=%s",
                    run_id,
                    location["id"],
                    failed_check_names,
                )
                insert_source_result(
                    database_path=database_path,
                    run_id=run_id,
                    location_id=location["id"],
                    source="wave",
                    status="validation_failed",
                    detail=failed_check_names,
                    recorded_at=datetime.now(timezone.utc),
                )
            elif wave_payload is not None:
                insert_source_result(
                    database_path=database_path,
                    run_id=run_id,
                    location_id=location["id"],
                    source="wave",
                    status="success",
                    detail=None,
                    recorded_at=datetime.now(timezone.utc),
                )
                logger.info(
                    "wave quality checks passed run_id=%s location=%s checks=%s",
                    run_id,
                    location["id"],
                    len(wave_quality_results),
                )

                wave_metadata = write_raw_snapshot(
                    payload=wave_payload,
                    location_id=location["id"],
                    raw_data_path=raw_data_path,
                    run_id=run_id,
                )
                wave_metadata.update(
                    {
                        "model_selector": WAVE_API["model"],
                        "request_latitude": wave_request_coordinate["latitude"],
                        "request_longitude": wave_request_coordinate[
                            "longitude"
                        ],
                        "returned_latitude": wave_payload["latitude"],
                        "returned_longitude": wave_payload["longitude"],
                    }
                )

                insert_forecast_snapshot(
                    database_path=database_path,
                    metadata=wave_metadata,
                )

                wave_rows_loaded = insert_wave_hourly(
                    database_path=database_path,
                    snapshot_id=wave_metadata["snapshot_id"],
                    location_id=location["id"],
                    payload=wave_payload,
                )

                rows_loaded += wave_rows_loaded
                snapshots_written += 1

                logger.info(
                    "wave processing completed run_id=%s location=%s rows=%s",
                    run_id,
                    location["id"],
                    wave_rows_loaded,
                )

            logger.info(
                "sst processing started run_id=%s location=%s",
                run_id,
                location["id"],
            )

            if location["sst"]:
                sst_config = location["sst"]
                sst_request_coordinate = sst_config["request_coordinate"]
                sst_payload = None
                sst_quality_results: list[dict[str, Any]] = []
                try:
                    sst_payload = fetch_sst_forecast(
                        location=location,
                        sst_api_config=SST_API,
                    )
                except Exception as error:
                    location_failure = (
                        f"sst API fetch failed for {location['id']}: {error}"
                    )
                    location_failures.append(location_failure)
                    logger.exception(
                        "sst API fetch failed run_id=%s location=%s",
                        run_id,
                        location["id"],
                    )
                    insert_source_result(
                        database_path=database_path,
                        run_id=run_id,
                        location_id=location["id"],
                        source="sst",
                        status="fetch_failed",
                        detail=str(error),
                        recorded_at=datetime.now(timezone.utc),
                    )

                if sst_payload is not None:
                    sst_quality_results = run_payload_quality_checks(
                        payload=sst_payload,
                    expected_hourly_fields=SST_API["hourly_fields"],
                    model_selector=SST_API["model"],
                        expected_returned_coordinate=sst_config[
                            "expected_returned_coordinate"
                        ],
                        expected_model_selector="meteofrance_currents",
                        source_label="sst",
                    )

                failed_sst_checks = [
                    quality_result
                    for quality_result in sst_quality_results
                    if quality_result["status"] == "fail"
                ]

                if sst_payload is not None and failed_sst_checks:
                    failed_check_names = ", ".join(
                        str(quality_result["check_name"])
                        for quality_result in failed_sst_checks
                    )
                    location_failure = (
                        f"sst quality checks failed for {location['id']}: "
                        f"{failed_check_names}"
                    )
                    location_failures.append(location_failure)
                    logger.error(
                        "sst quality checks failed run_id=%s location=%s "
                        "checks=%s",
                        run_id,
                        location["id"],
                        failed_check_names,
                    )
                    insert_source_result(
                        database_path=database_path,
                        run_id=run_id,
                        location_id=location["id"],
                        source="sst",
                        status="validation_failed",
                        detail=failed_check_names,
                        recorded_at=datetime.now(timezone.utc),
                    )
                elif sst_payload is not None:
                    insert_source_result(
                        database_path=database_path,
                        run_id=run_id,
                        location_id=location["id"],
                        source="sst",
                        status="success",
                        detail=None,
                        recorded_at=datetime.now(timezone.utc),
                    )
                    logger.info(
                        "sst quality checks passed run_id=%s location=%s "
                        "checks=%s",
                        run_id,
                        location["id"],
                        len(sst_quality_results),
                    )

                    sst_metadata = write_raw_snapshot(
                        payload=sst_payload,
                        location_id=location["id"],
                        raw_data_path=raw_data_path,
                        run_id=run_id,
                    )
                    sst_metadata.update(
                        {
                            "model_selector": SST_API["model"],
                            "request_latitude": sst_request_coordinate[
                                "latitude"
                            ],
                            "request_longitude": sst_request_coordinate[
                                "longitude"
                            ],
                            "returned_latitude": sst_payload["latitude"],
                            "returned_longitude": sst_payload["longitude"],
                        }
                    )

                    insert_forecast_snapshot(
                        database_path=database_path,
                        metadata=sst_metadata,
                    )

                    sst_rows_loaded = insert_sst_hourly(
                        database_path=database_path,
                        snapshot_id=sst_metadata["snapshot_id"],
                        location_id=location["id"],
                        payload=sst_payload,
                    )

                    rows_loaded += sst_rows_loaded
                    snapshots_written += 1

                    logger.info(
                        "sst processing completed run_id=%s location=%s "
                        "rows=%s",
                        run_id,
                        location["id"],
                        sst_rows_loaded,
                    )

            logger.info(
                "tide processing started run_id=%s location=%s",
                run_id,
                location["id"],
            )

            if location["tide"]:
                captured_at = datetime.now(timezone.utc)
                tide_params = build_tide_params(
                    location=location,
                    tide_api_config=TIDE_API,
                    forecast_start=tide_forecast_times[0],
                )
                request_provenance = {
                    **tide_params,
                    "captured_at": captured_at,
                }
                tide_payload = None
                tide_quality_results: list[dict[str, Any]] = []
                try:
                    tide_payload = fetch_tide_predictions(
                        tide_api_config=TIDE_API,
                        params=tide_params,
                    )
                except Exception as error:
                    location_failure = (
                        f"tide API fetch failed for {location['id']}: {error}"
                    )
                    location_failures.append(location_failure)
                    logger.exception(
                        "tide API fetch failed run_id=%s location=%s",
                        run_id,
                        location["id"],
                    )
                    insert_source_result(
                        database_path=database_path,
                        run_id=run_id,
                        location_id=location["id"],
                        source="tide",
                        status="fetch_failed",
                        detail=str(error),
                        recorded_at=datetime.now(timezone.utc),
                    )

                if tide_payload is not None:
                    tide_quality_results = run_tide_quality_checks(
                        payload=tide_payload,
                        request_provenance=request_provenance,
                        forecast_times=tide_forecast_times,
                    )

                failed_tide_checks = [
                    quality_result
                    for quality_result in tide_quality_results
                    if quality_result["status"] == "fail"
                ]

                if tide_payload is not None and failed_tide_checks:
                    failed_check_names = ", ".join(
                        str(quality_result["check_name"])
                        for quality_result in failed_tide_checks
                    )
                    location_failure = (
                        f"tide quality checks failed for {location['id']}: "
                        f"{failed_check_names}"
                    )
                    location_failures.append(location_failure)
                    logger.error(
                        "tide quality checks failed run_id=%s location=%s "
                        "checks=%s",
                        run_id,
                        location["id"],
                        failed_check_names,
                    )
                    insert_source_result(
                        database_path=database_path,
                        run_id=run_id,
                        location_id=location["id"],
                        source="tide",
                        status="validation_failed",
                        detail=failed_check_names,
                        recorded_at=datetime.now(timezone.utc),
                    )
                elif tide_payload is not None:
                    insert_source_result(
                        database_path=database_path,
                        run_id=run_id,
                        location_id=location["id"],
                        source="tide",
                        status="success",
                        detail=None,
                        recorded_at=datetime.now(timezone.utc),
                    )
                    tide_events = normalize_tide_events(tide_payload)
                    tide_phases = derive_tide_phases(
                        tide_events,
                        tide_forecast_times,
                    )
                    tide_metadata = write_raw_snapshot(
                        payload=tide_payload,
                        location_id=location["id"],
                        raw_data_path=raw_data_path,
                        run_id=run_id,
                        captured_at=captured_at,
                    )
                    insert_tide_snapshot(
                        database_path=database_path,
                        metadata=tide_metadata,
                        request_provenance=request_provenance,
                        relationship=location["tide"],
                    )
                    tide_event_rows = insert_tide_events(
                        database_path=database_path,
                        snapshot_id=tide_metadata["snapshot_id"],
                        location_id=location["id"],
                        events=tide_events,
                    )
                    tide_phase_rows = insert_tide_phase_hourly(
                        database_path=database_path,
                        snapshot_id=tide_metadata["snapshot_id"],
                        location_id=location["id"],
                        phases=tide_phases,
                    )

                    rows_loaded += tide_event_rows + tide_phase_rows
                    snapshots_written += 1

                    logger.info(
                        "tide processing completed run_id=%s location=%s "
                        "events=%s phases=%s",
                        run_id,
                        location["id"],
                        tide_event_rows,
                        tide_phase_rows,
                    )

        if location_failures:
            raise ValueError("; ".join(location_failures))

    except Exception as error:
        logger.exception(
            "pipeline failed run_id=%s",
            run_id,
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
        "pipeline completed run_id=%s snapshots=%s rows=%s",
        run_id,
        snapshots_written,
        rows_loaded,
    )

    return {
        "run_id": run_id,
        "status": "success",
        "started_at": started_at,
        "completed_at": completed_at,
        "snapshots_written": snapshots_written,
        "rows_loaded": rows_loaded,
    }
