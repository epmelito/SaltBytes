from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pytest

from saltbytes.database import (
    _SCHEMA_SQL,
    complete_pipeline_run,
    initialize_database,
    insert_pipeline_run,
)
from scripts.validate_hosted_database import (
    HostedDatabaseValidationError,
    validate_hosted_database,
)

STARTED_AT = datetime(2026, 7, 31, 12, tzinfo=timezone.utc)
COMPLETED_AT = datetime(2026, 7, 31, 12, 5, tzinfo=timezone.utc)


def complete_run(
    database_path: Path,
    *,
    run_id: str = "run123",
    status: str = "success",
    rows_loaded: int = 168,
    error_message: str | None = None,
) -> None:
    insert_pipeline_run(
        database_path=database_path,
        run_id=run_id,
        started_at=STARTED_AT,
    )
    complete_pipeline_run(
        database_path=database_path,
        run_id=run_id,
        completed_at=COMPLETED_AT,
        status=status,
        rows_loaded=rows_loaded,
        error_message=error_message,
    )


def test_rejects_openable_unrelated_database(tmp_path: Path) -> None:
    database_path = tmp_path / "unrelated.duckdb"
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("create table unrelated (value integer)")

    with pytest.raises(
        HostedDatabaseValidationError,
        match="missing required schema objects",
    ):
        validate_hosted_database(database_path)


def test_rejects_missing_required_table(tmp_path: Path) -> None:
    database_path = tmp_path / "missing-table.duckdb"
    initialize_database(database_path)
    complete_run(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("drop view coastal_conditions_hourly")
        connection.execute("drop table source_results")

    with pytest.raises(
        HostedDatabaseValidationError,
        match="source_results",
    ):
        validate_hosted_database(database_path)


def test_rejects_missing_required_pipeline_run_column(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "missing-column.duckdb"
    schema_without_error_message = _SCHEMA_SQL.replace(
        "    rows_loaded integer not null default 0,\n"
        "    error_message varchar\n",
        "    rows_loaded integer not null default 0\n",
    )
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(schema_without_error_message)

    with pytest.raises(
        HostedDatabaseValidationError,
        match=r"pipeline_runs\.error_message",
    ):
        validate_hosted_database(database_path)


def test_rejects_database_without_pipeline_run(tmp_path: Path) -> None:
    database_path = tmp_path / "no-runs.duckdb"
    initialize_database(database_path)

    with pytest.raises(
        HostedDatabaseValidationError,
        match="no persisted pipeline run",
    ):
        validate_hosted_database(database_path)


def test_rejects_unfinished_latest_run(tmp_path: Path) -> None:
    database_path = tmp_path / "unfinished.duckdb"
    initialize_database(database_path)
    complete_run(database_path)
    insert_pipeline_run(
        database_path=database_path,
        run_id="unfinished",
        started_at=STARTED_AT + timedelta(hours=1),
    )

    with pytest.raises(
        HostedDatabaseValidationError,
        match="latest pipeline run is unfinished: unfinished",
    ):
        validate_hosted_database(database_path)


def test_rejects_invalid_latest_run_id(tmp_path: Path) -> None:
    database_path = tmp_path / "invalid-run-id.duckdb"
    initialize_database(database_path)
    complete_run(database_path, run_id="../outside")

    with pytest.raises(
        HostedDatabaseValidationError,
        match="invalid run ID",
    ):
        validate_hosted_database(database_path)


def test_accepts_completed_successful_run(tmp_path: Path) -> None:
    database_path = tmp_path / "success.duckdb"
    initialize_database(database_path)
    complete_run(database_path)

    validation = validate_hosted_database(database_path)

    assert validation.run_id == "run123"
    assert validation.raw_file_paths == ()


@pytest.mark.parametrize("rows_loaded", [0, 84])
def test_accepts_completed_failed_or_partial_run(
    tmp_path: Path,
    rows_loaded: int,
) -> None:
    database_path = tmp_path / f"failed-{rows_loaded}.duckdb"
    initialize_database(database_path)
    complete_run(
        database_path,
        status="failed",
        rows_loaded=rows_loaded,
        error_message="source request failed",
    )

    validate_hosted_database(database_path)
