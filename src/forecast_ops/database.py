from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

_SCHEMA_SQL = """
create table if not exists pipeline_runs (
    run_id varchar primary key,
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
    foreign key (run_id) references pipeline_runs(run_id)
);

create table if not exists forecast_hourly (
    snapshot_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
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

create table if not exists sst_hourly (
    snapshot_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
    sea_surface_temperature double,
    primary key (snapshot_id, location_id, forecast_time),
    foreign key (snapshot_id) references forecast_snapshots(snapshot_id)
);

create table if not exists tide_snapshots (
    snapshot_id varchar primary key,
    station_id varchar not null,
    prediction_location varchar not null,
    relationship_type varchar not null,
    reference_station varchar,
    product varchar not null,
    interval varchar not null,
    datum varchar not null,
    time_zone varchar not null,
    units varchar not null,
    response_format varchar not null,
    request_begin_date date not null,
    request_end_date date not null,
    high_time_offset_minutes integer,
    low_time_offset_minutes integer,
    high_multiplier double,
    low_multiplier double,
    distance_km double not null,
    coastal_relationship varchar not null,
    known_limitation varchar not null,
    foreign key (snapshot_id) references forecast_snapshots(snapshot_id)
);

create table if not exists tide_events (
    snapshot_id varchar not null,
    location_id varchar not null,
    event_time timestamptz not null,
    event_type varchar not null,
    predicted_water_level double not null,
    primary key (snapshot_id, location_id, event_time),
    foreign key (snapshot_id) references tide_snapshots(snapshot_id)
);

create table if not exists tide_phase_hourly (
    snapshot_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
    phase varchar not null,
    primary key (snapshot_id, location_id, forecast_time),
    foreign key (snapshot_id) references tide_snapshots(snapshot_id)
);

create table if not exists source_results (
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
);

create or replace view coastal_conditions_hourly as
with hourly_keys as (
    select snapshots.run_id, hourly.location_id, hourly.forecast_time
    from forecast_hourly as hourly
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = hourly.snapshot_id
    union
    select snapshots.run_id, hourly.location_id, hourly.forecast_time
    from wave_hourly as hourly
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = hourly.snapshot_id
    union
    select snapshots.run_id, hourly.location_id, hourly.forecast_time
    from sst_hourly as hourly
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = hourly.snapshot_id
    union
    select snapshots.run_id, hourly.location_id, hourly.forecast_time
    from tide_phase_hourly as hourly
    inner join tide_snapshots as tide_snapshots
        on tide_snapshots.snapshot_id = hourly.snapshot_id
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = tide_snapshots.snapshot_id
),
weather_rows as (
    select
        snapshots.run_id,
        hourly.location_id,
        hourly.forecast_time,
        hourly.snapshot_id,
        hourly.precipitation_probability,
        hourly.wind_speed_10m,
        hourly.wind_direction_10m,
        hourly.wind_gusts_10m,
        hourly.precipitation
    from forecast_hourly as hourly
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = hourly.snapshot_id
),
wave_rows as (
    select
        snapshots.run_id,
        hourly.location_id,
        hourly.forecast_time,
        hourly.snapshot_id,
        hourly.wave_height,
        hourly.wave_direction,
        hourly.wave_period
    from wave_hourly as hourly
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = hourly.snapshot_id
),
sst_rows as (
    select
        snapshots.run_id,
        hourly.location_id,
        hourly.forecast_time,
        hourly.snapshot_id,
        hourly.sea_surface_temperature
    from sst_hourly as hourly
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = hourly.snapshot_id
),
tide_rows as (
    select
        snapshots.run_id,
        hourly.location_id,
        hourly.forecast_time,
        hourly.snapshot_id,
        hourly.phase
    from tide_phase_hourly as hourly
    inner join tide_snapshots as tide_snapshots
        on tide_snapshots.snapshot_id = hourly.snapshot_id
    inner join forecast_snapshots as snapshots
        on snapshots.snapshot_id = tide_snapshots.snapshot_id
)
select
    hourly_keys.run_id,
    runs.started_at as run_started_at,
    runs.status as run_status,
    hourly_keys.location_id,
    hourly_keys.forecast_time,
    weather_rows.snapshot_id as weather_snapshot_id,
    weather_rows.precipitation_probability,
    weather_rows.wind_speed_10m,
    weather_rows.wind_direction_10m,
    weather_rows.wind_gusts_10m,
    weather_rows.precipitation,
    weather_results.status as weather_status,
    wave_rows.snapshot_id as wave_snapshot_id,
    wave_rows.wave_height,
    wave_rows.wave_direction,
    wave_rows.wave_period,
    wave_results.status as wave_status,
    sst_rows.snapshot_id as sst_snapshot_id,
    sst_rows.sea_surface_temperature,
    sst_results.status as sst_status,
    tide_rows.snapshot_id as tide_snapshot_id,
    tide_rows.phase as tide_phase,
    tide_results.status as tide_status
from hourly_keys
inner join pipeline_runs as runs
    on runs.run_id = hourly_keys.run_id
left join weather_rows
    on weather_rows.run_id = hourly_keys.run_id
    and weather_rows.location_id = hourly_keys.location_id
    and weather_rows.forecast_time = hourly_keys.forecast_time
left join wave_rows
    on wave_rows.run_id = hourly_keys.run_id
    and wave_rows.location_id = hourly_keys.location_id
    and wave_rows.forecast_time = hourly_keys.forecast_time
left join sst_rows
    on sst_rows.run_id = hourly_keys.run_id
    and sst_rows.location_id = hourly_keys.location_id
    and sst_rows.forecast_time = hourly_keys.forecast_time
left join tide_rows
    on tide_rows.run_id = hourly_keys.run_id
    and tide_rows.location_id = hourly_keys.location_id
    and tide_rows.forecast_time = hourly_keys.forecast_time
left join source_results as weather_results
    on weather_results.run_id = hourly_keys.run_id
    and weather_results.location_id = hourly_keys.location_id
    and weather_results.source = 'weather'
left join source_results as wave_results
    on wave_results.run_id = hourly_keys.run_id
    and wave_results.location_id = hourly_keys.location_id
    and wave_results.source = 'wave'
left join source_results as sst_results
    on sst_results.run_id = hourly_keys.run_id
    and sst_results.location_id = hourly_keys.location_id
    and sst_results.source = 'sst'
left join source_results as tide_results
    on tide_results.run_id = hourly_keys.run_id
    and tide_results.location_id = hourly_keys.location_id
    and tide_results.source = 'tide';
"""

