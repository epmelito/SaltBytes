import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import duckdb

from saltbytes.database import _SCHEMA_SQL

_TERMINAL_RUN_STATUSES = {"failed", "success"}
_VALID_RUN_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class HostedDatabaseValidationError(ValueError):
    pass


@dataclass(frozen=True)
class HostedDatabaseValidation:
    run_id: str
    raw_file_paths: tuple[str, ...]


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


def validate_hosted_database(
    database_path: Path | str,
) -> HostedDatabaseValidation:
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
            if not _VALID_RUN_ID.fullmatch(run_id):
                raise HostedDatabaseValidationError(
                    f"latest pipeline run has an invalid run ID: {run_id}"
                )
            if (
                completed_at is None
                or status not in _TERMINAL_RUN_STATUSES
            ):
                raise HostedDatabaseValidationError(
                    f"latest pipeline run is unfinished: {run_id}"
                )

            raw_file_paths = tuple(
                row[0]
                for row in connection.execute(
                    """
                    select raw_file_path
                    from forecast_snapshots
                    where run_id = ?
                    order by snapshot_id
                    """,
                    [run_id],
                ).fetchall()
            )

            return HostedDatabaseValidation(
                run_id=run_id,
                raw_file_paths=raw_file_paths,
            )
    except duckdb.Error as error:
        raise HostedDatabaseValidationError(
            f"database cannot be validated: {error}"
        ) from error


def _resolved_local_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def audit_raw_publication(
    validation: HostedDatabaseValidation,
    raw_root: Path | str,
    published_paths_file: Path | str,
) -> tuple[list[str], int]:
    raw_root_path = _resolved_local_path(str(raw_root))
    published_values = Path(published_paths_file).read_bytes().split(b"\0")
    published_paths = {
        _resolved_local_path(os.fsdecode(value))
        for value in published_values
        if value
    }
    failures: list[str] = []

    for raw_file_path in validation.raw_file_paths:
        encoded_path = json.dumps(raw_file_path, ensure_ascii=True)
        if not raw_file_path or "\0" in raw_file_path:
            failures.append(f"unsafe_raw_reference={encoded_path}")
            continue

        try:
            resolved_path = _resolved_local_path(raw_file_path)
        except (OSError, ValueError):
            failures.append(f"unsafe_raw_reference={encoded_path}")
            continue

        if not resolved_path.is_relative_to(raw_root_path):
            failures.append(f"outside_raw_root_reference={encoded_path}")
        elif not resolved_path.is_file():
            failures.append(f"missing_raw_reference={encoded_path}")
        elif resolved_path not in published_paths:
            failures.append(f"unpublished_raw_reference={encoded_path}")

    return failures, len(validation.raw_file_paths)


def main(argv: list[str] | None = None) -> int:
    arguments = argv or sys.argv[1:]

    if len(arguments) not in {1, 4}:
        print(
            "usage: validate_hosted_database.py <database-path> "
            "[<raw-root> <published-paths-file> <failure-output>]",
            file=sys.stderr,
        )
        return 2

    try:
        validation = validate_hosted_database(arguments[0])
    except HostedDatabaseValidationError as error:
        print(error, file=sys.stderr)
        return 1

    if len(arguments) == 4:
        failures, expected_count = audit_raw_publication(
            validation,
            raw_root=arguments[1],
            published_paths_file=arguments[2],
        )
        Path(arguments[3]).write_text(
            "".join(f"{failure}\n" for failure in failures),
            encoding="utf-8",
        )
        print(
            "raw reference verification: "
            f"expected={expected_count} "
            f"verified={expected_count - len(failures)} "
            f"failed={len(failures)}",
            file=sys.stderr,
        )

    print(validation.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
