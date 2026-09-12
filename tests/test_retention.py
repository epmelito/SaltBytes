from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pytest

import saltbytes.database as database_module
from saltbytes.database import apply_environmental_retention, initialize_database
from scripts.validate_hosted_database import validate_hosted_database

NOW = datetime(2026, 9, 12, 12, tzinfo=timezone.utc)
NORMALIZED_TABLES = (
    "tide_events",
    "tide_phase_hourly",
    "forecast_hourly",
    "wave_hourly",
    "sst_hourly",
    "cloud_cover_hourly",
    "atmospheric_context_hourly",
    "pressure_context_hourly",
    "solar_context_hourly",
)
METADATA_TABLES = (
    "tide_snapshots",
    "forecast_snapshots",
    "source_results",
    "run_location_solar_context",
    "run_locations",
    "pipeline_runs",
)


def _seed_environmental_run(
    connection: duckdb.DuckDBPyConnection,
    run_id: str,
    started_at: datetime,
    status: str,
) -> None:
    snapshot_id = f"snapshot-{run_id}"
    location_id = "test-location"
    forecast_time = started_at + timedelta(hours=1)
    connection.execute(
        "insert into pipeline_runs values (?, ?, ?, ?, 9, null)",
        [run_id, started_at, started_at + timedelta(minutes=5), status],
    )
    connection.execute(
        """
        insert into run_locations values (
            ?, ?, 'pier', 90, 90, 'reviewed', 'test', date '2026-01-01', 'none'
        )
        """,
        [run_id, location_id],
    )
    connection.execute(
        """
        insert into forecast_snapshots values (
            ?, ?, ?, ?, ?, null, null, null, null, null
        )
        """,
        [snapshot_id, run_id, location_id, started_at, f"data/raw/{run_id}.json"],
    )
    connection.execute(
        "insert into source_results values (?, ?, 'weather', 'success', null, ?)",
        [run_id, location_id, started_at],
    )
    connection.execute(
        """
        insert into run_location_solar_context values (
            ?, ?, 35.9, -75.6, 'America/New_York',
            'civil twilight', 'astral', '3.2'
        )
        """,
        [run_id, location_id],
    )
    connection.execute(
        """
        insert into solar_context_hourly values (
            ?, ?, ?, ?, ?, ?, ?, 'daylight', 60, -600
        )
        """,
        [
            run_id,
            location_id,
            forecast_time,
            started_at,
            started_at,
            started_at + timedelta(hours=10),
            started_at + timedelta(hours=11),
        ],
    )
    connection.execute(
        "insert into forecast_hourly values (?, ?, ?, 10, 12, 90, 15, 0)",
        [snapshot_id, location_id, forecast_time],
    )
    connection.execute(
        "insert into wave_hourly values (?, ?, ?, 1, 90, 8)",
        [snapshot_id, location_id, forecast_time],
    )
    connection.execute(
        "insert into sst_hourly values (?, ?, ?, 24)",
        [snapshot_id, location_id, forecast_time],
    )
    connection.execute(
        "insert into cloud_cover_hourly values (?, ?, ?, 20)",
        [snapshot_id, location_id, forecast_time],
    )
    connection.execute(
        "insert into atmospheric_context_hourly values (?, ?, ?, 22, 23)",
        [snapshot_id, location_id, forecast_time],
    )
    connection.execute(
        "insert into pressure_context_hourly values (?, ?, ?, 1013)",
        [snapshot_id, location_id, forecast_time],
    )
    connection.execute(
        """
        insert into tide_snapshots (
            snapshot_id, station_id, prediction_location, relationship_type,
            product, interval, datum, time_zone, units, response_format,
            request_begin_date, request_end_date, distance_km,
            coastal_relationship, known_limitation
        ) values (
            ?, 'station', 'test', 'reference', 'predictions', 'hilo',
            'MLLW', 'gmt', 'metric', 'json', date '2026-01-01',
            date '2026-01-02', 1, 'same coast', 'none'
        )
        """,
        [snapshot_id],
    )
    connection.execute(
        "insert into tide_events values (?, ?, ?, 'high', 1)",
        [snapshot_id, location_id, forecast_time],
    )
    connection.execute(
        "insert into tide_phase_hourly values (?, ?, ?, 'falling')",
        [snapshot_id, location_id, forecast_time],
    )


