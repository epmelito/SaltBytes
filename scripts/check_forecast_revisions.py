from pathlib import Path

import duckdb

from forecast_ops.config import load_config
from forecast_ops.database import initialize_database

# inspect the latest forecast changes in the dev database
config = load_config("dev")
database_path = Path(config["storage"]["database_path"])

initialize_database(database_path)

with duckdb.connect(str(database_path), read_only=True) as connection:
    revisions = connection.execute(
        """
        select
            location_id,
            forecast_time,
            wind_speed_10m_change,
            wind_direction_10m,
            previous_wind_direction_10m,
            wind_gusts_10m_change,
            precipitation_probability_change,
            precipitation_change
        from forecast_revision_changes
        order by
            captured_at desc,
            location_id,
            forecast_time
        limit 20
        """
    ).fetchall()
    wave_revisions = connection.execute(
        """
        select
            location_id,
            forecast_time,
            wave_height_change,
            wave_direction,
            previous_wave_direction,
            wave_period_change
        from wave_revision_changes
        order by
            captured_at desc,
            location_id,
            forecast_time
        limit 20
        """
    ).fetchall()

print(f"database: {database_path}")
print(f"atmospheric revision rows: {len(revisions)}")

for revision in revisions:
    print(revision)

print(f"wave revision rows: {len(wave_revisions)}")

for revision in wave_revisions:
    print(revision)
