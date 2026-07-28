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
    insert_quality_result,
)

EXPECTED_TABLES = {
    "forecast_hourly",
    "forecast_snapshots",
    "pipeline_runs",
    "quality_results",
}
EXPECTED_VIEWS = {"forecast_revision_changes"}
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
    "response_timezone",
    "response_utc_offset_seconds",
}
EXPECTED_HOURLY_COLUMNS = {
    "snapshot_id",
    "location_id",
    "forecast_time",
    "temperature_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation_probability",
    "precipitation",
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
        "response_timezone": "America/New_York",
        "response_utc_offset_seconds": -14400,
    }


def atmospheric_payload(
    wind_speed: float = 10.0,
    wind_direction: float = 180.0,
    wind_gust: float = 15.0,
    precipitation_probability: float = 20.0,
    precipitation: float = 0.0,
) -> dict[str, Any]:
    return {
        "timezone": "America/New_York",
        "hourly": {
            "time": ["2026-07-29T12:00"],
            "wind_speed_10m": [wind_speed],
            "wind_direction_10m": [wind_direction],
            "wind_gusts_10m": [wind_gust],
            "precipitation_probability": [precipitation_probability],
            "precipitation": [precipitation],
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
        environment="test",
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
        views = {
            row[0]
            for row in connection.execute(
                """
                select table_name
                from information_schema.views
                where table_schema = 'main'
                    and table_catalog = current_database()
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

    assert tables == EXPECTED_TABLES
    assert views == EXPECTED_VIEWS
    assert snapshot_columns == EXPECTED_SNAPSHOT_COLUMNS
    assert hourly_columns == EXPECTED_HOURLY_COLUMNS


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


def test_initialize_database_upgrades_legacy_schema_and_preserves_rows(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            create table pipeline_runs (
                run_id varchar primary key,
                environment varchar not null,
                started_at timestamptz not null,
                completed_at timestamptz,
                status varchar not null,
                rows_loaded integer not null default 0,
                error_message varchar
            );
            create table forecast_snapshots (
                snapshot_id varchar primary key,
                run_id varchar not null,
                location_id varchar not null,
                captured_at timestamptz not null,
                raw_file_path varchar not null,
                foreign key (run_id) references pipeline_runs(run_id)
            );
            create table forecast_hourly (
                snapshot_id varchar not null,
                location_id varchar not null,
                forecast_time timestamptz not null,
                temperature_2m double,
                precipitation_probability double,
                wind_speed_10m double,
                primary key (snapshot_id, location_id, forecast_time),
                foreign key (snapshot_id)
                    references forecast_snapshots(snapshot_id)
            );
            create view forecast_revision_changes as
            select
                location_id,
                forecast_time,
                temperature_2m
            from forecast_hourly;
            insert into pipeline_runs
            values (
                'legacy-run',
                'dev',
                '2026-07-28 08:00:00+00',
                null,
                'success',
                1,
                null
            );
            insert into forecast_snapshots
            values (
                'legacy-snapshot',
                'legacy-run',
                'prague',
                '2026-07-28 08:05:00+00',
                'data/dev/raw/legacy.json'
            );
            insert into forecast_hourly
            values (
                'legacy-snapshot',
                'prague',
                '2026-07-29 12:00:00+00',
                18.2,
                20,
                8.4
            );
            """
        )

    initialize_database(database_path)
    initialize_database(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        snapshot = connection.execute(
            """
            select
                snapshot_id,
                model_selector,
                request_latitude,
                returned_latitude
            from forecast_snapshots
            """
        ).fetchone()
        hourly = connection.execute(
            """
            select
                temperature_2m,
                wind_speed_10m,
                wind_direction_10m,
                wind_gusts_10m,
                precipitation_probability,
                precipitation
            from forecast_hourly
            """
        ).fetchone()
        revision_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'forecast_revision_changes'
                """
            ).fetchall()
        }

    assert snapshot == ("legacy-snapshot", None, None, None)
    assert hourly == (18.2, 8.4, None, None, 20.0, None)
    assert "wind_direction_10m" in revision_columns
    assert "previous_wind_direction_10m" in revision_columns
    assert "wind_direction_10m_change" not in revision_columns


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
            select environment, status, rows_loaded
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
                returned_longitude,
                response_timezone,
                response_utc_offset_seconds
            from forecast_snapshots
            where snapshot_id = 'snapshot123'
            """
        ).fetchone()

    assert run == ("test", "running", 0)
    assert snapshot == (
        "run123",
        "jennettes_pier",
        "data/test/raw/snapshot123.json",
        "ncep_nbm_conus",
        35.9096355,
        -75.5966537,
        35.89557,
        -75.5936,
        "America/New_York",
        -14400,
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
        "timezone": "America/New_York",
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
                temperature_2m,
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
            datetime(2026, 7, 29, 16, 0, tzinfo=timezone.utc),
            None,
            10.0,
            180.0,
            15.0,
            20.0,
            0.0,
        ),
        (
            datetime(2026, 7, 29, 17, 0, tzinfo=timezone.utc),
            None,
            11.0,
            190.0,
            16.0,
            30.0,
            0.4,
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


def test_insert_forecast_hourly_requires_timezone(
    tmp_path: Path,
) -> None:
    payload = atmospheric_payload()
    del payload["timezone"]

    with pytest.raises(
        ValueError,
        match="forecast payload must contain a timezone",
    ):
        insert_forecast_hourly(
            database_path=tmp_path / "forecast_ops.duckdb",
            snapshot_id="snapshot123",
            location_id="jennettes_pier",
            payload=payload,
        )


def test_insert_quality_result(tmp_path: Path) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(database_path)

    insert_quality_result(
        database_path=database_path,
        run_id="run123",
        check_name="hourly_utc_time_count",
        status="pass",
        observed_value="168",
        expected_value="168",
        checked_at=datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc),
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute(
            """
            select check_name, status, observed_value, expected_value
            from quality_results
            where run_id = 'run123'
            """
        ).fetchone()

    assert result == (
        "hourly_utc_time_count",
        "pass",
        "168",
        "168",
    )


def test_forecast_revision_view_compares_coastal_fields(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)
    insert_run(
        database_path,
        run_id="run001",
        started_at=datetime(2026, 7, 28, 8, 0, tzinfo=timezone.utc),
    )
    insert_run(
        database_path,
        run_id="run002",
        started_at=datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
    )
    insert_forecast_snapshot(
        database_path,
        snapshot_metadata(
            snapshot_id="snapshot001",
            run_id="run001",
            captured_at=datetime(
                2026,
                7,
                28,
                8,
                5,
                tzinfo=timezone.utc,
            ),
        ),
    )
    insert_forecast_snapshot(
        database_path,
        snapshot_metadata(
            snapshot_id="snapshot002",
            run_id="run002",
            captured_at=datetime(
                2026,
                7,
                28,
                10,
                5,
                tzinfo=timezone.utc,
            ),
        ),
    )

    insert_forecast_hourly(
        database_path,
        "snapshot001",
        "jennettes_pier",
        atmospheric_payload(
            wind_speed=10.0,
            wind_direction=350.0,
            wind_gust=15.0,
            precipitation_probability=20.0,
            precipitation=0.0,
        ),
    )
    insert_forecast_hourly(
        database_path,
        "snapshot002",
        "jennettes_pier",
        atmospheric_payload(
            wind_speed=8.5,
            wind_direction=10.0,
            wind_gust=18.0,
            precipitation_probability=35.0,
            precipitation=0.4,
        ),
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        revision = connection.execute(
            """
            select
                snapshot_id,
                previous_snapshot_id,
                wind_speed_10m_change,
                wind_direction_10m,
                previous_wind_direction_10m,
                wind_gusts_10m_change,
                precipitation_probability_change,
                precipitation_change
            from forecast_revision_changes
            where location_id = 'jennettes_pier'
            """
        ).fetchone()
        revision_columns = {
            row[0]
            for row in connection.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'forecast_revision_changes'
                """
            ).fetchall()
        }

    assert revision == (
        "snapshot002",
        "snapshot001",
        -1.5,
        10.0,
        350.0,
        3.0,
        15.0,
        0.4,
    )
    assert "wind_direction_10m_change" not in revision_columns