def _seed_observation_state(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        insert into fishing_observation_reports values (
            'report', 'source', 'https://example.com/report', 'hash', 'today',
            'report title', 'test-location', 'pier', ?
        )
        """,
        [NOW - timedelta(days=200)],
    )
    connection.execute(
        "insert into fishing_observation_retrievals values ('report', ?)",
        [NOW - timedelta(days=199)],
    )
    connection.execute(
        """
        insert into fishing_observation_assertions values (
            'assertion', 'report', 'catch', 'report', 'explicit', 'today',
            'fish', 'fish reported'
        )
        """
    )
    connection.execute(
        """
        insert into fishing_observation_review_candidates values (
            'candidate', 'report', 'possible fish', 'fishing terminology'
        )
        """
    )
    connection.execute(
        """
        insert into fishing_observation_review_patterns values (
            'pattern', 'source', 'fishing terminology', 'possible fish',
            'accepted_for_parser', ?
        )
        """,
        [NOW - timedelta(days=150)],
    )
    connection.execute(
        "insert into fishing_observation_review_candidate_patterns values ('candidate', 'pattern')"
    )
    connection.execute(
        """
        insert into fishing_observation_ingestion_attempts values (
            'attempt', 'source', ?, 'success', 1, 0, 1
        )
        """,
        [NOW - timedelta(days=200)],
    )


def _run_ids(connection: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    if table_name == "solar_context_hourly":
        query = "select run_id from solar_context_hourly"
    else:
        query = f"""
            select snapshots.run_id
            from {table_name} as retained
            inner join forecast_snapshots as snapshots using (snapshot_id)
        """
    return {row[0] for row in connection.execute(query).fetchall()}


def _metadata_run_ids(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> set[str]:
    if table_name == "tide_snapshots":
        query = """
            select snapshots.run_id
            from tide_snapshots
            inner join forecast_snapshots as snapshots using (snapshot_id)
        """
    else:
        query = f"select run_id from {table_name}"
    return {row[0] for row in connection.execute(query).fetchall()}


def test_retention_applies_7_and_90_day_windows_and_preserves_observations(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "retention.duckdb"
    initialize_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        _seed_environmental_run(connection, "recent-success", NOW - timedelta(days=1), "success")
        _seed_environmental_run(connection, "metadata-only", NOW - timedelta(days=30), "failed")
        _seed_environmental_run(connection, "expired", NOW - timedelta(days=100), "failed")
        _seed_observation_state(connection)

    result = apply_environmental_retention(database_path, as_of=NOW)

    assert result.protected_run_id == "recent-success"
    assert result.normalized_rows_removed == 18
    assert result.metadata_rows_removed == 6
    assert result.database_size_before > 0
    assert result.database_size_after > 0
    with duckdb.connect(str(database_path), read_only=True) as connection:
        for table_name in NORMALIZED_TABLES:
            assert _run_ids(connection, table_name) == {"recent-success"}
        for table_name in METADATA_TABLES:
            assert _metadata_run_ids(connection, table_name) == {
                "recent-success",
                "metadata-only",
            }
        observation_counts = connection.execute(
            """
            select
                (select count(*) from fishing_observation_reports),
                (select count(*) from fishing_observation_retrievals),
                (select count(*) from fishing_observation_assertions),
                (select count(*) from fishing_observation_review_candidates),
                (select count(*) from fishing_observation_review_patterns),
                (select count(*) from fishing_observation_review_candidate_patterns),
                (select count(*) from fishing_observation_ingestion_attempts)
            """
        ).fetchone()
        disposition = connection.execute(
            "select disposition from fishing_observation_review_patterns"
        ).fetchone()

    assert observation_counts == (1, 1, 1, 1, 1, 1, 1)
    assert disposition == ("accepted_for_parser",)
    validate_hosted_database(database_path)

    second_result = apply_environmental_retention(database_path, as_of=NOW)
    assert second_result.normalized_rows_removed == 0
    assert second_result.metadata_rows_removed == 0


def test_retention_preserves_only_the_latest_completed_success_when_it_is_old(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "protected-success.duckdb"
    initialize_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        _seed_environmental_run(connection, "expired-failure", NOW - timedelta(days=130), "failed")
        _seed_environmental_run(
            connection,
            "protected-success",
            NOW - timedelta(days=120),
            "success",
        )
        _seed_environmental_run(connection, "recent-failure", NOW - timedelta(days=1), "failed")

    result = apply_environmental_retention(database_path, as_of=NOW)

    assert result.protected_run_id == "protected-success"
    assert result.normalized_rows_removed == 9
    assert result.metadata_rows_removed == 6
    with duckdb.connect(str(database_path), read_only=True) as connection:
        for table_name in NORMALIZED_TABLES:
            assert _run_ids(connection, table_name) == {
                "protected-success",
                "recent-failure",
            }
        latest_success = connection.execute(
            """
            select run_id
            from pipeline_runs
            where status = 'success' and completed_at is not null
            order by started_at desc, run_id desc
            limit 1
            """
        ).fetchone()
        protected_conditions = connection.execute(
            """
            select count(*)
            from coastal_conditions_hourly
            where run_id = 'protected-success'
            """
        ).fetchone()

    assert latest_success == ("protected-success",)
    assert protected_conditions == (1,)
    validate_hosted_database(database_path)


def test_working_copy_stage_failure_leaves_original_database_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "rollback.duckdb"
    initialize_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        _seed_environmental_run(connection, "protected-success", NOW - timedelta(days=1), "success")
        _seed_environmental_run(connection, "blocked-expired", NOW - timedelta(days=100), "failed")
        connection.execute(
            """
            create table retention_blocker (
                run_id varchar primary key,
                foreign key (run_id) references pipeline_runs(run_id)
            )
            """
        )
        connection.execute("insert into retention_blocker values ('blocked-expired')")
        connection.execute("checkpoint")

    original_database_bytes = database_path.read_bytes()

    completed_stages = 0
    run_retention_stage = database_module._run_retention_stage

    def record_completed_stage(*args: object, **kwargs: object) -> int:
        nonlocal completed_stages
        result = run_retention_stage(*args, **kwargs)
        completed_stages += 1
        return result

    monkeypatch.setattr(
        database_module,
        "_run_retention_stage",
        record_completed_stage,
    )

    with pytest.raises(duckdb.ConstraintException):
        apply_environmental_retention(database_path, as_of=NOW)

    assert completed_stages == 3
    assert database_path.read_bytes() == original_database_bytes
    with duckdb.connect(str(database_path), read_only=True) as connection:
        for table_name in NORMALIZED_TABLES:
            assert "blocked-expired" in _run_ids(connection, table_name)
        assert connection.execute(
            "select count(*) from forecast_snapshots where run_id = 'blocked-expired'"
        ).fetchone() == (1,)
        assert connection.execute(
            "select count(*) from pipeline_runs where run_id = 'blocked-expired'"
        ).fetchone() == (1,)
    assert list(tmp_path.glob(".rollback.duckdb.retention-*.duckdb")) == []


def test_original_is_replaced_only_after_complete_working_copy_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "replacement.duckdb"
    initialize_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        _seed_environmental_run(connection, "recent-success", NOW - timedelta(days=1), "success")
        _seed_environmental_run(connection, "expired", NOW - timedelta(days=100), "failed")

    validation_completed = False
    validate_working_copy = database_module._validate_retained_working_copy
    replace_database = database_module._replace_retained_database

    def validate_then_record(*args: object, **kwargs: object) -> None:
        nonlocal validation_completed
        validate_working_copy(*args, **kwargs)
        validation_completed = True

    def inspect_then_replace(working_path: Path, original_path: Path) -> None:
        assert validation_completed is True
        assert working_path.parent == original_path.parent
        with duckdb.connect(str(original_path), read_only=True) as original:
            assert original.execute(
                "select count(*) from pipeline_runs where run_id = 'expired'"
            ).fetchone() == (1,)
        with duckdb.connect(str(working_path), read_only=True) as retained:
            assert retained.execute(
                "select count(*) from pipeline_runs where run_id = 'expired'"
            ).fetchone() == (0,)
        replace_database(working_path, original_path)

    monkeypatch.setattr(
        database_module,
        "_validate_retained_working_copy",
        validate_then_record,
    )
    monkeypatch.setattr(
        database_module,
        "_replace_retained_database",
        inspect_then_replace,
    )

    apply_environmental_retention(database_path, as_of=NOW)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        assert connection.execute(
            "select count(*) from pipeline_runs where run_id = 'expired'"
        ).fetchone() == (0,)


def test_validation_failure_discards_working_copy_and_preserves_original(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "validation-failure.duckdb"
    initialize_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        _seed_environmental_run(connection, "recent-success", NOW - timedelta(days=1), "success")
        _seed_environmental_run(connection, "expired", NOW - timedelta(days=100), "failed")

    def reject_working_copy(
        original_path: Path,
        working_path: Path,
        *_: object,
    ) -> None:
        with duckdb.connect(str(original_path), read_only=True) as original:
            assert original.execute(
                "select count(*) from pipeline_runs where run_id = 'expired'"
            ).fetchone() == (1,)
        with duckdb.connect(str(working_path), read_only=True) as retained:
            assert retained.execute(
                "select count(*) from pipeline_runs where run_id = 'expired'"
            ).fetchone() == (0,)
        raise ValueError("controlled retained database validation failure")

    monkeypatch.setattr(
        database_module,
        "_validate_retained_working_copy",
        reject_working_copy,
    )
    monkeypatch.setattr(
        database_module,
        "_replace_retained_database",
        lambda *_: pytest.fail("replacement must not run after validation failure"),
    )

    with pytest.raises(ValueError, match="controlled retained database validation failure"):
        apply_environmental_retention(database_path, as_of=NOW)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        assert connection.execute(
            "select count(*) from pipeline_runs where run_id = 'expired'"
        ).fetchone() == (1,)
        assert _run_ids(connection, "forecast_hourly") == {
            "recent-success",
            "expired",
        }
    assert list(tmp_path.glob(".validation-failure.duckdb.retention-*.duckdb")) == []
