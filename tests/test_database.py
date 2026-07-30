from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pytest

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

EXPECTED_TABLES = {
    "forecast_hourly",
    "forecast_snapshots",
    "pipeline_runs",
    "source_results",
    "sst_hourly",
    "tide_events",
    "tide_phase_hourly",
    "tide_snapshots",
    "wave_hourly",
}
EXPECTED_SNAPSHOT_COLUMNS = {
    "snapshot_id",
    "run_id",
    "location_id",
    "captured_at",
    "raw_file_path",
    "model_selector",
    "request_latitude",
    "request_longitude",
    "returned_latitude",
    "returned_longitude",
}
EXPECTED_HOURLY_COLUMNS = {
    "snapshot_id",
    "location_id",
    "forecast_time",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation_probability",
    "precipitation",
}
EXPECTED_WAVE_COLUMNS = {
    "snapshot_id",
    "location_id",
    "forecast_time",
    "wave_height",
    "wave_direction",
    "wave_period",
}
EXPECTED_SST_COLUMNS = {
    "snapshot_id",
    "location_id",
    "forecast_time",
    "sea_surface_temperature",
}
EXPECTED_TIDE_SNAPSHOT_COLUMNS = {
    "snapshot_id",
    "station_id",
    "prediction_location",
    "relationship_type",
    "reference_station",
    "product",
    "interval",
    "datum",
    "time_zone",
    "units",
    "response_format",
    "request_begin_date",
    "request_end_date",
    "high_time_offset_minutes",
    "low_time_offset_minutes",
    "high_multiplier",
    "low_multiplier",
    "distance_km",
    "coastal_relationship",
    "known_limitation",
}
EXPECTED_TIDE_EVENT_COLUMNS = {
    "snapshot_id",
    "location_id",
    "event_time",
    "event_type",
    "predicted_water_level",
}
EXPECTED_TIDE_PHASE_COLUMNS = {
    "snapshot_id",
    "location_id",
    "forecast_time",
    "phase",
}
EXPECTED_SOURCE_RESULT_COLUMNS = {
    "run_id",
    "location_id",
    "source",
    "status",
    "detail",
    "recorded_at",
}


def snapshot_metadata(
    snapshot_id: str = "snapshot123",
    run_id: str = "run123",
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "location_id": "jennettes_pier",
        "captured_at": captured_at
        or datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc),
        "raw_file_path": f"data/test/raw/{snapshot_id}.json",
        "model_selector": "ncep_nbm_conus",
        "request_latitude": 35.9096355,
        "request_longitude": -75.5966537,
        "returned_latitude": 35.89557,
        "returned_longitude": -75.5936,
    }


def wave_snapshot_metadata(
    snapshot_id: str = "wave-snapshot123",
    run_id: str = "run123",
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "location_id": "fort_macon_ocean",
        "captured_at": captured_at
        or datetime(2026, 7, 28, 10, 6, tzinfo=timezone.utc),
        "raw_file_path": f"data/test/raw/{snapshot_id}.json",
        "model_selector": "meteofrance_wave",
        "request_latitude": 34.65,
        "request_longitude": -76.697,
        "returned_latitude": 34.625,
        "returned_longitude": -76.70833,
    }


def sst_snapshot_metadata(
    snapshot_id: str = "sst-snapshot123",
    run_id: str = "run123",
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "location_id": "fort_fisher",
        "captured_at": captured_at
        or datetime(2026, 7, 28, 10, 7, tzinfo=timezone.utc),
        "raw_file_path": f"data/test/raw/{snapshot_id}.json",
        "model_selector": "meteofrance_currents",
        "request_latitude": 33.93,
        "request_longitude": -77.9,
        "returned_latitude": 33.958336,
        "returned_longitude": -77.87499,
    }


def tide_snapshot_metadata(
    snapshot_id: str = "tide-snapshot123",
    run_id: str = "run123",
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "location_id": "jennettes_pier",
        "captured_at": captured_at
        or datetime(2026, 7, 28, 10, 8, tzinfo=timezone.utc),
        "raw_file_path": f"data/test/raw/{snapshot_id}.json",
    }


