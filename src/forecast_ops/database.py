from datetime import datetime, timezone
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
    model_selector varchar,
    request_latitude double,
    request_longitude double,
    returned_latitude double,
    returned_longitude double,
    response_timezone varchar,
    response_utc_offset_seconds integer,
    foreign key (run_id) references pipeline_runs(run_id)
);

create table if not exists forecast_hourly (
    snapshot_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
    temperature_2m double,
    precipitation_probability double,
    wind_speed_10m double,
    wind_direction_10m double,
    wind_gusts_10m double,
    precipitation double,
    primary key (snapshot_id, location_id, forecast_time),
    foreign key (snapshot_id) references forecast_snapshots(snapshot_id)
);

create table if not exists wave_hourly (
    snapshot_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
    wave_height double,
    wave_direction double,
    wave_period double,
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

_MIGRATION_SQL = """
drop view if exists forecast_revision_changes;

alter table forecast_snapshots
    add column if not exists model_selector varchar;
alter table forecast_snapshots
    add column if not exists request_latitude double;
alter table forecast_snapshots
    add column if not exists request_longitude double;
alter table forecast_snapshots
    add column if not exists returned_latitude double;
alter table forecast_snapshots
    add column if not exists returned_longitude double;
alter table forecast_snapshots
    add column if not exists response_timezone varchar;
alter table forecast_snapshots
    add column if not exists response_utc_offset_seconds integer;

alter table forecast_hourly
    add column if not exists wind_direction_10m double;
alter table forecast_hourly
    add column if not exists wind_gusts_10m double;
alter table forecast_hourly
    add column if not exists precipitation double;
"""

_REVISION_VIEW_SQL = """
create or replace view forecast_revision_changes as
with ordered_forecasts as (
    select
        hourly.location_id,
        hourly.forecast_time,
        snapshots.captured_at,
        hourly.snapshot_id,
        hourly.wind_speed_10m,
        hourly.wind_direction_10m,
        hourly.wind_gusts_10m,
        hourly.precipitation_probability,
        hourly.precipitation,
        lag(hourly.snapshot_id) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_snapshot_id,
        lag(hourly.wind_speed_10m) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_wind_speed_10m,
        lag(hourly.wind_direction_10m) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_wind_direction_10m,
        lag(hourly.wind_gusts_10m) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_wind_gusts_10m,
        lag(hourly.precipitation_probability) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_precipitation_probability,
        lag(hourly.precipitation) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_precipitation
    from forecast_hourly as hourly
    inner join forecast_snapshots as snapshots
        on hourly.snapshot_id = snapshots.snapshot_id
)
select
    location_id,
    forecast_time,
    captured_at,
    snapshot_id,
    previous_snapshot_id,
    wind_speed_10m,
    previous_wind_speed_10m,
    wind_speed_10m - previous_wind_speed_10m as wind_speed_10m_change,
    wind_direction_10m,
    previous_wind_direction_10m,
    wind_gusts_10m,
    previous_wind_gusts_10m,
    wind_gusts_10m
        - previous_wind_gusts_10m
        as wind_gusts_10m_change,
    precipitation_probability,
    previous_precipitation_probability,
    precipitation_probability
        - previous_precipitation_probability
        as precipitation_probability_change,
    precipitation,
    previous_precipitation,
    precipitation - previous_precipitation as precipitation_change
from ordered_forecasts
where previous_snapshot_id is not null;

create or replace view wave_revision_changes as
with ordered_wave_forecasts as (
    select
        hourly.location_id,
        hourly.forecast_time,
        snapshots.captured_at,
        hourly.snapshot_id,
        hourly.wave_height,
        hourly.wave_direction,
        hourly.wave_period,
        lag(hourly.snapshot_id) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_snapshot_id,
        lag(hourly.wave_height) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_wave_height,
        lag(hourly.wave_direction) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_wave_direction,
        lag(hourly.wave_period) over (
            partition by
                hourly.location_id,
                hourly.forecast_time
            order by
                snapshots.captured_at,
                hourly.snapshot_id
        ) as previous_wave_period
    from wave_hourly as hourly
    inner join forecast_snapshots as snapshots
        on hourly.snapshot_id = snapshots.snapshot_id
    where snapshots.model_selector = 'meteofrance_wave'
)
select
    location_id,
    forecast_time,
    captured_at,
    snapshot_id,
    previous_snapshot_id,
    wave_height,
    previous_wave_height,
    wave_height - previous_wave_height as wave_height_change,
    wave_direction,
    previous_wave_direction,
    wave_period,
    previous_wave_period,
    wave_period - previous_wave_period as wave_period_change
from ordered_wave_forecasts
where previous_snapshot_id is not null;
"""


# create the database file and required tables
def initialize_database(database_path: Path | str) -> None:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("begin transaction")

        try:
            connection.execute(_SCHEMA_SQL)
            connection.execute(_MIGRATION_SQL)
            connection.execute(_REVISION_VIEW_SQL)
        except Exception:
            connection.execute("rollback")
            raise
        else:
            connection.execute("commit")


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
                raw_file_path,
                model_selector,
                request_latitude,
                request_longitude,
                returned_latitude,
                returned_longitude,
                response_timezone,
                response_utc_offset_seconds
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                metadata["snapshot_id"],
                metadata["run_id"],
                metadata["location_id"],
                metadata["captured_at"],
                metadata["raw_file_path"],
                metadata["model_selector"],
                metadata["request_latitude"],
                metadata["request_longitude"],
                metadata["returned_latitude"],
                metadata["returned_longitude"],
                metadata["response_timezone"],
                metadata["response_utc_offset_seconds"],
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
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "precipitation_probability",
        "precipitation",
    )

    for metric_name in metric_names:
        metric_values = hourly.get(metric_name)

        if not isinstance(metric_values, list):
            raise ValueError(f"forecast payload must contain an hourly {metric_name} list")

        if len(metric_values) != len(forecast_times):
            raise ValueError(
                f"hourly {metric_name} length must match hourly time length"
            )

    normalized_times = []

    for forecast_time in forecast_times:
        parsed_time = datetime.fromisoformat(forecast_time)

        if parsed_time.tzinfo is None:
            parsed_time = parsed_time.replace(tzinfo=forecast_timezone)

        normalized_times.append(parsed_time.astimezone(timezone.utc))

    rows = [
        (
            snapshot_id,
            location_id,
            forecast_time,
            hourly["wind_speed_10m"][index],
            hourly["wind_direction_10m"][index],
            hourly["wind_gusts_10m"][index],
            hourly["precipitation_probability"][index],
            hourly["precipitation"][index],
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
                wind_speed_10m,
                wind_direction_10m,
                wind_gusts_10m,
                precipitation_probability,
                precipitation
            )
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    return len(rows)


# insert normalized hourly wave rows for one snapshot
def insert_wave_hourly(
    database_path: Path | str,
    snapshot_id: str,
    location_id: str,
    payload: dict[str, Any],
) -> int:
    hourly = payload.get("hourly")

    if not isinstance(hourly, dict):
        raise ValueError("wave payload must contain an hourly mapping")

    forecast_times = hourly.get("time")

    if not isinstance(forecast_times, list):
        raise ValueError("wave payload must contain an hourly time list")

    timezone_name = payload.get("timezone")

    if not isinstance(timezone_name, str):
        raise ValueError("wave payload must contain a timezone")

    try:
        forecast_timezone = ZoneInfo(timezone_name)
    except Exception as error:
        raise ValueError(f"invalid wave timezone: {timezone_name}") from error

    metric_names = (
        "wave_height",
        "wave_direction",
        "wave_period",
    )

    for metric_name in metric_names:
        metric_values = hourly.get(metric_name)

        if not isinstance(metric_values, list):
            raise ValueError(
                f"wave payload must contain an hourly {metric_name} list"
            )

        if len(metric_values) != len(forecast_times):
            raise ValueError(
                f"hourly {metric_name} length must match hourly time length"
            )

    normalized_times = []

    for forecast_time in forecast_times:
        parsed_time = datetime.fromisoformat(forecast_time)

        if parsed_time.tzinfo is None:
            parsed_time = parsed_time.replace(tzinfo=forecast_timezone)

        normalized_times.append(parsed_time.astimezone(timezone.utc))

    rows = [
        (
            snapshot_id,
            location_id,
            forecast_time,
            hourly["wave_height"][index],
            hourly["wave_direction"][index],
            hourly["wave_period"][index],
        )
        for index, forecast_time in enumerate(normalized_times)
    ]

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into wave_hourly (
                snapshot_id,
                location_id,
                forecast_time,
                wave_height,
                wave_direction,
                wave_period
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
