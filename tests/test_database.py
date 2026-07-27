from pathlib import Path

import duckdb

from forecast_ops.database import initialize_database

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