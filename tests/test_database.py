from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pytest

import saltbytes.database as database
from saltbytes.database import (
    SourcePersistenceError,
    complete_pipeline_run,
    initialize_database,
    insert_forecast_hourly,
    insert_forecast_snapshot,
    insert_pipeline_run,
    insert_run_locations,
    insert_source_result,
    insert_sst_hourly,
    insert_tide_events,
    insert_tide_phase_hourly,
    insert_tide_snapshot,
    insert_wave_hourly,
    persist_source_success,
)

EXPECTED_TABLES = {
    "cloud_cover_hourly",
    "forecast_hourly",
    "forecast_snapshots",
    "fishing_observation_assertions",
    "fishing_observation_reports",
    "fishing_observation_retrievals",
    "fishing_observation_review_candidates",
    "fishing_observation_ingestion_attempts",
    "fishing_observation_review_candidate_patterns",
    "fishing_observation_review_patterns",
    "pipeline_runs",
    "run_locations",
    "run_location_solar_context",
    "solar_context_hourly",
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
    database_path = tmp_path / "nested" / "saltbytes.duckdb"

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
    database_path = tmp_path / "saltbytes.duckdb"

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


def test_optional_cloud_cover_preserves_weather_rows_and_availability(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    metadata = snapshot_metadata(snapshot_id="cloud-weather")
    insert_forecast_snapshot(database_path, metadata)
    payload = atmospheric_payload()
    payload["hourly"]["cloud_cover"] = [25.0, None, "invalid"]
    payload["hourly"]["time"] = [
        "2026-07-29T12:00",
        "2026-07-29T13:00",
        "2026-07-29T14:00",
    ]
    for field_name in (
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "precipitation_probability",
        "precipitation",
    ):
        payload["hourly"][field_name] = payload["hourly"][field_name] * 3

    assert insert_forecast_hourly(database_path, "cloud-weather", "jennettes_pier", payload) == 3

    with duckdb.connect(str(database_path), read_only=True) as connection:
        cloud_rows = connection.execute(
            "select cloud_cover from cloud_cover_hourly order by forecast_time"
        ).fetchall()

    assert cloud_rows == [(25.0,), (None,), (None,)]


def test_forecast_hourly_rejects_duplicate_business_key(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
            database_path=tmp_path / "saltbytes.duckdb",
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
            database_path=tmp_path / "saltbytes.duckdb",
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
            database_path=tmp_path / "saltbytes.duckdb",
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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


def test_persist_source_success_rolls_back_partial_weather_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    insert_run(database_path)

    monkeypatch.setattr(
        database,
        "insert_forecast_hourly",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("normalized rows unavailable")
        ),
    )

    with pytest.raises(SourcePersistenceError, match="normalized rows"):
        persist_source_success(
            database_path=database_path,
            run_id="run123",
            location_id="jennettes_pier",
            source="weather",
            metadata=snapshot_metadata(),
            payload=atmospheric_payload(),
            recorded_at=datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc),
        )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        counts = connection.execute(
            """
            select
                (select count(*) from forecast_snapshots),
                (select count(*) from forecast_hourly),
                (select count(*) from source_results)
            """
        ).fetchone()

    assert counts == (0, 0, 0)


def test_initialize_database_migrates_existing_source_result_statuses(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            create table pipeline_runs (
                run_id varchar primary key,
                started_at timestamptz not null,
                completed_at timestamptz,
                status varchar not null,
                rows_loaded integer not null default 0,
                error_message varchar
            )
            """
        )
        connection.execute(
            """
            create table source_results (
                run_id varchar not null,
                location_id varchar not null,
                source varchar not null,
                status varchar not null check (
                    status in ('success', 'fetch_failed', 'validation_failed')
                ),
                detail varchar,
                recorded_at timestamptz not null,
                primary key (run_id, location_id, source),
                foreign key (run_id) references pipeline_runs(run_id)
            )
            """
        )
        connection.execute(
            "insert into pipeline_runs values ('run123', ?, null, 'failed', 0, null)",
            [datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc)],
        )
        connection.execute(
            """
            insert into source_results values
            ('run123', 'jennettes_pier', 'weather', 'success', null, ?)
            """,
            [datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc)],
        )

    initialize_database(database_path)
    insert_source_result(
        database_path=database_path,
        run_id="run123",
        location_id="jennettes_pier",
        source="wave",
        status="persistence_failed",
        detail="normalized rows: unavailable",
        recorded_at=datetime(2026, 7, 28, 10, 6, tzinfo=timezone.utc),
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        results = connection.execute(
            "select source, status from source_results order by source"
        ).fetchall()
        connection.execute("select * from analysis_ready_features_hourly").fetchall()

    assert results == [("wave", "persistence_failed"), ("weather", "success")]


def test_source_results_enforce_one_result_per_run_location_and_source(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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
    database_path = tmp_path / "saltbytes.duckdb"
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


def test_coastal_conditions_hourly_keeps_exact_run_and_hour_boundaries(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    hour = datetime(2026, 7, 29, 12, tzinfo=timezone.utc)
    later_hour = datetime(2026, 7, 29, 13, tzinfo=timezone.utc)
    sst_hour = datetime(2026, 7, 29, 14, tzinfo=timezone.utc)
    tide_hour = datetime(2026, 7, 29, 15, tzinfo=timezone.utc)
    initialize_database(database_path)
    insert_run(database_path, "run-one")
    insert_run(database_path, "run-two")

    for snapshot_id, model_selector in (
        ("weather-one", "ncep_nbm_conus"),
        ("wave-one", "meteofrance_wave"),
        ("sst-one", "meteofrance_currents"),
        ("weather-two", "ncep_nbm_conus"),
    ):
        metadata = snapshot_metadata(snapshot_id=snapshot_id, run_id="run-one")
        if snapshot_id == "weather-two":
            metadata["run_id"] = "run-two"
        metadata["model_selector"] = model_selector
        insert_forecast_snapshot(database_path, metadata)

    tide_metadata = tide_snapshot_metadata(
        snapshot_id="tide-one",
        run_id="run-one",
    )
    insert_tide_snapshot(
        database_path,
        tide_metadata,
        tide_request_provenance(),
        tide_relationship(),
    )

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into forecast_hourly values (?, 'jennettes_pier', ?, 20, 10, 180, 15, 0)
            """,
            [("weather-one", hour), ("weather-two", hour)],
        )
        connection.executemany(
            """
            insert into wave_hourly values (?, 'jennettes_pier', ?, 1.2, 135, 8)
            """,
            [("wave-one", hour), ("wave-one", later_hour)],
        )
        connection.executemany(
            """
            insert into sst_hourly values (?, 'jennettes_pier', ?, 25.1)
            """,
            [("sst-one", hour), ("sst-one", sst_hour)],
        )
        connection.executemany(
            """
            insert into tide_phase_hourly values (?, 'jennettes_pier', ?, 'rising')
            """,
            [("tide-one", hour), ("tide-one", tide_hour)],
        )
        connection.executemany(
            """
            insert into source_results values (?, 'jennettes_pier', ?, ?, null, ?)
            """,
            [
                ("run-one", source, "success", hour)
                for source in ("weather", "wave", "sst", "tide")
            ]
            + [
                ("run-two", "weather", "success", hour),
                ("run-two", "wave", "fetch_failed", hour),
                ("run-two", "sst", "validation_failed", hour),
                ("run-two", "tide", "fetch_failed", hour),
            ],
        )

    initialize_database(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                run_id,
                forecast_time,
                weather_snapshot_id,
                wave_snapshot_id,
                sst_snapshot_id,
                tide_snapshot_id,
                wind_speed_10m,
                wave_height,
                sea_surface_temperature,
                tide_phase,
                weather_status,
                wave_status,
                sst_status,
                tide_status
            from coastal_conditions_hourly
            order by run_id, forecast_time
            """
        ).fetchall()

    assert rows == [
        (
            "run-one", hour, "weather-one", "wave-one", "sst-one", "tide-one",
            10.0, 1.2, 25.1, "rising", "success", "success", "success", "success",
        ),
        (
            "run-one", later_hour, None, "wave-one", None, None,
            None, 1.2, None, None, "success", "success", "success", "success",
        ),
        (
            "run-one", sst_hour, None, None, "sst-one", None,
            None, None, 25.1, None, "success", "success", "success", "success",
        ),
        (
            "run-one", tide_hour, None, None, None, "tide-one",
            None, None, None, "rising", "success", "success", "success", "success",
        ),
        (
            "run-two", hour, "weather-two", None, None, None,
            10.0, None, None, None, "success", "fetch_failed", "validation_failed", "fetch_failed",
        ),
    ]


def test_tide_state_hourly_derives_bracketing_extrema(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    low_time = datetime(2026, 7, 29, 0, tzinfo=timezone.utc)
    middle_time = datetime(2026, 7, 29, 3, tzinfo=timezone.utc)
    high_time = datetime(2026, 7, 29, 6, tzinfo=timezone.utc)
    later_time = datetime(2026, 7, 29, 9, tzinfo=timezone.utc)
    next_low_time = datetime(2026, 7, 29, 12, tzinfo=timezone.utc)

    initialize_database(database_path)
    insert_run(database_path)
    insert_tide_snapshot(
        database_path,
        tide_snapshot_metadata(),
        tide_request_provenance(),
        tide_relationship(),
    )
    insert_tide_events(
        database_path,
        "tide-snapshot123",
        "jennettes_pier",
        [
            {
                "event_time": low_time,
                "event_type": "low",
                "predicted_water_level": 0.0,
            },
            {
                "event_time": high_time,
                "event_type": "high",
                "predicted_water_level": 1.0,
            },
            {
                "event_time": next_low_time,
                "event_type": "low",
                "predicted_water_level": 0.25,
            },
        ],
    )
    insert_tide_phase_hourly(
        database_path,
        "tide-snapshot123",
        "jennettes_pier",
        [
            {"forecast_time": low_time, "phase": "rising"},
            {"forecast_time": middle_time, "phase": "rising"},
            {"forecast_time": high_time, "phase": "falling"},
            {"forecast_time": later_time, "phase": "falling"},
        ],
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                forecast_time,
                phase,
                previous_extremum_time,
                previous_extremum_type,
                previous_predicted_water_level,
                next_extremum_time,
                next_extremum_type,
                next_predicted_water_level,
                minutes_since_previous_extremum,
                minutes_until_next_extremum,
                predicted_tidal_range
            from tide_state_hourly
            order by forecast_time
            """
        ).fetchall()

    assert rows == [
        (
            low_time,
            "rising",
            low_time,
            "low",
            0.0,
            high_time,
            "high",
            1.0,
            0,
            360,
            1.0,
        ),
        (
            middle_time,
            "rising",
            low_time,
            "low",
            0.0,
            high_time,
            "high",
            1.0,
            180,
            180,
            1.0,
        ),
        (
            high_time,
            "falling",
            high_time,
            "high",
            1.0,
            next_low_time,
            "low",
            0.25,
            0,
            360,
            0.75,
        ),
        (
            later_time,
            "falling",
            high_time,
            "high",
            1.0,
            next_low_time,
            "low",
            0.25,
            180,
            180,
            0.75,
        ),
    ]


def test_tide_state_hourly_isolates_snapshots_and_missing_pairs(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    low_time = datetime(2026, 7, 29, 0, tzinfo=timezone.utc)
    forecast_time = datetime(2026, 7, 29, 3, tzinfo=timezone.utc)
    high_time = datetime(2026, 7, 29, 6, tzinfo=timezone.utc)

    initialize_database(database_path)

    for run_id in ("run-a", "run-b", "run-c"):
        insert_run(database_path, run_id)

    for snapshot_id, run_id in (
        ("tide-a", "run-a"),
        ("tide-b", "run-b"),
        ("tide-c", "run-c"),
    ):
        insert_tide_snapshot(
            database_path,
            tide_snapshot_metadata(
                snapshot_id=snapshot_id,
                run_id=run_id,
            ),
            tide_request_provenance(),
            tide_relationship(),
        )

    for snapshot_id, low_level, high_level in (
        ("tide-a", 0.0, 1.0),
        ("tide-b", 10.0, 20.0),
    ):
        insert_tide_events(
            database_path,
            snapshot_id,
            "jennettes_pier",
            [
                {
                    "event_time": low_time,
                    "event_type": "low",
                    "predicted_water_level": low_level,
                },
                {
                    "event_time": high_time,
                    "event_type": "high",
                    "predicted_water_level": high_level,
                },
            ],
        )

    insert_tide_events(
        database_path,
        "tide-c",
        "jennettes_pier",
        [
            {
                "event_time": low_time,
                "event_type": "low",
                "predicted_water_level": 5.0,
            }
        ],
    )

    for snapshot_id in ("tide-a", "tide-b", "tide-c"):
        insert_tide_phase_hourly(
            database_path,
            snapshot_id,
            "jennettes_pier",
            [{"forecast_time": forecast_time, "phase": "rising"}],
        )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                snapshot_id,
                phase,
                previous_predicted_water_level,
                next_predicted_water_level,
                predicted_tidal_range
            from tide_state_hourly
            order by snapshot_id
            """
        ).fetchall()

    assert rows == [
        ("tide-a", "rising", 0.0, 1.0, 1.0),
        ("tide-b", "rising", 10.0, 20.0, 10.0),
        ("tide-c", "rising", None, None, None),
    ]


def test_coastal_conditions_hourly_exposes_tide_state_once(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    hour = datetime(2026, 7, 29, 12, tzinfo=timezone.utc)
    previous_time = datetime(2026, 7, 29, 6, tzinfo=timezone.utc)
    next_time = datetime(2026, 7, 29, 18, tzinfo=timezone.utc)

    initialize_database(database_path)
    insert_run(database_path, "run-one")
    insert_run(database_path, "run-two")

    insert_tide_snapshot(
        database_path,
        tide_snapshot_metadata(
            snapshot_id="tide-one",
            run_id="run-one",
        ),
        tide_request_provenance(),
        tide_relationship(),
    )
    insert_tide_events(
        database_path,
        "tide-one",
        "jennettes_pier",
        [
            {
                "event_time": previous_time,
                "event_type": "low",
                "predicted_water_level": 0.0,
            },
            {
                "event_time": next_time,
                "event_type": "high",
                "predicted_water_level": 1.0,
            },
        ],
    )
    insert_tide_phase_hourly(
        database_path,
        "tide-one",
        "jennettes_pier",
        [{"forecast_time": hour, "phase": "rising"}],
    )

    insert_forecast_snapshot(
        database_path,
        snapshot_metadata(
            snapshot_id="weather-two",
            run_id="run-two",
        ),
    )
    insert_forecast_hourly(
        database_path,
        "weather-two",
        "jennettes_pier",
        atmospheric_payload(),
    )

    insert_source_result(
        database_path,
        "run-one",
        "jennettes_pier",
        "tide",
        "success",
        None,
        hour,
    )
    insert_source_result(
        database_path,
        "run-two",
        "jennettes_pier",
        "tide",
        "fetch_failed",
        "request timed out",
        hour,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                run_id,
                tide_snapshot_id,
                tide_phase,
                tide_previous_extremum_time,
                tide_previous_extremum_type,
                tide_previous_predicted_water_level,
                tide_next_extremum_time,
                tide_next_extremum_type,
                tide_next_predicted_water_level,
                tide_minutes_since_previous_extremum,
                tide_minutes_until_next_extremum,
                tide_predicted_range,
                tide_status
            from coastal_conditions_hourly
            order by run_id
            """
        ).fetchall()

    assert rows == [
        (
            "run-one",
            "tide-one",
            "rising",
            previous_time,
            "low",
            0.0,
            next_time,
            "high",
            1.0,
            360,
            360,
            1.0,
            "success",
        ),
        (
            "run-two",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "fetch_failed",
        ),
    ]

def orientation_location(
    location_id: str = "jennettes_pier",
    shore_normal: float = 75.0,
    fishing_context: str = "surf",
    pier_azimuth: float | None = None,
) -> dict[str, Any]:
    return {
        "id": location_id,
        "fishing_context": fishing_context,
        "orientation": {
            "shore_normal_azimuth_degrees": shore_normal,
            "pier_seaward_azimuth_degrees": pier_azimuth,
            "orientation_method": "manual satellite review",
            "orientation_source": "reviewed satellite image",
            "orientation_reviewed_at": "2026-08-01",
            "orientation_limitation": "local shoreline segment only",
        },
    }


def test_run_locations_store_complete_reference_frame(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    insert_run(database_path)
    location = orientation_location(
        fishing_context="pier",
        pier_azimuth=70.0,
    )

    insert_run_locations(database_path, "run123", [location])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'run_locations'
                """
            ).fetchall()
        }
        row = connection.execute(
            """
            select
                run_id,
                location_id,
                fishing_context,
                shore_normal_azimuth_degrees,
                pier_seaward_azimuth_degrees,
                orientation_method,
                orientation_source,
                orientation_reviewed_at,
                orientation_limitation
            from run_locations
            """
        ).fetchone()

    assert columns == {
        "run_id",
        "location_id",
        "fishing_context",
        "shore_normal_azimuth_degrees",
        "pier_seaward_azimuth_degrees",
        "orientation_method",
        "orientation_source",
        "orientation_reviewed_at",
        "orientation_limitation",
    }
    assert row == (
        "run123",
        "jennettes_pier",
        "pier",
        75.0,
        70.0,
        "manual satellite review",
        "reviewed satellite image",
        datetime(2026, 8, 1).date(),
        "local shoreline segment only",
    )

    with pytest.raises(duckdb.ConstraintException):
        insert_run_locations(database_path, "run123", [location])


@pytest.mark.parametrize(
    ("shore_normal", "direction", "expected_angle"),
    [
        (0.0, 0.0, 0.0),
        (0.0, 360.0, 0.0),
        (0.0, 90.0, 90.0),
        (0.0, 180.0, -180.0),
        (10.0, 350.0, -20.0),
        (350.0, 10.0, 20.0),
    ],
)
def test_coastal_conditions_hourly_derives_signed_site_relative_angles(
    tmp_path: Path,
    shore_normal: float,
    direction: float,
    expected_angle: float,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    location_id = "test_location"
    initialize_database(database_path)
    insert_run(database_path)
    insert_run_locations(
        database_path,
        "run123",
        [
            orientation_location(
                location_id=location_id,
                shore_normal=shore_normal,
            )
        ],
    )

    weather_metadata = snapshot_metadata(
        snapshot_id="weather-angle",
        run_id="run123",
    )
    weather_metadata["location_id"] = location_id
    wave_metadata = wave_snapshot_metadata(
        snapshot_id="wave-angle",
        run_id="run123",
    )
    wave_metadata["location_id"] = location_id
    insert_forecast_snapshot(database_path, weather_metadata)
    insert_forecast_snapshot(database_path, wave_metadata)
    insert_forecast_hourly(
        database_path,
        "weather-angle",
        location_id,
        atmospheric_payload(wind_direction=direction),
    )
    insert_wave_hourly(
        database_path,
        "wave-angle",
        location_id,
        wave_payload(wave_direction=direction),
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        row = connection.execute(
            """
            select
                shore_normal_azimuth_degrees,
                wind_to_shore_angle_degrees,
                wave_to_shore_angle_degrees
            from coastal_conditions_hourly
            """
        ).fetchone()

    assert row == (
        shore_normal,
        expected_angle,
        expected_angle,
    )


def test_coastal_conditions_hourly_retains_historical_and_missing_values(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    insert_run(database_path, "historical-run")
    historical_metadata = snapshot_metadata(
        snapshot_id="historical-weather",
        run_id="historical-run",
    )
    insert_forecast_snapshot(database_path, historical_metadata)
    insert_forecast_hourly(
        database_path,
        "historical-weather",
        "jennettes_pier",
        atmospheric_payload(wind_direction=75.0),
    )

    insert_run(database_path, "current-run")
    insert_run_locations(
        database_path,
        "current-run",
        [
            orientation_location(
                location_id="jennettes_pier",
                shore_normal=75.0,
            )
        ],
    )
    current_metadata = snapshot_metadata(
        snapshot_id="current-weather",
        run_id="current-run",
    )
    insert_forecast_snapshot(database_path, current_metadata)
    insert_forecast_hourly(
        database_path,
        "current-weather",
        "jennettes_pier",
        atmospheric_payload(wind_direction=75.0),
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                run_id,
                shore_normal_azimuth_degrees,
                wind_to_shore_angle_degrees,
                wave_to_shore_angle_degrees
            from coastal_conditions_hourly
            order by run_id
            """
        ).fetchall()

    assert rows == [
        ("current-run", 75.0, 0.0, None),
        ("historical-run", None, None, None),
    ]


def test_site_relative_angles_preserve_run_and_location_isolation(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    insert_run(database_path, "run-one")
    insert_run(database_path, "run-two")
    insert_run_locations(
        database_path,
        "run-one",
        [
            orientation_location("location-a", 0.0),
            orientation_location("location-b", 90.0),
        ],
    )
    insert_run_locations(
        database_path,
        "run-two",
        [orientation_location("location-a", 180.0)],
    )

    cases = [
        ("run-one", "location-a", "weather-one-a"),
        ("run-one", "location-b", "weather-one-b"),
        ("run-two", "location-a", "weather-two-a"),
    ]
    for run_id, location_id, snapshot_id in cases:
        metadata = snapshot_metadata(
            snapshot_id=snapshot_id,
            run_id=run_id,
        )
        metadata["location_id"] = location_id
        insert_forecast_snapshot(database_path, metadata)
        insert_forecast_hourly(
            database_path,
            snapshot_id,
            location_id,
            atmospheric_payload(wind_direction=90.0),
        )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                run_id,
                location_id,
                shore_normal_azimuth_degrees,
                wind_to_shore_angle_degrees
            from coastal_conditions_hourly
            order by run_id, location_id
            """
        ).fetchall()

    assert rows == [
        ("run-one", "location-a", 0.0, 90.0),
        ("run-one", "location-b", 90.0, 0.0),
        ("run-two", "location-a", 180.0, -90.0),
    ]

def test_initialize_database_upgrades_legacy_orientation_schema(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    insert_run(database_path, "legacy-run")
    metadata = snapshot_metadata(
        snapshot_id="legacy-weather",
        run_id="legacy-run",
    )
    insert_forecast_snapshot(database_path, metadata)
    insert_forecast_hourly(
        database_path,
        "legacy-weather",
        "jennettes_pier",
        atmospheric_payload(wind_direction=75.0),
    )

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("drop view coastal_conditions_hourly")
        connection.execute("drop table run_locations")
        connection.execute(
            """
            create view coastal_conditions_hourly as
            select
                snapshots.run_id,
                hourly.location_id,
                hourly.forecast_time,
                hourly.wind_direction_10m
            from forecast_hourly as hourly
            inner join forecast_snapshots as snapshots
                on snapshots.snapshot_id = hourly.snapshot_id
            """
        )

    initialize_database(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run_location_table_count = connection.execute(
            """
            select count(*)
            from information_schema.tables
            where table_schema = 'main'
                and table_name = 'run_locations'
                and table_type = 'BASE TABLE'
            """
        ).fetchone()
        solar_table_count = connection.execute(
            """
            select count(*)
            from information_schema.tables
            where table_schema = 'main'
                and table_name = 'run_location_solar_context'
                and table_type = 'BASE TABLE'
            """
        ).fetchone()
        row = connection.execute(
            """
            select
                run_id,
                wind_direction_10m,
                shore_normal_azimuth_degrees,
                wind_to_shore_angle_degrees,
                morning_twilight_start,
                evening_twilight_end,
                solar_state
            from coastal_conditions_hourly
            """
        ).fetchone()

    assert run_location_table_count == (1,)
    assert solar_table_count == (1,)
    assert row == ("legacy-run", 75.0, None, None, None, None, None)


def test_analysis_ready_features_require_complete_windows_and_hourly_values(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    target_time = datetime(2026, 7, 29, 23, tzinfo=timezone.utc)
    initialize_database(database_path)
    insert_run(database_path)
    insert_run_locations(database_path, "run123", [orientation_location()])

    weather_metadata = snapshot_metadata(snapshot_id="weather-features")
    wave_metadata = wave_snapshot_metadata(snapshot_id="wave-features")
    wave_metadata["location_id"] = "jennettes_pier"
    sst_metadata = sst_snapshot_metadata(snapshot_id="sst-features")
    sst_metadata["location_id"] = "jennettes_pier"
    insert_forecast_snapshot(database_path, weather_metadata)
    insert_forecast_snapshot(database_path, wave_metadata)
    insert_forecast_snapshot(database_path, sst_metadata)
    insert_tide_snapshot(
        database_path,
        tide_snapshot_metadata(snapshot_id="tide-features"),
        tide_request_provenance(),
        tide_relationship(),
    )

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into forecast_hourly values (?, ?, ?, 20, 10, 75, 15, 1)
            """,
            [
                (
                    "weather-features",
                    "jennettes_pier",
                    datetime(2026, 7, 29, hour, tzinfo=timezone.utc),
                )
                for hour in range(24)
                if hour != 11
            ],
        )
        connection.execute(
            """
            insert into wave_hourly values (?, ?, ?, 1.2, 75, 8)
            """,
            ["wave-features", "jennettes_pier", target_time],
        )
        connection.execute(
            """
            insert into sst_hourly values (?, ?, ?, 25.1)
            """,
            ["sst-features", "jennettes_pier", target_time],
        )
        connection.execute(
            """
            insert into cloud_cover_hourly values (?, ?, ?, 50.0)
            """,
            ["weather-features", "jennettes_pier", target_time],
        )

    insert_tide_events(
        database_path,
        "tide-features",
        "jennettes_pier",
        [
            {
                "event_time": datetime(2026, 7, 29, 0, tzinfo=timezone.utc),
                "event_type": "low",
                "predicted_water_level": 0.0,
            },
            {
                "event_time": datetime(2026, 7, 30, 6, tzinfo=timezone.utc),
                "event_type": "high",
                "predicted_water_level": 1.0,
            },
        ],
    )
    insert_tide_phase_hourly(
        database_path,
        "tide-features",
        "jennettes_pier",
        [{"forecast_time": target_time, "phase": "rising"}],
    )
    for source in ("weather", "wave", "sst", "tide"):
        insert_source_result(
            database_path,
            "run123",
            "jennettes_pier",
            source,
            "success",
            None,
            target_time,
        )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        row = connection.execute(
            """
            select
                precipitation_6h,
                precipitation_6h_complete,
                precipitation_24h,
                precipitation_24h_complete,
                weather_available,
                wave_available,
                sst_available,
                tide_available,
                tide_context_available,
                cloud_cover_available,
                technically_eligible
            from analysis_ready_features_hourly
            where forecast_time = ?
            """,
            [target_time],
        ).fetchone()

    assert row == (6.0, True, None, False, True, True, True, True, True, True, False)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        missing_hour_row = connection.execute(
            """
            select
                weather_status,
                weather_available,
                wave_status,
                wave_available,
                sst_status,
                sst_available,
                tide_status,
                tide_available,
                tide_context_available,
                cloud_cover_available,
                technically_eligible
            from analysis_ready_features_hourly
            where forecast_time = ?
            """,
            [datetime(2026, 7, 29, 22, tzinfo=timezone.utc)],
        ).fetchone()

    assert missing_hour_row == (
        "success",
        True,
        "success",
        False,
        "success",
        False,
        "success",
        False,
        False,
        False,
        False,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        cloud_column_count = connection.execute(
            """
            select count(*)
            from information_schema.columns
            where table_name = 'analysis_ready_features_hourly'
                and column_name = 'cloud_cover_available'
            """
        ).fetchone()

    assert cloud_column_count == (1,)
