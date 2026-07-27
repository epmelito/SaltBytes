from pathlib import Path

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