def tide_request_provenance() -> dict[str, Any]:
    return {
        "station": "8652226",
        "begin_date": "20260727",
        "end_date": "20260805",
        "product": "predictions",
        "interval": "hilo",
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "format": "json",
        "captured_at": datetime(
            2026,
            7,
            28,
            10,
            8,
            tzinfo=timezone.utc,
        ),
    }


def tide_relationship() -> dict[str, Any]:
    return {
        "prediction_location": "Jennettes Pier, Nags Head (ocean)",
        "station_id": "8652226",
        "relationship_type": "direct",
        "reference_station": "8651370",
        "high_time_offset_minutes": -5,
        "low_time_offset_minutes": 1,
        "high_multiplier": 1.04,
        "low_multiplier": 1.43,
        "distance_km": 0.448,
        "coastal_relationship": "Direct use at the Atlantic-facing pier",
        "known_limitation": (
            "Prediction behavior remains distinct from observed water levels"
        ),
    }


def atmospheric_payload(
    wind_speed: float = 10.0,
    wind_direction: float = 180.0,
    wind_gust: float = 15.0,
    precipitation_probability: float = 20.0,
    precipitation: float = 0.0,
) -> dict[str, Any]:
    return {
        "timezone": "GMT",
        "hourly": {
            "time": ["2026-07-29T12:00"],
            "wind_speed_10m": [wind_speed],
            "wind_direction_10m": [wind_direction],
            "wind_gusts_10m": [wind_gust],
            "precipitation_probability": [precipitation_probability],
            "precipitation": [precipitation],
        },
    }


def wave_payload(
    wave_height: float = 1.2,
    wave_direction: float = 135.0,
    wave_period: float = 8.0,
) -> dict[str, Any]:
    return {
        "timezone": "GMT",
        "hourly": {
            "time": ["2026-07-29T12:00"],
            "wave_height": [wave_height],
            "wave_direction": [wave_direction],
            "wave_period": [wave_period],
        },
    }


def sst_payload(
    sea_surface_temperature: float = 25.1,
) -> dict[str, Any]:
    return {
        "timezone": "GMT",
        "hourly": {
            "time": ["2026-07-29T12:00"],
            "sea_surface_temperature": [sea_surface_temperature],
        },
    }


def insert_run(
    database_path: Path,
    run_id: str = "run123",
    started_at: datetime | None = None,
) -> None:
    insert_pipeline_run(
        database_path=database_path,
        run_id=run_id,
        started_at=started_at
        or datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
    )


def test_initialize_database_creates_required_schema(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nested" / "forecast_ops.duckdb"

    initialize_database(database_path)

    assert database_path.exists()

    with duckdb.connect(str(database_path), read_only=True) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'main'
                    and table_type = 'BASE TABLE'
                """
            ).fetchall()
        }
        snapshot_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'forecast_snapshots'
                """
            ).fetchall()
        }
        hourly_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'forecast_hourly'
                """
            ).fetchall()
        }
        wave_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'wave_hourly'
                """
            ).fetchall()
        }
        sst_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'sst_hourly'
                """
            ).fetchall()
        }
        tide_snapshot_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'tide_snapshots'
                """
            ).fetchall()
        }
        tide_event_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'tide_events'
                """
            ).fetchall()
        }
        tide_phase_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'tide_phase_hourly'
                """
            ).fetchall()
        }
        source_result_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'source_results'
                """
            ).fetchall()
        }

    assert tables == EXPECTED_TABLES
    assert snapshot_columns == EXPECTED_SNAPSHOT_COLUMNS
    assert hourly_columns == EXPECTED_HOURLY_COLUMNS
    assert wave_columns == EXPECTED_WAVE_COLUMNS
    assert sst_columns == EXPECTED_SST_COLUMNS
    assert tide_snapshot_columns == EXPECTED_TIDE_SNAPSHOT_COLUMNS
    assert tide_event_columns == EXPECTED_TIDE_EVENT_COLUMNS
    assert tide_phase_columns == EXPECTED_TIDE_PHASE_COLUMNS
    assert source_result_columns == EXPECTED_SOURCE_RESULT_COLUMNS


def test_initialize_database_can_run_more_than_once(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"

    initialize_database(database_path)
    initialize_database(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        table_count = connection.execute(
            """
            select count(*)
            from information_schema.tables
            where table_schema = 'main'
                and table_type = 'BASE TABLE'
            """
        ).fetchone()

    assert table_count == (len(EXPECTED_TABLES),)


def test_forecast_hourly_rejects_duplicate_business_key(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    insert_forecast_snapshot(database_path, snapshot_metadata())
    payload = atmospheric_payload()

    insert_forecast_hourly(
        database_path,
        "snapshot123",
        "jennettes_pier",
        payload,
    )

    with pytest.raises(duckdb.ConstraintException):
        insert_forecast_hourly(
            database_path,
            "snapshot123",
            "jennettes_pier",
            payload,
        )


def test_insert_pipeline_run_and_snapshot_provenance(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)

    metadata = snapshot_metadata()
    insert_forecast_snapshot(database_path, metadata)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select status, rows_loaded
            from pipeline_runs
            where run_id = 'run123'
            """
        ).fetchone()
        snapshot = connection.execute(
            """
            select
                run_id,
                location_id,
                raw_file_path,
                model_selector,
                request_latitude,
                request_longitude,
                returned_latitude,
                returned_longitude
            from forecast_snapshots
            where snapshot_id = 'snapshot123'
            """
        ).fetchone()

    assert run == ("running", 0)
    assert snapshot == (
        "run123",
        "jennettes_pier",
        "data/test/raw/snapshot123.json",
        "ncep_nbm_conus",
        35.9096355,
        -75.5966537,
        35.89557,
        -75.5936,
    )