# create the database file and required tables
def initialize_database(database_path: Path | str) -> None:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("begin transaction")

        try:
            connection.execute(_SCHEMA_SQL)
        except Exception:
            connection.execute("rollback")
            raise
        else:
            connection.execute("commit")


# insert a new pipeline run
def insert_pipeline_run(
    database_path: Path | str,
    run_id: str,
    started_at: datetime,
    status: str = "running",
) -> None:
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs (
                run_id,
                started_at,
                status
            )
            values (?, ?, ?)
            """,
            [run_id, started_at, status],
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
                returned_longitude
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ],
        )


def insert_source_result(
    database_path: Path | str,
    run_id: str,
    location_id: str,
    source: str,
    status: str,
    detail: str | None,
    recorded_at: datetime,
) -> None:
    valid_statuses = {"success", "fetch_failed", "validation_failed"}

    if status not in valid_statuses:
        raise ValueError(f"unsupported source result status: {status}")

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into source_results (
                run_id,
                location_id,
                source,
                status,
                detail,
                recorded_at
            )
            values (?, ?, ?, ?, ?, ?)
            """,
            [
                run_id,
                location_id,
                source,
                status,
                detail,
                recorded_at,
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

        if parsed_time.tzinfo is not None:
            raise ValueError(
                "forecast payload hourly timestamps must be UTC-naive"
            )

        normalized_times.append(parsed_time.replace(tzinfo=timezone.utc))

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

        if parsed_time.tzinfo is not None:
            raise ValueError("wave payload hourly timestamps must be UTC-naive")

        normalized_times.append(parsed_time.replace(tzinfo=timezone.utc))

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


# insert normalized hourly sea surface temperature rows for one snapshot
def insert_sst_hourly(
    database_path: Path | str,
    snapshot_id: str,
    location_id: str,
    payload: dict[str, Any],
) -> int:
    hourly = payload.get("hourly")

    if not isinstance(hourly, dict):
        raise ValueError("sst payload must contain an hourly mapping")

    forecast_times = hourly.get("time")

    if not isinstance(forecast_times, list):
        raise ValueError("sst payload must contain an hourly time list")

    sst_values = hourly.get("sea_surface_temperature")

    if not isinstance(sst_values, list):
        raise ValueError(
            "sst payload must contain an hourly sea_surface_temperature list"
        )

    if len(sst_values) != len(forecast_times):
        raise ValueError(
            "hourly sea_surface_temperature length must match "
            "hourly time length"
        )

    normalized_times = []

    for forecast_time in forecast_times:
        parsed_time = datetime.fromisoformat(forecast_time)

        if parsed_time.tzinfo is not None:
            raise ValueError("sst payload hourly timestamps must be UTC-naive")

        normalized_times.append(parsed_time.replace(tzinfo=timezone.utc))

    rows = [
        (
            snapshot_id,
            location_id,
            forecast_time,
            sst_values[index],
        )
        for index, forecast_time in enumerate(normalized_times)
    ]

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into sst_hourly (
                snapshot_id,
                location_id,
                forecast_time,
                sea_surface_temperature
            )
            values (?, ?, ?, ?)
            """,
            rows,
        )

    return len(rows)


# insert one tide raw snapshot and its distinct NOAA request provenance
def insert_tide_snapshot(
    database_path: Path | str,
    metadata: dict[str, Any],
    request_provenance: dict[str, Any],
    relationship: dict[str, Any],
) -> None:
    request_begin_date = datetime.strptime(
        request_provenance["begin_date"],
        "%Y%m%d",
    ).date()
    request_end_date = datetime.strptime(
        request_provenance["end_date"],
        "%Y%m%d",
    ).date()

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("begin transaction")

        try:
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
            connection.execute(
                """
                insert into tide_snapshots (
                    snapshot_id,
                    station_id,
                    prediction_location,
                    relationship_type,
                    reference_station,
                    product,
                    interval,
                    datum,
                    time_zone,
                    units,
                    response_format,
                    request_begin_date,
                    request_end_date,
                    high_time_offset_minutes,
                    low_time_offset_minutes,
                    high_multiplier,
                    low_multiplier,
                    distance_km,
                    coastal_relationship,
                    known_limitation
                )
                values (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                [
                    metadata["snapshot_id"],
                    request_provenance["station"],
                    relationship["prediction_location"],
                    relationship["relationship_type"],
                    relationship["reference_station"],
                    request_provenance["product"],
                    request_provenance["interval"],
                    request_provenance["datum"],
                    request_provenance["time_zone"],
                    request_provenance["units"],
                    request_provenance["format"],
                    request_begin_date,
                    request_end_date,
                    relationship["high_time_offset_minutes"],
                    relationship["low_time_offset_minutes"],
                    relationship["high_multiplier"],
                    relationship["low_multiplier"],
                    relationship["distance_km"],
                    relationship["coastal_relationship"],
                    relationship["known_limitation"],
                ],
            )
        except Exception:
            connection.execute("rollback")
            raise
        else:
            connection.execute("commit")


# insert normalized NOAA high and low events for one tide snapshot
def insert_tide_events(
    database_path: Path | str,
    snapshot_id: str,
    location_id: str,
    events: list[dict[str, Any]],
) -> int:
    rows = [
        (
            snapshot_id,
            location_id,
            event["event_time"],
            event["event_type"],
            event["predicted_water_level"],
        )
        for event in events
    ]

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into tide_events (
                snapshot_id,
                location_id,
                event_time,
                event_type,
                predicted_water_level
            )
            values (?, ?, ?, ?, ?)
            """,
            rows,
        )

    return len(rows)


# insert the accepted binary tide phase for each forecast valid time
def insert_tide_phase_hourly(
    database_path: Path | str,
    snapshot_id: str,
    location_id: str,
    phases: list[dict[str, Any]],
) -> int:
    rows = [
        (
            snapshot_id,
            location_id,
            phase["forecast_time"],
            phase["phase"],
        )
        for phase in phases
    ]

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into tide_phase_hourly (
                snapshot_id,
                location_id,
                forecast_time,
                phase
            )
            values (?, ?, ?, ?)
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
