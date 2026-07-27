from pathlib import Path

import duckdb

from forecast_ops.config import load_config
from forecast_ops.database import initialize_database


# initialize the configured dev database and inspect its tables
config = load_config("dev")
database_path = Path(config["storage"]["database_path"])

initialize_database(database_path)

with duckdb.connect(str(database_path), read_only=True) as connection:
    tables = connection.execute(
        """
        select table_name
        from information_schema.tables
        where table_schema = 'main'
        order by table_name
        """
    ).fetchall()

print(f"database: {database_path}")
print("tables:")

for table_name, in tables:
    print(f"- {table_name}")