def test_complete_pipeline_run_updates_status(tmp_path: Path) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)

    complete_pipeline_run(
        database_path=database_path,
        run_id="run123",
        completed_at=datetime(2026, 7, 28, 10, 10, tzinfo=timezone.utc),
        status="success",
        rows_loaded=168,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute(
            """
            select status, rows_loaded, error_message
            from pipeline_runs
            where run_id = 'run123'
            """
        ).fetchone()

    assert result == ("success", 168, None)


def test_complete_pipeline_run_requires_existing_run(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)

    with pytest.raises(ValueError, match="pipeline run not found"):
        complete_pipeline_run(
            database_path=database_path,
            run_id="missing",
            completed_at=datetime(2026, 7, 28, 10, 10, tzinfo=timezone.utc),
            status="failed",
            rows_loaded=0,
            error_message="api request failed",
        )


def test_insert_forecast_hourly_stores_coastal_fields_in_utc(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    insert_forecast_snapshot(database_path, snapshot_metadata())

    payload = {
        "timezone": "GMT",
        "hourly": {
            "time": [
                "2026-07-29T12:00",
                "2026-07-29T13:00",
            ],
            "wind_speed_10m": [10.0, 11.0],
            "wind_direction_10m": [180.0, 190.0],
            "wind_gusts_10m": [15.0, 16.0],
            "precipitation_probability": [20.0, 30.0],
            "precipitation": [0.0, 0.4],
        },
    }

    rows_loaded = insert_forecast_hourly(
        database_path=database_path,
        snapshot_id="snapshot123",
        location_id="jennettes_pier",
        payload=payload,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                forecast_time,
                wind_speed_10m,
                wind_direction_10m,
                wind_gusts_10m,
                precipitation_probability,
                precipitation
            from forecast_hourly
            order by forecast_time
            """
        ).fetchall()

    assert rows_loaded == 2
    assert rows == [
        (
            datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc),
            10.0,
            180.0,
            15.0,
            20.0,
            0.0,
        ),
        (
            datetime(2026, 7, 29, 13, 0, tzinfo=timezone.utc),
            11.0,
            190.0,
            16.0,
            30.0,
            0.4,
        ),
    ]


def test_atmospheric_wave_and_sst_snapshot_provenance_remain_distinct(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    insert_forecast_snapshot(database_path, snapshot_metadata())
    insert_forecast_snapshot(database_path, wave_snapshot_metadata())
    insert_forecast_snapshot(database_path, sst_snapshot_metadata())

    with duckdb.connect(str(database_path), read_only=True) as connection:
        snapshots = connection.execute(
            """
            select
                snapshot_id,
                model_selector,
                request_latitude,
                request_longitude,
                returned_latitude,
                returned_longitude
            from forecast_snapshots
            order by snapshot_id
            """
        ).fetchall()

    assert snapshots == [
        (
            "snapshot123",
            "ncep_nbm_conus",
            35.9096355,
            -75.5966537,
            35.89557,
            -75.5936,
        ),
        (
            "sst-snapshot123",
            "meteofrance_currents",
            33.93,
            -77.9,
            33.958336,
            -77.87499,
        ),
        (
            "wave-snapshot123",
            "meteofrance_wave",
            34.65,
            -76.697,
            34.625,
            -76.70833,
        ),
    ]


def test_insert_sst_hourly_stores_values_in_utc(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    insert_forecast_snapshot(database_path, sst_snapshot_metadata())
    payload = {
        "timezone": "GMT",
        "hourly": {
            "time": [
                "2026-07-29T12:00",
                "2026-07-29T13:00",
            ],
            "sea_surface_temperature": [25.1, 25.4],
        },
    }

    rows_loaded = insert_sst_hourly(
        database_path=database_path,
        snapshot_id="sst-snapshot123",
        location_id="fort_fisher",
        payload=payload,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                forecast_time,
                sea_surface_temperature
            from sst_hourly
            order by forecast_time
            """
        ).fetchall()

    assert rows_loaded == 2
    assert rows == [
        (
            datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc),
            25.1,
        ),
        (
            datetime(2026, 7, 29, 13, 0, tzinfo=timezone.utc),
            25.4,
        ),
    ]


def test_insert_wave_hourly_stores_fields_in_utc(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    insert_forecast_snapshot(database_path, wave_snapshot_metadata())
    payload = {
        "timezone": "GMT",
        "hourly": {
            "time": [
                "2026-07-29T12:00",
                "2026-07-29T13:00",
            ],
            "wave_height": [1.2, 1.4],
            "wave_direction": [135.0, 145.0],
            "wave_period": [8.0, 9.0],
        },
    }

    rows_loaded = insert_wave_hourly(
        database_path=database_path,
        snapshot_id="wave-snapshot123",
        location_id="fort_macon_ocean",
        payload=payload,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                forecast_time,
                wave_height,
                wave_direction,
                wave_period
            from wave_hourly
            order by forecast_time
            """
        ).fetchall()

    assert rows_loaded == 2
    assert rows == [
        (
            datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc),
            1.2,
            135.0,
            8.0,
        ),
        (
            datetime(2026, 7, 29, 13, 0, tzinfo=timezone.utc),
            1.4,
            145.0,
            9.0,
        ),
    ]


def test_insert_forecast_hourly_rejects_mismatched_lengths(
    tmp_path: Path,
) -> None:
    payload = atmospheric_payload()
    payload["hourly"]["precipitation"] = []

    with pytest.raises(
        ValueError,
        match="hourly precipitation length must match hourly time length",
    ):
        insert_forecast_hourly(
            database_path=tmp_path / "forecast_ops.duckdb",
            snapshot_id="snapshot123",
            location_id="jennettes_pier",
            payload=payload,
        )


def test_insert_forecast_hourly_requires_hourly_mapping(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="forecast payload must contain an hourly mapping",
    ):
        insert_forecast_hourly(
            database_path=tmp_path / "forecast_ops.duckdb",
            snapshot_id="snapshot123",
            location_id="jennettes_pier",
            payload={},
        )


def test_insert_forecast_hourly_rejects_offset_aware_timestamps(
    tmp_path: Path,
) -> None:
    payload = atmospheric_payload()
    payload["hourly"]["time"] = ["2026-07-29T12:00+00:00"]

    with pytest.raises(
        ValueError,
        match="forecast payload hourly timestamps must be UTC-naive",
    ):
        insert_forecast_hourly(
            database_path=tmp_path / "forecast_ops.duckdb",
            snapshot_id="snapshot123",
            location_id="jennettes_pier",
            payload=payload,
        )


@pytest.mark.parametrize(
    ("source", "status", "detail"),
    [
        ("weather", "success", None),
        ("wave", "fetch_failed", "request timed out"),
        ("sst", "validation_failed", "missing hourly timestamps"),
    ],
)
def test_insert_source_result(
    tmp_path: Path,
    source: str,
    status: str,
    detail: str | None,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    recorded_at = datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc)
    initialize_database(database_path)
    insert_run(database_path)

    insert_source_result(
        database_path=database_path,
        run_id="run123",
        location_id="jennettes_pier",
        source=source,
        status=status,
        detail=detail,
        recorded_at=recorded_at,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute(
            """
            select source, status, detail, recorded_at
            from source_results
            where run_id = 'run123'
            """
        ).fetchone()

    assert result == (source, status, detail, recorded_at)


def test_insert_source_result_rejects_unsupported_status(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)

    with pytest.raises(ValueError, match="unsupported source result status"):
        insert_source_result(
            database_path=database_path,
            run_id="run123",
            location_id="jennettes_pier",
            source="weather",
            status="failed",
            detail="request failed",
            recorded_at=datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc),
        )


def test_source_results_enforce_one_result_per_run_location_and_source(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    result = {
        "database_path": database_path,
        "run_id": "run123",
        "location_id": "jennettes_pier",
        "source": "weather",
        "status": "success",
        "detail": None,
        "recorded_at": datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc),
    }

    insert_source_result(**result)

    with pytest.raises(duckdb.ConstraintException):
        insert_source_result(**result)


def test_initialize_database_preserves_source_results(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    insert_source_result(
        database_path=database_path,
        run_id="run123",
        location_id="jennettes_pier",
        source="weather",
        status="success",
        detail=None,
        recorded_at=datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc),
    )

    initialize_database(database_path)
    initialize_database(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute(
            """
            select run_id, location_id, source, status, detail
            from source_results
            """
        ).fetchone()

    assert result == ("run123", "jennettes_pier", "weather", "success", None)


def test_tide_snapshot_events_and_phase_preserve_distinct_provenance(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    insert_tide_snapshot(
        database_path,
        tide_snapshot_metadata(),
        tide_request_provenance(),
        tide_relationship(),
    )
    events = [
        {
            "event_time": datetime(
                2026,
                7,
                28,
                0,
                tzinfo=timezone.utc,
            ),
            "event_type": "low",
            "predicted_water_level": 0.1,
        },
        {
            "event_time": datetime(
                2026,
                7,
                28,
                6,
                tzinfo=timezone.utc,
            ),
            "event_type": "high",
            "predicted_water_level": 1.2,
        },
    ]
    phases = [
        {
            "forecast_time": datetime(
                2026,
                7,
                28,
                0,
                tzinfo=timezone.utc,
            ),
            "phase": "rising",
        }
    ]

    event_count = insert_tide_events(
        database_path,
        "tide-snapshot123",
        "jennettes_pier",
        events,
    )
    phase_count = insert_tide_phase_hourly(
        database_path,
        "tide-snapshot123",
        "jennettes_pier",
        phases,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        snapshot = connection.execute(
            """
            select
                snapshots.model_selector,
                snapshots.request_latitude,
                tide.station_id,
                tide.product,
                tide.interval,
                tide.datum,
                tide.time_zone,
                tide.units,
                tide.response_format,
                tide.relationship_type,
                tide.reference_station,
                tide.request_begin_date,
                tide.request_end_date
            from forecast_snapshots as snapshots
            inner join tide_snapshots as tide
                on snapshots.snapshot_id = tide.snapshot_id
            """
        ).fetchone()
        stored_events = connection.execute(
            """
            select event_time, event_type, predicted_water_level
            from tide_events
            order by event_time
            """
        ).fetchall()
        stored_phases = connection.execute(
            """
            select forecast_time, phase
            from tide_phase_hourly
            """
        ).fetchall()

    assert event_count == 2
    assert phase_count == 1
    assert snapshot == (
        None,
        None,
        "8652226",
        "predictions",
        "hilo",
        "MLLW",
        "gmt",
        "metric",
        "json",
        "direct",
        "8651370",
        datetime(2026, 7, 27).date(),
        datetime(2026, 8, 5).date(),
    )
    assert stored_events == [
        (
            datetime(2026, 7, 28, 0, tzinfo=timezone.utc),
            "low",
            0.1,
        ),
        (
            datetime(2026, 7, 28, 6, tzinfo=timezone.utc),
            "high",
            1.2,
        ),
    ]
    assert stored_phases == [
        (
            datetime(2026, 7, 28, 0, tzinfo=timezone.utc),
            "rising",
        )
    ]
