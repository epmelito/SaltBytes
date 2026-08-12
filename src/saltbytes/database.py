import math
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


class SourcePersistenceError(RuntimeError):
    """Identify the failed stage of an atomic source persistence attempt."""

    def __init__(self, stage: str, error: Exception) -> None:
        self.stage = stage
        super().__init__(str(error))


def _database_connection(
    database_path: Path | str,
    connection: duckdb.DuckDBPyConnection | None,
) -> duckdb.DuckDBPyConnection | nullcontext[duckdb.DuckDBPyConnection]:
    if connection is not None:
        return nullcontext(connection)
    return duckdb.connect(str(database_path))

_SCHEMA_SQL = """
create table if not exists pipeline_runs (
    run_id varchar primary key,
    started_at timestamptz not null,
    completed_at timestamptz,
    status varchar not null,
    rows_loaded integer not null default 0,
    error_message varchar
);

create table if not exists run_locations (
    run_id varchar not null,
    location_id varchar not null,
    fishing_context varchar not null,
    shore_normal_azimuth_degrees double not null,
    pier_seaward_azimuth_degrees double,
    orientation_method varchar not null,
    orientation_source varchar not null,
    orientation_reviewed_at date not null,
    orientation_limitation varchar not null,
    primary key (run_id, location_id),
    foreign key (run_id) references pipeline_runs(run_id)
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
        status in (
            'success',
            'fetch_failed',
            'validation_failed',
            'persistence_failed'
        )
    ),
    detail varchar,
    recorded_at timestamptz not null,
    primary key (run_id, location_id, source),
    foreign key (run_id) references pipeline_runs(run_id)
);

create table if not exists fishing_observation_reports (
    report_id varchar primary key,
    source varchar not null,
    source_url varchar not null,
    content_hash varchar not null,
    report_time_text varchar,
    report_title varchar,
    location_id varchar not null,
    spatial_scope varchar not null,
    first_retrieved_at timestamptz not null,
    unique (source, source_url, content_hash)
);

create table if not exists fishing_observation_retrievals (
    report_id varchar not null,
    retrieved_at timestamptz not null,
    primary key (report_id, retrieved_at),
    foreign key (report_id) references fishing_observation_reports(report_id)
);

create table if not exists fishing_observation_assertions (
    assertion_id varchar primary key,
    report_id varchar not null,
    assertion_kind varchar not null,
    granularity varchar not null,
    evidence_basis varchar not null,
    observation_time_text varchar,
    raw_subject varchar,
    assertion_text varchar not null,
    foreign key (report_id) references fishing_observation_reports(report_id)
);

create table if not exists fishing_observation_review_candidates (
    candidate_id varchar primary key,
    report_id varchar not null,
    raw_segment varchar not null,
    reason varchar not null,
    unique (report_id, raw_segment, reason),
    foreign key (report_id) references fishing_observation_reports(report_id)
);

create table if not exists solar_context_hourly (
    run_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
    morning_twilight_start timestamptz,
    sunrise timestamptz,
    sunset timestamptz,
    evening_twilight_end timestamptz,
    solar_state varchar,
    minutes_from_sunrise integer,
    minutes_from_sunset integer,
    primary key (run_id, location_id, forecast_time),
    foreign key (run_id) references pipeline_runs(run_id)
);

create table if not exists run_location_solar_context (
    run_id varchar not null,
    location_id varchar not null,
    display_latitude double not null,
    display_longitude double not null,
    display_timezone varchar not null,
    calculation_contract varchar not null,
    calculation_library varchar not null,
    calculation_library_version varchar not null,
    primary key (run_id, location_id),
    foreign key (run_id) references pipeline_runs(run_id)
);

create table if not exists cloud_cover_hourly (
    snapshot_id varchar not null,
    location_id varchar not null,
    forecast_time timestamptz not null,
    cloud_cover double,
    primary key (snapshot_id, location_id, forecast_time),
    foreign key (snapshot_id) references forecast_snapshots(snapshot_id)
);

create or replace view tide_state_hourly as
with event_pairs as (
    select
        snapshot_id,
        location_id,
        event_time as previous_extremum_time,
        event_type as previous_extremum_type,
        predicted_water_level as previous_predicted_water_level,
        lead(event_time) over (
            partition by snapshot_id, location_id
            order by event_time
        ) as next_extremum_time,
        lead(event_type) over (
            partition by snapshot_id, location_id
            order by event_time
        ) as next_extremum_type,
        lead(predicted_water_level) over (
            partition by snapshot_id, location_id
            order by event_time
        ) as next_predicted_water_level
    from tide_events
)
select
    hourly.snapshot_id,
    hourly.location_id,
    hourly.forecast_time,
    hourly.phase,
    pairs.previous_extremum_time,
    pairs.previous_extremum_type,
    pairs.previous_predicted_water_level,
    pairs.next_extremum_time,
    pairs.next_extremum_type,
    pairs.next_predicted_water_level,
    date_diff(
        'minute',
        pairs.previous_extremum_time,
        hourly.forecast_time
    ) as minutes_since_previous_extremum,
    date_diff(
        'minute',
        hourly.forecast_time,
        pairs.next_extremum_time
    ) as minutes_until_next_extremum,
    abs(
        pairs.next_predicted_water_level
        - pairs.previous_predicted_water_level
    ) as predicted_tidal_range
from tide_phase_hourly as hourly
left join event_pairs as pairs
    on pairs.snapshot_id = hourly.snapshot_id
    and pairs.location_id = hourly.location_id
    and pairs.previous_extremum_time <= hourly.forecast_time
    and hourly.forecast_time < pairs.next_extremum_time;

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
    from tide_state_hourly as hourly
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
cloud_rows as (
    select
        snapshots.run_id,
        hourly.location_id,
        hourly.forecast_time,
        hourly.cloud_cover
    from cloud_cover_hourly as hourly
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
        hourly.phase,
        hourly.previous_extremum_time,
        hourly.previous_extremum_type,
        hourly.previous_predicted_water_level,
        hourly.next_extremum_time,
        hourly.next_extremum_type,
        hourly.next_predicted_water_level,
        hourly.minutes_since_previous_extremum,
        hourly.minutes_until_next_extremum,
        hourly.predicted_tidal_range
    from tide_state_hourly as hourly
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
    run_locations.shore_normal_azimuth_degrees,
    hourly_keys.forecast_time,
    weather_rows.snapshot_id as weather_snapshot_id,
    weather_rows.precipitation_probability,
    weather_rows.wind_speed_10m,
    weather_rows.wind_direction_10m,
    case
        when weather_rows.wind_direction_10m is null
            or run_locations.shore_normal_azimuth_degrees is null
        then null
        else mod(
            weather_rows.wind_direction_10m
            - run_locations.shore_normal_azimuth_degrees
            + 540,
            360
        ) - 180
    end as wind_to_shore_angle_degrees,
    weather_rows.wind_gusts_10m,
    weather_rows.precipitation,
    cloud_rows.cloud_cover,
    weather_results.status as weather_status,
    wave_rows.snapshot_id as wave_snapshot_id,
    wave_rows.wave_height,
    wave_rows.wave_direction,
    case
        when wave_rows.wave_direction is null
            or run_locations.shore_normal_azimuth_degrees is null
        then null
        else mod(
            wave_rows.wave_direction
            - run_locations.shore_normal_azimuth_degrees
            + 540,
            360
        ) - 180
    end as wave_to_shore_angle_degrees,
    wave_rows.wave_period,
    wave_results.status as wave_status,
    sst_rows.snapshot_id as sst_snapshot_id,
    sst_rows.sea_surface_temperature,
    sst_results.status as sst_status,
    tide_rows.snapshot_id as tide_snapshot_id,
    tide_rows.phase as tide_phase,
    tide_rows.previous_extremum_time as tide_previous_extremum_time,
    tide_rows.previous_extremum_type as tide_previous_extremum_type,
    tide_rows.previous_predicted_water_level
        as tide_previous_predicted_water_level,
    tide_rows.next_extremum_time as tide_next_extremum_time,
    tide_rows.next_extremum_type as tide_next_extremum_type,
    tide_rows.next_predicted_water_level
        as tide_next_predicted_water_level,
    tide_rows.minutes_since_previous_extremum
        as tide_minutes_since_previous_extremum,
    tide_rows.minutes_until_next_extremum
        as tide_minutes_until_next_extremum,
    tide_rows.predicted_tidal_range as tide_predicted_range,
    tide_results.status as tide_status,
    solar_rows.morning_twilight_start,
    solar_rows.sunrise,
    solar_rows.sunset,
    solar_rows.evening_twilight_end,
    solar_rows.solar_state,
    solar_rows.minutes_from_sunrise,
    solar_rows.minutes_from_sunset
from hourly_keys
inner join pipeline_runs as runs
    on runs.run_id = hourly_keys.run_id
left join run_locations
    on run_locations.run_id = hourly_keys.run_id
    and run_locations.location_id = hourly_keys.location_id
left join weather_rows
    on weather_rows.run_id = hourly_keys.run_id
    and weather_rows.location_id = hourly_keys.location_id
    and weather_rows.forecast_time = hourly_keys.forecast_time
left join wave_rows
    on wave_rows.run_id = hourly_keys.run_id
    and wave_rows.location_id = hourly_keys.location_id
    and wave_rows.forecast_time = hourly_keys.forecast_time
left join cloud_rows
    on cloud_rows.run_id = hourly_keys.run_id
    and cloud_rows.location_id = hourly_keys.location_id
    and cloud_rows.forecast_time = hourly_keys.forecast_time
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
    and tide_results.source = 'tide'
left join solar_context_hourly as solar_rows
    on solar_rows.run_id = hourly_keys.run_id
    and solar_rows.location_id = hourly_keys.location_id
    and solar_rows.forecast_time = hourly_keys.forecast_time;

create or replace view analysis_ready_features_hourly as
with feature_rows as (
    select
        conditions.*,
        coalesce(conditions.weather_status = 'success'
            and conditions.weather_snapshot_id is not null
            and conditions.precipitation_probability is not null
            and conditions.wind_speed_10m is not null
            and conditions.wind_direction_10m is not null
            and conditions.wind_gusts_10m is not null
            and conditions.precipitation is not null, false) as weather_available,
        coalesce(conditions.wave_status = 'success'
            and conditions.wave_snapshot_id is not null
            and conditions.wave_height is not null
            and conditions.wave_direction is not null
            and conditions.wave_period is not null, false) as wave_available,
        coalesce(conditions.sst_status = 'success'
            and conditions.sst_snapshot_id is not null
            and conditions.sea_surface_temperature is not null, false) as sst_available,
        coalesce(conditions.tide_status = 'success'
            and conditions.tide_snapshot_id is not null
            and conditions.tide_phase is not null, false) as tide_available,
        coalesce(conditions.tide_status = 'success'
            and conditions.tide_snapshot_id is not null
            and conditions.tide_phase is not null
            and conditions.tide_previous_extremum_time is not null
            and conditions.tide_previous_extremum_type is not null
            and conditions.tide_previous_predicted_water_level is not null
            and conditions.tide_next_extremum_time is not null
            and conditions.tide_next_extremum_type is not null
            and conditions.tide_next_predicted_water_level is not null
            and conditions.tide_minutes_since_previous_extremum is not null
            and conditions.tide_minutes_until_next_extremum is not null
            and conditions.tide_predicted_range is not null, false) as tide_context_available,
        coalesce(conditions.weather_status = 'success'
            and conditions.weather_snapshot_id is not null
            and conditions.cloud_cover is not null, false) as cloud_cover_available
    from coastal_conditions_hourly as conditions
),
six_hour_windows as (
    select
        feature_rows.run_id,
        feature_rows.location_id,
        feature_rows.forecast_time,
        count(six_hour_values.forecast_time) = 6
            and count(six_hour_values.precipitation) = 6
            as precipitation_6h_complete,
        case
            when count(six_hour_values.forecast_time) = 6
                and count(six_hour_values.precipitation) = 6
            then sum(six_hour_values.precipitation)
        end as precipitation_6h
    from feature_rows
    cross join lateral generate_series(
        feature_rows.forecast_time - interval '5 hours',
        feature_rows.forecast_time,
        interval '1 hour'
    ) as six_hour_window(forecast_time)
    left join coastal_conditions_hourly as six_hour_values
        on six_hour_values.run_id = feature_rows.run_id
        and six_hour_values.location_id = feature_rows.location_id
        and six_hour_values.weather_snapshot_id = feature_rows.weather_snapshot_id
        and six_hour_values.forecast_time = six_hour_window.forecast_time
    group by
        feature_rows.run_id,
        feature_rows.location_id,
        feature_rows.forecast_time
),
twenty_four_hour_windows as (
    select
        feature_rows.run_id,
        feature_rows.location_id,
        feature_rows.forecast_time,
        count(twenty_four_hour_values.forecast_time) = 24
            and count(twenty_four_hour_values.precipitation) = 24
            as precipitation_24h_complete,
        case
            when count(twenty_four_hour_values.forecast_time) = 24
                and count(twenty_four_hour_values.precipitation) = 24
            then sum(twenty_four_hour_values.precipitation)
        end as precipitation_24h
    from feature_rows
    cross join lateral generate_series(
        feature_rows.forecast_time - interval '23 hours',
        feature_rows.forecast_time,
        interval '1 hour'
    ) as twenty_four_hour_window(forecast_time)
    left join coastal_conditions_hourly as twenty_four_hour_values
        on twenty_four_hour_values.run_id = feature_rows.run_id
        and twenty_four_hour_values.location_id = feature_rows.location_id
        and twenty_four_hour_values.weather_snapshot_id = feature_rows.weather_snapshot_id
        and twenty_four_hour_values.forecast_time = twenty_four_hour_window.forecast_time
    group by
        feature_rows.run_id,
        feature_rows.location_id,
        feature_rows.forecast_time
)
select
    feature_rows.*,
    six_hour_windows.precipitation_6h,
    six_hour_windows.precipitation_6h_complete,
    twenty_four_hour_windows.precipitation_24h,
    twenty_four_hour_windows.precipitation_24h_complete,
    feature_rows.weather_available
        and feature_rows.wave_available
        and feature_rows.sst_available
        and feature_rows.tide_available
        and feature_rows.wind_to_shore_angle_degrees is not null
        and feature_rows.wave_to_shore_angle_degrees is not null
        and feature_rows.tide_context_available
        and six_hour_windows.precipitation_6h_complete
        and twenty_four_hour_windows.precipitation_24h_complete
        as technically_eligible
from feature_rows
inner join six_hour_windows
    on six_hour_windows.run_id = feature_rows.run_id
    and six_hour_windows.location_id = feature_rows.location_id
    and six_hour_windows.forecast_time = feature_rows.forecast_time
inner join twenty_four_hour_windows
    on twenty_four_hour_windows.run_id = feature_rows.run_id
    and twenty_four_hour_windows.location_id = feature_rows.location_id
    and twenty_four_hour_windows.forecast_time = feature_rows.forecast_time;
"""

