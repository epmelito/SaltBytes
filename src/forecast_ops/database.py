from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import duckdb

_SCHEMA_SQL = """
create table if not exists pipeline_runs (
    run_id varchar primary key,
    environment varchar not null,
    started_at timestamptz not null,
    completed_at timestamptz,
    status varchar not null,
    rows_loaded integer not null default 0,
    error_message varchar
);

create table if not exists forecast_snapshots (
    snapshot_id varchar primary key,
    run_id varchar not null,
    location_id varchar not null,
    captured_at timestamptz not null,
    raw_file_path varchar not null,
    foreign key (run_id) references pipeline_runs(run_id)
);

create table if not exists forecast_hourly (
    snapshot_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
    temperature_2m double,
    precipitation_probability double,
    wind_speed_10m double,
    primary key (snapshot_id, location_id, forecast_time),
    foreign key (snapshot_id) references forecast_snapshots(snapshot_id)
);

create table if not exists quality_results (
    run_id varchar not null,
    check_name varchar not null,
    status varchar not null,
    observed_value varchar,
    expected_value varchar,
    checked_at timestamptz not null,
    foreign key (run_id) references pipeline_runs(run_id)
);
"""


# create the database file and required tables
def initialize_database(database_path: Path | str) -> None:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(_SCHEMA_SQL)


# insert a new pipeline run
def insert_pipeline_run(
    database_path: Path | str,
    run_id: str,
    environment: str,
    started_at: datetime,
    status: str = "running",
) -> None:
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs (
                run_id,
                environment,
                started_at,
                status
            )
            values (?, ?, ?, ?)
            """,
            [run_id, environment, started_at, status],
        )


# insert metadata for one raw forecast snapshot
def insert_forecast_snapshot(
    database_path: Path | str,
    metadata: dict[str, Any],
) -> None:
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into forecast_snapshots (
                snapshot_id,
                run_id,
                location_id,
                captured_at,
                raw_file_path
            )
            values (?, ?, ?, ?, ?)
            """,
            [
                metadata["snapshot_id"],
                metadata["run_id"],
                metadata["location_id"],
                metadata["captured_at"],
                metadata["raw_file_path"],
            ],
        )


# insert one data quality result
def insert_quality_result(
    database_path: Path | str,
    run_id: str,
    check_name: str,
    status: str,
    observed_value: str,
    expected_value: str,
    checked_at: datetime,
) -> None:
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into quality_results (
                run_id,
                check_name,
                status,
                observed_value,
                expected_value,
                checked_at
            )
            values (?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                check_name,
                status,
                observed_value,
                expected_value,
                checked_at,
            ],
        )


# insert normalized hourly forecast rows for one snapshot
def insert_forecast_hourly(
    database_path: Path | str,
    snapshot_id: str,
    location_id: str,
    payload: dict[str, Any],
) -> int:
    hourly = payload.get("hourly")

    if not isinstance(hourly, dict):
        raise ValueError("forecast payload must contain an hourly mapping")

    forecast_times = hourly.get("time")

    if not isinstance(forecast_times, list):
        raise ValueError("forecast payload must contain an hourly time list")

    timezone_name = payload.get("timezone")

    if not isinstance(timezone_name, str):
        raise ValueError("forecast payload must contain a timezone")

    try:
        forecast_timezone = ZoneInfo(timezone_name)
    except Exception as error:
        raise ValueError(f"invalid forecast timezone: {timezone_name}") from error

    metric_names = (
        "temperature_2m",
        "precipitation_probability",
        "wind_speed_10m",
    )

    for metric_name in metric_names:
        metric_values = hourly.get(metric_name)

        if not isinstance(metric_values, list):
            raise ValueError(f"forecast payload must contain an hourly {metric_name} list")

        if len(metric_values) != len(forecast_times):
            raise ValueError(
                f"hourly {metric_name} length must match hourly time length"
            )

    normalized_times = [
        datetime.fromisoformat(forecast_time).replace(tzinfo=forecast_timezone)
        for forecast_time in forecast_times
    ]

    rows = [
        (
            snapshot_id,
            location_id,
            forecast_time,
            hourly["temperature_2m"][index],
            hourly["precipitation_probability"][index],
            hourly["wind_speed_10m"][index],
        )
        for index, forecast_time in enumerate(normalized_times)
    ]

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into forecast_hourly (
                snapshot_id,
                location_id,
                forecast_time,
                temperature_2m,
                precipitation_probability,
                wind_speed_10m
            )
            values (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    return len(rows)


# update the final state of a pipeline run
def complete_pipeline_run(
    database_path: Path | str,
    run_id: str,
    completed_at: datetime,
    status: str,
    rows_loaded: int,
    error_message: str | None = None,
) -> None:
    with duckdb.connect(str(database_path)) as connection:
        existing_run = connection.execute(
            """
            select 1
            from pipeline_runs
            where run_id = ?
            """,
            [run_id],
        ).fetchone()

        if existing_run is None:
            raise ValueError(f"pipeline run not found: {run_id}")

        connection.execute(
            """
            update pipeline_runs
            set
                completed_at = ?,
                status = ?,
                rows_loaded = ?,
                error_message = ?
            where run_id = ?
            """,
            [
                completed_at,
                status,
                rows_loaded,
                error_message,
                run_id,
            ],
        )