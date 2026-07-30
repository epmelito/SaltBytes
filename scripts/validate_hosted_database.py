import sys
from pathlib import Path

import duckdb

from saltbytes.database import _SCHEMA_SQL

_TERMINAL_RUN_STATUSES = {"failed", "success"}


class HostedDatabaseValidationError(ValueError):
    pass


def _schema_contract(
    connection: duckdb.DuckDBPyConnection,
) -> dict[str, tuple[str, set[str]]]:
    rows = connection.execute(
        """
        select
            tables.table_name,
            tables.table_type,
            columns.column_name
        from information_schema.tables as tables
        left join information_schema.columns as columns
            on columns.table_schema = tables.table_schema
            and columns.table_name = tables.table_name
        where tables.table_schema = 'main'
        order by tables.table_name, columns.ordinal_position
        """
    ).fetchall()
    contract: dict[str, tuple[str, set[str]]] = {}

    for table_name, table_type, column_name in rows:
        if table_name not in contract:
            contract[table_name] = (table_type, set())
        if column_name is not None:
            contract[table_name][1].add(column_name)

    return contract


def _required_schema_contract() -> dict[str, tuple[str, set[str]]]:
    with duckdb.connect(":memory:") as connection:
        connection.execute(_SCHEMA_SQL)
        return _schema_contract(connection)


def validate_hosted_database(database_path: Path | str) -> None:
    database_path = Path(database_path)

    if not database_path.is_file():
        raise HostedDatabaseValidationError(
            f"database file does not exist: {database_path}"
        )

    try:
        with duckdb.connect(str(database_path), read_only=True) as connection:
            required_schema = _required_schema_contract()
            actual_schema = _schema_contract(connection)

            missing_objects = sorted(
                set(required_schema) - set(actual_schema)
            )
            if missing_objects:
                raise HostedDatabaseValidationError(
                    "database is missing required schema objects: "
                    + ", ".join(missing_objects)
                )

            wrong_object_types = sorted(
                table_name
                for table_name, (table_type, _) in required_schema.items()
                if actual_schema[table_name][0] != table_type
            )
            if wrong_object_types:
                raise HostedDatabaseValidationError(
                    "database has invalid schema object types: "
                    + ", ".join(wrong_object_types)
                )

            missing_columns = sorted(
                f"{table_name}.{column_name}"
                for table_name, (_, required_columns) in required_schema.items()
                for column_name in (
                    required_columns - actual_schema[table_name][1]
                )
            )
            if missing_columns:
                raise HostedDatabaseValidationError(
                    "database is missing required columns: "
                    + ", ".join(missing_columns)
                )

            latest_run = connection.execute(
                """
                select run_id, completed_at, status
                from pipeline_runs
                order by started_at desc, run_id desc
                limit 1
                """
            ).fetchone()

            if latest_run is None:
                raise HostedDatabaseValidationError(
                    "database has no persisted pipeline run"
                )

            run_id, completed_at, status = latest_run
            if (
                completed_at is None
                or status not in _TERMINAL_RUN_STATUSES
            ):
                raise HostedDatabaseValidationError(
                    f"latest pipeline run is unfinished: {run_id}"
                )
    except duckdb.Error as error:
        raise HostedDatabaseValidationError(
            f"database cannot be validated: {error}"
        ) from error


def main(argv: list[str] | None = None) -> int:
    arguments = argv or sys.argv[1:]

    if len(arguments) != 1:
        print(
            "usage: validate_hosted_database.py <database-path>",
            file=sys.stderr,
        )
        return 2

    try:
        validate_hosted_database(arguments[0])
    except HostedDatabaseValidationError as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