# create the database file and required tables
def initialize_database(database_path: Path | str) -> None:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("begin transaction")

        try:
            connection.execute(_SCHEMA_SQL)
            _migrate_source_result_statuses(connection)
        except Exception:
            connection.execute("rollback")
            raise
        else:
            connection.execute("commit")


def _migrate_source_result_statuses(connection: duckdb.DuckDBPyConnection) -> None:
    supported_statuses = connection.execute(
        """
        select constraint_text
        from duckdb_constraints()
        where table_name = 'source_results'
            and constraint_type = 'CHECK'
        """
    ).fetchall()

    if any("persistence_failed" in constraint[0] for constraint in supported_statuses):
        return

    connection.execute("alter table source_results rename to source_results_legacy")
    connection.execute(
        """
        create table source_results (
            run_id varchar not null,
            location_id varchar not null,
            source varchar not null,
            status varchar not null check (
                status in (
                    'success',
                    'fetch_failed',
                    'validation_failed',
                    'persistence_failed'
                )
            ),
            detail varchar,
            recorded_at timestamptz not null,
            primary key (run_id, location_id, source),
            foreign key (run_id) references pipeline_runs(run_id)
        )
        """
    )
    connection.execute(
        """
        insert into source_results
        select * from source_results_legacy
        """
    )
    connection.execute("drop table source_results_legacy")


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


