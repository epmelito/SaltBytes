from datetime import datetime, timezone
from pathlib import Path

import duckdb

from forecast_ops.api import fetch_forecast
from forecast_ops.config import load_config
from forecast_ops.database import (
    complete_pipeline_run,
    initialize_database,
    insert_forecast_hourly,
    insert_forecast_snapshot,
    insert_pipeline_run,
)
from forecast_ops.storage import create_run_id, write_raw_snapshot

# run one live dev load through raw storage and duckdb persistence
config = load_config("dev")
database_path = Path(config["storage"]["database_path"])
location = config["locations"][0]
run_id = create_run_id()
started_at = datetime.now(timezone.utc)

initialize_database(database_path)

insert_pipeline_run(
    database_path=database_path,
    run_id=run_id,
    environment=config["environment"],
    started_at=started_at,
)

payload = fetch_forecast(location, config["api"])

metadata = write_raw_snapshot(
    payload=payload,
    location_id=location["id"],
    raw_data_path=config["storage"]["raw_data_path"],
    run_id=run_id,
)

insert_forecast_snapshot(
    database_path=database_path,
    metadata=metadata,
)

rows_loaded = insert_forecast_hourly(
    database_path=database_path,
    snapshot_id=metadata["snapshot_id"],
    location_id=location["id"],
    payload=payload,
)

complete_pipeline_run(
    database_path=database_path,
    run_id=run_id,
    completed_at=datetime.now(timezone.utc),
    status="success",
    rows_loaded=rows_loaded,
)

with duckdb.connect(str(database_path), read_only=True) as connection:
    run = connection.execute(
        """
        select
            run_id,
            environment,
            status,
            rows_loaded
        from pipeline_runs
        where run_id = ?
        """,
        [run_id],
    ).fetchone()

    snapshot_count = connection.execute(
        """
        select count(*)
        from forecast_snapshots
        where run_id = ?
        """,
        [run_id],
    ).fetchone()

    hourly_count = connection.execute(
        """
        select count(*)
        from forecast_hourly
        where snapshot_id = ?
        """,
        [metadata["snapshot_id"]],
    ).fetchone()

print(f"database: {database_path}")
print(f"run: {run}")
print(f"snapshots: {snapshot_count[0] if snapshot_count else 0}")
print(f"hourly rows: {hourly_count[0] if hourly_count else 0}")