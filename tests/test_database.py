from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from forecast_ops.database import (
    complete_pipeline_run,
    initialize_database,
    insert_forecast_hourly,
    insert_forecast_snapshot,
    insert_pipeline_run,
)

EXPECTED_TABLES = {
    "forecast_hourly",
    "forecast_snapshots",
    "pipeline_runs",
    "quality_results",
}


def test_initialize_database_creates_database_and_tables(tmp_path: Path) -> None:
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
                """
            ).fetchall()
        }

    assert tables == EXPECTED_TABLES


def test_initialize_database_can_run_more_than_once(tmp_path: Path) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"

    initialize_database(database_path)
    initialize_database(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        table_count = connection.execute(
            """
            select count(*)
            from information_schema.tables
            where table_schema = 'main'
            """
        ).fetchone()

    assert table_count is not None
    assert table_count[0] == len(EXPECTED_TABLES)


def test_forecast_hourly_rejects_duplicate_business_key(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs (
                run_id,
                environment,
                started_at,
                status
            )
            values (
                'run123',
                'test',
                '2026-07-28 10:00:00+00',
                'running'
            )
            """
        )
        connection.execute(
            """
            insert into forecast_snapshots (
                snapshot_id,
                run_id,
                location_id,
                captured_at,
                raw_file_path
            )
            values (
                'snapshot123',
                'run123',
                'prague',
                '2026-07-28 10:00:00+00',
                'data/test/raw/snapshot123.json'
            )
            """
        )
        connection.execute(
            """
            insert into forecast_hourly (
                snapshot_id,
                location_id,
                forecast_time,
                temperature_2m
            )
            values (
                'snapshot123',
                'prague',
                '2026-07-28 12:00:00+00',
                18.2
            )
            """
        )

        try:
            connection.execute(
                """
                insert into forecast_hourly (
                    snapshot_id,
                    location_id,
                    forecast_time,
                    temperature_2m
                )
                values (
                    'snapshot123',
                    'prague',
                    '2026-07-28 12:00:00+00',
                    19.1
                )
                """
            )
        except duckdb.ConstraintException:
            pass
        else:
            raise AssertionError("duplicate forecast business key was accepted")


def test_insert_pipeline_run_and_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)

    started_at = datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc)
    captured_at = datetime(2026, 7, 28, 10, 5, tzinfo=timezone.utc)

    insert_pipeline_run(
        database_path=database_path,
        run_id="run123",
        environment="test",
        started_at=started_at,
    )

    insert_forecast_snapshot(
        database_path=database_path,
        metadata={
            "snapshot_id": "snapshot123",
            "run_id": "run123",
            "location_id": "prague",
            "captured_at": captured_at,
            "raw_file_path": "data/test/raw/snapshot123.json",
        },
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select
                environment,
                status,
                rows_loaded
            from pipeline_runs
            where run_id = 'run123'
            """
        ).fetchone()

        snapshot = connection.execute(
            """
            select
                run_id,
                location_id,
                raw_file_path
            from forecast_snapshots
            where snapshot_id = 'snapshot123'
            """
        ).fetchone()

    assert run == ("test", "running", 0)
    assert snapshot == (
        "run123",
        "prague",
        "data/test/raw/snapshot123.json",
    )


def test_complete_pipeline_run_updates_status(tmp_path: Path) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)

    insert_pipeline_run(
        database_path=database_path,
        run_id="run123",
        environment="test",
        started_at=datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
    )

    completed_at = datetime(2026, 7, 28, 10, 10, tzinfo=timezone.utc)

    complete_pipeline_run(
        database_path=database_path,
        run_id="run123",
        completed_at=completed_at,
        status="success",
        rows_loaded=48,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute(
            """
            select
                status,
                rows_loaded,
                error_message
            from pipeline_runs
            where run_id = 'run123'
            """
        ).fetchone()

    assert result == ("success", 48, None)


def test_complete_pipeline_run_requires_existing_run(tmp_path: Path) -> None:
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


def test_insert_forecast_hourly_loads_normalized_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "forecast_ops.duckdb"
    initialize_database(database_path)

    insert_pipeline_run(
        database_path=database_path,
        run_id="run123",
        environment="test",
        started_at=datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
    )

    insert_forecast_snapshot(
        database_path=database_path,
        metadata={
            "snapshot_id": "snapshot123",
            "run_id": "run123",
            "location_id": "prague",
            "captured_at": datetime(
                2026,
                7,
                28,
                10,
                5,
                tzinfo=timezone.utc,
            ),
            "raw_file_path": "data/test/raw/snapshot123.json",
        },
    )

    payload = {
        "timezone": "Europe/Prague",
        "hourly": {
            "time": [
                "2026-07-28T12:00",
                "2026-07-28T13:00",
            ],
            "temperature_2m": [18.2, 19.1],
            "precipitation_probability": [10, 20],
            "wind_speed_10m": [8.4, 9.1],
        },
    }

    rows_loaded = insert_forecast_hourly(
        database_path=database_path,
        snapshot_id="snapshot123",
        location_id="prague",
        payload=payload,
    )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            select
                location_id,
                forecast_time,
                temperature_2m,
                precipitation_probability,
                wind_speed_10m
            from forecast_hourly
            order by forecast_time
            """
        ).fetchall()

    assert rows_loaded == 2
    assert rows == [
        (
            "prague",
            datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
            18.2,
            10.0,
            8.4,
        ),
        (
            "prague",
            datetime(2026, 7, 28, 11, 0, tzinfo=timezone.utc),
            19.1,
            20.0,
            9.1,
        ),
    ]


def test_insert_forecast_hourly_rejects_mismatched_lengths(
    tmp_path: Path,
) -> None:
    payload = {
        "timezone": "Europe/Prague",
        "hourly": {
            "time": [
                "2026-07-28T12:00",
                "2026-07-28T13:00",
            ],
            "temperature_2m": [18.2],
            "precipitation_probability": [10, 20],
            "wind_speed_10m": [8.4, 9.1],
        },
    }

    with pytest.raises(
        ValueError,
        match="hourly temperature_2m length must match hourly time length",
    ):
        insert_forecast_hourly(
            database_path=tmp_path / "forecast_ops.duckdb",
            snapshot_id="snapshot123",
            location_id="prague",
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
            location_id="prague",
            payload={},
        )


def test_insert_forecast_hourly_requires_timezone(tmp_path: Path) -> None:
    payload = {
        "hourly": {
            "time": ["2026-07-28T12:00"],
            "temperature_2m": [18.2],
            "precipitation_probability": [10],
            "wind_speed_10m": [8.4],
        }
    }

    with pytest.raises(
        ValueError,
        match="forecast payload must contain a timezone",
    ):
        insert_forecast_hourly(
            database_path=tmp_path / "forecast_ops.duckdb",
            snapshot_id="snapshot123",
            location_id="prague",
            payload=payload,
        )