# persist the configured location reference frame for one run
def insert_run_locations(
    database_path: Path | str,
    run_id: str,
    locations: list[dict[str, Any]],
) -> None:
    rows = []

    for location in locations:
        orientation = location["orientation"]
        rows.append(
            (
                run_id,
                location["id"],
                location["fishing_context"],
                orientation["shore_normal_azimuth_degrees"],
                orientation["pier_seaward_azimuth_degrees"],
                orientation["orientation_method"],
                orientation["orientation_source"],
                orientation["orientation_reviewed_at"],
                orientation["orientation_limitation"],
            )
        )

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("begin transaction")

        try:
            connection.executemany(
                """
                insert into run_locations (
                    run_id,
                    location_id,
                    fishing_context,
                    shore_normal_azimuth_degrees,
                    pier_seaward_azimuth_degrees,
                    orientation_method,
                    orientation_source,
                    orientation_reviewed_at,
                    orientation_limitation
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        except Exception:
            connection.execute("rollback")
            raise
        else:
            connection.execute("commit")


def insert_solar_context_hourly(
    database_path: Path | str,
    run_id: str,
    location_id: str,
    contexts: list[dict[str, Any]],
) -> int:
    rows = [
        (
            run_id,
            location_id,
            context["forecast_time"],
            context["morning_twilight_start"],
            context["sunrise"],
            context["sunset"],
            context["evening_twilight_end"],
            context["solar_state"],
            context["minutes_from_sunrise"],
            context["minutes_from_sunset"],
        )
        for context in contexts
    ]

    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into solar_context_hourly values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    return len(rows)


def insert_run_location_solar_context(
    database_path: Path | str,
    run_id: str,
    locations: list[dict[str, Any]],
    display_timezone: str,
    solar_provenance: dict[str, str],
) -> None:
    rows = [
        (
            run_id,
            location["id"],
            location["display_coordinate"]["latitude"],
            location["display_coordinate"]["longitude"],
            display_timezone,
            solar_provenance["calculation_contract"],
            solar_provenance["calculation_library"],
            solar_provenance["calculation_library_version"],
        )
        for location in locations
    ]
    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into run_location_solar_context values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


# insert metadata for one raw forecast snapshot
def insert_forecast_snapshot(
    database_path: Path | str,
    metadata: dict[str, Any],
    connection: duckdb.DuckDBPyConnection | None = None,
) -> None:
    with _database_connection(database_path, connection) as database_connection:
        database_connection.execute(
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
    connection: duckdb.DuckDBPyConnection | None = None,
) -> None:
    valid_statuses = {
        "success",
        "fetch_failed",
        "validation_failed",
        "persistence_failed",
    }

    if status not in valid_statuses:
        raise ValueError(f"unsupported source result status: {status}")

    with _database_connection(database_path, connection) as database_connection:
        database_connection.execute(
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
    connection: duckdb.DuckDBPyConnection | None = None,
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

    cloud_values = hourly.get("cloud_cover")
    cloud_values_are_complete = (
        isinstance(cloud_values, list)
        and len(cloud_values) == len(forecast_times)
    )

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

    with _database_connection(database_path, connection) as database_connection:
        database_connection.executemany(
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
        database_connection.executemany(
            """
            insert into cloud_cover_hourly values (?, ?, ?, ?)
            """,
            [
                (
                    snapshot_id,
                    location_id,
                    forecast_time,
                    _cloud_cover_value(cloud_values[index])
                    if cloud_values_are_complete
                    else None,
                )
                for index, forecast_time in enumerate(normalized_times)
            ],
        )

    return len(rows)


def _cloud_cover_value(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    cloud_cover = float(value)
    if not math.isfinite(cloud_cover) or not 0 <= cloud_cover <= 100:
        return None
    return cloud_cover


# insert normalized hourly wave rows for one snapshot
def insert_wave_hourly(
    database_path: Path | str,
    snapshot_id: str,
    location_id: str,
    payload: dict[str, Any],
    connection: duckdb.DuckDBPyConnection | None = None,
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

    with _database_connection(database_path, connection) as database_connection:
        database_connection.executemany(
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
    connection: duckdb.DuckDBPyConnection | None = None,
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

    with _database_connection(database_path, connection) as database_connection:
        database_connection.executemany(
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
    connection: duckdb.DuckDBPyConnection | None = None,
) -> None:
    request_begin_date = datetime.strptime(
        request_provenance["begin_date"],
        "%Y%m%d",
    ).date()
    request_end_date = datetime.strptime(
        request_provenance["end_date"],
        "%Y%m%d",
    ).date()

    if connection is not None:
        _insert_tide_snapshot(
            connection,
            metadata,
            request_provenance,
            relationship,
            request_begin_date,
            request_end_date,
        )
        return

    with duckdb.connect(str(database_path)) as database_connection:
        database_connection.execute("begin transaction")

        try:
            _insert_tide_snapshot(
                database_connection,
                metadata,
                request_provenance,
                relationship,
                request_begin_date,
                request_end_date,
            )
        except Exception:
            database_connection.execute("rollback")
            raise
        else:
            database_connection.execute("commit")


def _insert_tide_snapshot(
    connection: duckdb.DuckDBPyConnection,
    metadata: dict[str, Any],
    request_provenance: dict[str, Any],
    relationship: dict[str, Any],
    request_begin_date: Any,
    request_end_date: Any,
) -> None:
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


# insert normalized NOAA high and low events for one tide snapshot
def insert_tide_events(
    database_path: Path | str,
    snapshot_id: str,
    location_id: str,
    events: list[dict[str, Any]],
    connection: duckdb.DuckDBPyConnection | None = None,
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

    with _database_connection(database_path, connection) as database_connection:
        database_connection.executemany(
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
    connection: duckdb.DuckDBPyConnection | None = None,
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

    with _database_connection(database_path, connection) as database_connection:
        database_connection.executemany(
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


def persist_source_success(
    database_path: Path | str,
    run_id: str,
    location_id: str,
    source: str,
    metadata: dict[str, Any],
    payload: dict[str, Any],
    recorded_at: datetime,
    tide_events: list[dict[str, Any]] | None = None,
    tide_phases: list[dict[str, Any]] | None = None,
    request_provenance: dict[str, Any] | None = None,
    relationship: dict[str, Any] | None = None,
) -> int:
    """Commit one source's database evidence and success result together."""
    stage = "snapshot metadata"

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("begin transaction")

        try:
            if source == "weather":
                stage = "snapshot metadata"
                insert_forecast_snapshot(
                    database_path,
                    metadata,
                    connection=connection,
                )
                stage = "normalized rows"
                rows_loaded = insert_forecast_hourly(
                    database_path,
                    metadata["snapshot_id"],
                    location_id,
                    payload,
                    connection=connection,
                )
            elif source == "wave":
                stage = "snapshot metadata"
                insert_forecast_snapshot(
                    database_path,
                    metadata,
                    connection=connection,
                )
                stage = "normalized rows"
                rows_loaded = insert_wave_hourly(
                    database_path,
                    metadata["snapshot_id"],
                    location_id,
                    payload,
                    connection=connection,
                )
            elif source == "sst":
                stage = "snapshot metadata"
                insert_forecast_snapshot(
                    database_path,
                    metadata,
                    connection=connection,
                )
                stage = "normalized rows"
                rows_loaded = insert_sst_hourly(
                    database_path,
                    metadata["snapshot_id"],
                    location_id,
                    payload,
                    connection=connection,
                )
            elif source == "tide":
                if (
                    tide_events is None
                    or tide_phases is None
                    or request_provenance is None
                    or relationship is None
                ):
                    raise ValueError("tide persistence requires provenance and rows")
                stage = "snapshot provenance"
                insert_tide_snapshot(
                    database_path,
                    metadata,
                    request_provenance,
                    relationship,
                    connection=connection,
                )
                stage = "normalized events"
                event_rows = insert_tide_events(
                    database_path,
                    metadata["snapshot_id"],
                    location_id,
                    tide_events,
                    connection=connection,
                )
                stage = "normalized phases"
                phase_rows = insert_tide_phase_hourly(
                    database_path,
                    metadata["snapshot_id"],
                    location_id,
                    tide_phases,
                    connection=connection,
                )
                rows_loaded = event_rows + phase_rows
            else:
                raise ValueError(f"unsupported source: {source}")

            stage = "source result"
            insert_source_result(
                database_path=database_path,
                run_id=run_id,
                location_id=location_id,
                source=source,
                status="success",
                detail=None,
                recorded_at=recorded_at,
                connection=connection,
            )
            stage = "transaction commit"
            connection.execute("commit")
        except Exception as error:
            try:
                connection.execute("rollback")
            except Exception:
                pass
            raise SourcePersistenceError(stage, error) from error

    return rows_loaded


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
