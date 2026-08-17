import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import duckdb
import pytest

from saltbytes.dashboard import DashboardSchemaError, export_dashboard_data
from saltbytes.database import initialize_database

_LOCATION = {
    "id": "jennettes_pier",
    "name": "Jennette's Pier",
    "fishing_context": "pier",
}
_EXPECTED_FILES = {
    "conditions.json",
    "forecast-history.json",
    "locations.json",
    "manifest.json",
    "observation-health.json",
    "pipeline-runs.json",
    "provenance.json",
    "source-health.json",
}


def _config(database_path: Path) -> dict[str, Any]:
    return {
        "display_timezone": "America/New_York",
        "storage": {"database_path": str(database_path)},
        "locations": [_LOCATION],
    }


def _read_json(output_path: Path, filename: str) -> Any:
    return json.loads((output_path / filename).read_text(encoding="utf-8"))


def _seed_dashboard_database(database_path: Path) -> None:
    initialize_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs values
                ('run-old', timestamptz '2026-07-29 00:00:00+00',
                    timestamptz '2026-07-29 00:05:00+00', 'success', 4, null),
                ('run-success', timestamptz '2026-07-29 06:00:00+00',
                    timestamptz '2026-07-29 06:05:00+00', 'success', 4, null),
                ('run-failed', timestamptz '2026-07-29 12:00:00+00',
                    timestamptz '2026-07-29 12:02:00+00', 'failed', 1,
                    'weather unavailable');

            insert into run_locations
            select
                run_id,
                'jennettes_pier',
                'pier',
                90.0,
                100.0,
                'reviewed_map',
                'project review',
                date '2026-07-01',
                'Approximate seaward reference'
            from pipeline_runs;

            insert into run_location_solar_context
            select
                run_id,
                'jennettes_pier',
                35.91,
                -75.60,
                'America/New_York',
                'solar-v1',
                'astral',
                '3.2.1'
            from pipeline_runs;

            insert into forecast_snapshots values
                ('old-weather', 'run-old', 'jennettes_pier',
                    timestamptz '2026-07-29 00:01:00+00',
                    'C:/private/raw/old-weather.json', 'ncep_nbm_conus',
                    35.91, -75.60, 35.90, -75.59),
                ('old-wave', 'run-old', 'jennettes_pier',
                    timestamptz '2026-07-29 00:01:00+00',
                    'C:/private/raw/old-wave.json', 'meteofrance_wave',
                    35.91, -75.60, 35.90, -75.59),
                ('old-sst', 'run-old', 'jennettes_pier',
                    timestamptz '2026-07-29 00:01:00+00',
                    'C:/private/raw/old-sst.json', 'meteofrance_currents',
                    35.91, -75.60, 35.90, -75.59),
                ('old-tide', 'run-old', 'jennettes_pier',
                    timestamptz '2026-07-29 00:01:00+00',
                    'C:/private/raw/old-tide.json', null,
                    null, null, null, null),
                ('current-weather', 'run-success', 'jennettes_pier',
                    timestamptz '2026-07-29 06:01:00+00',
                    'C:/private/raw/current-weather.json', 'ncep_nbm_conus',
                    35.91, -75.60, 35.90, -75.59),
                ('current-wave', 'run-success', 'jennettes_pier',
                    timestamptz '2026-07-29 06:01:00+00',
                    'C:/private/raw/current-wave.json', 'meteofrance_wave',
                    35.91, -75.60, 35.90, -75.59),
                ('current-sst', 'run-success', 'jennettes_pier',
                    timestamptz '2026-07-29 06:01:00+00',
                    'C:/private/raw/current-sst.json', 'meteofrance_currents',
                    35.91, -75.60, 35.90, -75.59),
                ('current-tide', 'run-success', 'jennettes_pier',
                    timestamptz '2026-07-29 06:01:00+00',
                    'C:/private/raw/current-tide.json', null,
                    null, null, null, null),
                ('failed-wave', 'run-failed', 'jennettes_pier',
                    timestamptz '2026-07-29 12:01:00+00',
                    'C:/private/raw/failed-wave.json', 'meteofrance_wave',
                    35.91, -75.60, 35.90, -75.59);

            insert into tide_snapshots values
                ('old-tide', '8652226', 'Jennettes Pier', 'direct', '8651370',
                    'predictions', 'hilo', 'MLLW', 'gmt', 'metric', 'json',
                    date '2026-07-29', date '2026-07-31', null, -5, 1, 1.04, 1.43,
                    null, null, null,
                    0.448, 'Atlantic facing pier', 'Forecast, not observation'),
                ('current-tide', '8652226', 'Jennettes Pier', 'direct', '8651370',
                    'predictions', 'hilo', 'MLLW', 'gmt', 'metric', 'json',
                    date '2026-07-29', date '2026-07-31', null, -5, 1, 1.04, 1.43,
                    null, null, null,
                    0.448, 'Atlantic facing pier', 'Forecast, not observation');

            insert into forecast_hourly values
                ('old-weather', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', 20.0,
                    10.0, 120.0, 15.0, 0.0),
                ('current-weather', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', null,
                    12.0, 120.0, 17.0, 0.0);

            insert into wave_hourly values
                ('old-wave', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', 1.1, 135.0, 8.0),
                ('current-wave', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', 1.2, 135.0, 8.0);

            insert into sst_hourly values
                ('old-sst', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', 25.0),
                ('current-sst', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', 25.1);

            insert into tide_events values
                ('old-tide', 'jennettes_pier',
                    timestamptz '2026-07-29 22:00:00+00', 'low', 0.2),
                ('old-tide', 'jennettes_pier',
                    timestamptz '2026-07-30 04:00:00+00', 'high', 1.4),
                ('current-tide', 'jennettes_pier',
                    timestamptz '2026-07-29 22:00:00+00', 'low', 0.2),
                ('current-tide', 'jennettes_pier',
                    timestamptz '2026-07-30 04:00:00+00', 'high', 1.4);

            insert into tide_phase_hourly values
                ('old-tide', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', 'rising'),
                ('current-tide', 'jennettes_pier',
                    timestamptz '2026-07-30 00:00:00+00', 'rising');

            insert into source_results values
                ('run-old', 'jennettes_pier', 'weather', 'success', null,
                    timestamptz '2026-07-29 00:05:00+00'),
                ('run-old', 'jennettes_pier', 'wave', 'success', null,
                    timestamptz '2026-07-29 00:05:00+00'),
                ('run-old', 'jennettes_pier', 'sst', 'success', null,
                    timestamptz '2026-07-29 00:05:00+00'),
                ('run-old', 'jennettes_pier', 'tide', 'success', null,
                    timestamptz '2026-07-29 00:05:00+00'),
                ('run-success', 'jennettes_pier', 'weather', 'success', null,
                    timestamptz '2026-07-29 06:05:00+00'),
                ('run-success', 'jennettes_pier', 'wave', 'success', null,
                    timestamptz '2026-07-29 06:05:00+00'),
                ('run-success', 'jennettes_pier', 'sst', 'success', null,
                    timestamptz '2026-07-29 06:05:00+00'),
                ('run-success', 'jennettes_pier', 'tide', 'success', null,
                    timestamptz '2026-07-29 06:05:00+00'),
                ('run-failed', 'jennettes_pier', 'weather', 'fetch_failed',
                    'private connection detail: token=secret',
                    timestamptz '2026-07-29 12:02:00+00'),
                ('run-failed', 'jennettes_pier', 'wave', 'success', null,
                    timestamptz '2026-07-29 12:02:00+00');
            """
        )


def test_export_dashboard_data_writes_curated_public_json(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    _seed_dashboard_database(database_path)

    export_dashboard_data(
        _config(database_path),
        output_path,
        generated_at=datetime(2026, 7, 29, 12, 10, tzinfo=timezone.utc),
    )

    assert {path.name for path in output_path.iterdir()} == _EXPECTED_FILES
    manifest = _read_json(output_path, "manifest.json")
    assert manifest["latest_attempt"]["run_id"] == "run-failed"
    assert manifest["latest_success"]["run_id"] == "run-success"
    assert manifest["latest_success_freshness_minutes"] == 365
    assert manifest["schema_version"] == 4
    assert manifest["forecast_window"] == {
        "start": "2026-07-30T00:00:00Z",
        "end": "2026-07-30T00:00:00Z",
    }

    conditions = _read_json(output_path, "conditions.json")
    assert len(conditions) == 1
    assert conditions[0]["run_id"] == "run-success"
    assert conditions[0]["precipitation_probability"] is None
    assert conditions[0]["wind_speed_10m"] == 12.0
    assert conditions[0]["wind_to_shore_angle_degrees"] == 30.0
    assert conditions[0]["tide_minutes_until_next_extremum"] == 240
    score = conditions[0]["spanish_mackerel_conditions"]
    assert score == {
        "state": "available",
        "methodology_version": "spanish-mackerel-v1.1.0",
        "score": 76,
        "score_band": "favorable_alignment",
        "confidence": [
            {"identifier": "species_identity_confidence", "state": "high"},
            {"identifier": "location_applicability_confidence", "state": "high"},
            {"identifier": "environmental_source_confidence", "state": "moderate"},
            {"identifier": "seasonal_evidence_confidence", "state": "high"},
            {"identifier": "habitat_data_confidence", "state": "moderate"},
            {"identifier": "biological_observation_confidence", "state": "low"},
            {"identifier": "fishability_data_confidence", "state": "moderate"},
            {"identifier": "overall_interpretation_confidence", "state": "moderate"},
        ],
        "positive_factors": [
            "seasonal_alignment",
            "thermal_context",
            "wind_fishability",
        ],
        "limiting_factors": ["wave_fishability"],
        "unknown_factors": [
            "local_baitfish_presence",
            "current_spanish_mackerel_presence",
            "schools_within_casting_range",
            "nearshore_sst_accuracy_and_site_representativeness",
        ],
    }

    history = _read_json(output_path, "forecast-history.json")
    assert [row["run_id"] for row in history] == ["run-old", "run-success"]
    assert all(row["forecast_time"] == "2026-07-30T00:00:00Z" for row in history)

    pipeline_runs = _read_json(output_path, "pipeline-runs.json")
    assert [run["run_id"] for run in pipeline_runs] == [
        "run-failed",
        "run-success",
        "run-old",
    ]
    assert pipeline_runs[0]["partial_data"] is True
    assert pipeline_runs[0]["snapshot_count"] == 1

    source_health = _read_json(output_path, "source-health.json")
    summaries = {row["source"]: row for row in source_health["summary"]}
    assert summaries["weather"]["success_rate_percent"] == 66.7
    assert summaries["weather"]["failure_count"] == 1
    assert summaries["sst"]["missing_count"] == 1
    assert source_health["failures"][0]["status"] == "fetch_failed"
    assert "detail" not in source_health["failures"][0]

    observation_health = _read_json(output_path, "observation-health.json")
    assert observation_health == {
        "latest_attempt": None,
        "latest_attempts": [],
        "outstanding_patterns": [],
    }

    provenance = _read_json(output_path, "provenance.json")
    assert {row["source"] for row in provenance} == {
        "weather",
        "wave",
        "sst",
        "tide",
    }
    tide = next(row for row in provenance if row["source"] == "tide")
    assert tide["station_id"] == "8652226"
    assert tide["shore_normal_azimuth_degrees"] == 90.0

    serialized_export = "\n".join(
        path.read_text(encoding="utf-8") for path in output_path.iterdir()
    )
    assert "raw_file_path" not in serialized_export
    assert "C:/private" not in serialized_export
    assert "private connection detail" not in serialized_export
    assert "token=secret" not in serialized_export
    assert ".duckdb" not in serialized_export
    assert "biological_alignment" not in serialized_export
    assert "effective_wind_kmh" not in serialized_export


def test_export_dashboard_data_preserves_expected_source_without_snapshot_reference(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    _seed_dashboard_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            "delete from wave_hourly where snapshot_id = 'current-wave'"
        )

    export_dashboard_data(_config(database_path), output_path)

    provenance = _read_json(output_path, "provenance.json")
    assert len(provenance) == 4
    wave = next(row for row in provenance if row["source"] == "wave")
    assert wave["location_id"] == "jennettes_pier"
    assert wave["snapshot_id"] is None
    assert wave["captured_at"] is None
    assert wave["model_selector"] is None


def test_export_dashboard_data_includes_tide_relationship_metadata(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    _seed_dashboard_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """insert into run_locations values (
                'run-success', 'little_bridge_sound_access', 'sound-side',
                60.0, null, 'reviewed_map', 'project review', date '2026-08-13',
                'Analytical directional context for the Roanoke Sound access'
            )"""
        )
        connection.execute(
            """insert into forecast_snapshots values (
                'little-bridge-tide', 'run-success', 'little_bridge_sound_access',
                timestamptz '2026-07-29 06:01:00+00',
                'C:/private/raw/little-bridge-tide.json', null,
                null, null, null, null
            )"""
        )
        connection.execute(
            """insert into tide_snapshots (
                snapshot_id, station_id, prediction_location, relationship_type,
                reference_station, product, interval, datum, time_zone, units,
                response_format, request_begin_date, request_end_date,
                subordinate_station_type, high_time_offset_minutes,
                low_time_offset_minutes, high_multiplier, low_multiplier,
                height_offset_high_tide, height_offset_low_tide,
                height_adjusted_type, distance_km, coastal_relationship,
                known_limitation
            ) values (
                'little-bridge-tide', '8652591', 'Roanoke Sound Channel',
                'transfer', '8652587', 'predictions', 'hilo', 'MLLW', 'gmt',
                'metric', 'json', date '2026-07-29', date '2026-07-31', 'S',
                97, 77, null, null, 0.47, 0.14, 'R', 11.487,
                'Approved transferred tide relationship',
                'Prediction is not an observed water level'
            )"""
        )
        connection.execute(
            """insert into tide_events values
                ('little-bridge-tide', 'little_bridge_sound_access',
                    timestamptz '2026-07-29 22:00:00+00', 'low', 0.2),
                ('little-bridge-tide', 'little_bridge_sound_access',
                    timestamptz '2026-07-30 04:00:00+00', 'high', 1.4)"""
        )
        connection.execute(
            """insert into tide_phase_hourly values (
                'little-bridge-tide', 'little_bridge_sound_access',
                timestamptz '2026-07-30 00:00:00+00', 'rising'
            )"""
        )

    export_dashboard_data(_config(database_path), output_path)

    provenance = _read_json(output_path, "provenance.json")
    jennettes_tide = next(
        row
        for row in provenance
        if row["location_id"] == "jennettes_pier" and row["source"] == "tide"
    )
    little_bridge_tide = next(
        row
        for row in provenance
        if row["location_id"] == "little_bridge_sound_access"
        and row["source"] == "tide"
    )

    assert jennettes_tide["high_multiplier"] == 1.04
    assert jennettes_tide["low_multiplier"] == 1.43
    assert jennettes_tide["subordinate_station_type"] is None
    assert jennettes_tide["height_offset_high_tide"] is None
    assert jennettes_tide["height_offset_low_tide"] is None
    assert jennettes_tide["height_adjusted_type"] is None
    assert little_bridge_tide["subordinate_station_type"] == "S"
    assert little_bridge_tide["height_offset_high_tide"] == 0.47
    assert little_bridge_tide["height_offset_low_tide"] == 0.14
    assert little_bridge_tide["height_adjusted_type"] == "R"
    assert little_bridge_tide["high_multiplier"] is None
    assert little_bridge_tide["low_multiplier"] is None


def test_export_dashboard_data_groups_outstanding_review_patterns(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    _seed_dashboard_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        for index in range(21):
            pattern_id = f"pattern-{index:02d}"
            connection.execute(
                """insert into fishing_observation_review_patterns
                (pattern_id, source, reason, raw_segment)
                values (?, 'jennettes_pier', 'reason', ?)""",
                [pattern_id, f"Candidate {index}"],
            )
            occurrence_count = 2 if index == 0 else 1
            for occurrence in range(occurrence_count):
                report_id = f"report-{index:02d}-{occurrence}"
                candidate_id = f"candidate-{index:02d}-{occurrence}"
                connection.execute(
                """insert into fishing_observation_reports values
                    (?, 'jennettes_pier', 'url', ?, 'DATE', 'TITLE',
                    'jennettes_pier', 'exact_site',
                    timestamptz '2026-08-13 12:00:00+00')""",
                    [report_id, report_id],
                )
                connection.execute(
                    """insert into fishing_observation_review_candidates values
                    (?, ?, 'wording', 'reason')""",
                    [candidate_id, report_id],
                )
                connection.execute(
                    "insert into fishing_observation_review_candidate_patterns values (?, ?)",
                    [candidate_id, pattern_id],
                )

    export_dashboard_data(_config(database_path), output_path)

    patterns = _read_json(output_path, "observation-health.json")["outstanding_patterns"]
    first = next(pattern for pattern in patterns if pattern["pattern_id"] == "pattern-00")
    assert len(patterns) == 20
    assert first["occurrence_count"] == 2
    assert first["report_id"]
    assert first["report_time_text"] == "DATE"
    assert "pattern-20" not in {pattern["pattern_id"] for pattern in patterns}


@pytest.mark.parametrize(
    ("attempts", "expected_statuses"),
    [
        (
            [("jennettes_pier", "success"), ("sunset_beach_pier", "success")],
            {"jennettes_pier": "success", "sunset_beach_pier": "success"},
        ),
        (
            [("jennettes_pier", "failed"), ("sunset_beach_pier", "success")],
            {"jennettes_pier": "failed", "sunset_beach_pier": "success"},
        ),
        (
            [("jennettes_pier", "success"), ("sunset_beach_pier", "failed")],
            {"jennettes_pier": "success", "sunset_beach_pier": "failed"},
        ),
        ([], {}),
    ],
)
def test_export_dashboard_data_includes_latest_attempt_for_each_observation_source(
    tmp_path: Path,
    attempts: list[tuple[str, str]],
    expected_statuses: dict[str, str],
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    _seed_dashboard_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        for index, (source, status) in enumerate(attempts):
            connection.execute(
                """insert into fishing_observation_ingestion_attempts values
                (?, ?, timestamptz '2026-08-13 12:00:00+00', ?, 0, 0, 0)""",
                [f"attempt-{index}", source, status],
            )

    export_dashboard_data(_config(database_path), output_path)

    observation_health = _read_json(output_path, "observation-health.json")
    latest_attempts = observation_health["latest_attempts"]
    assert {
        attempt["source"]: attempt["status"] for attempt in latest_attempts
    } == expected_statuses
    if not attempts:
        assert observation_health["latest_attempt"] is None


@pytest.mark.parametrize(
    ("statement", "reason"),
    [
        (
            "delete from run_location_solar_context where run_id = 'run-success'",
            "display_timezone_missing",
        ),
        (
            "update run_locations set fishing_context = 'surf' where run_id = 'run-success'",
            "location_not_applicable",
        ),
        (
            "delete from run_locations where run_id = 'run-success'",
            "location_not_applicable",
        ),
    ],
)
def test_export_dashboard_data_preserves_rows_with_unavailable_score_provenance(
    tmp_path: Path,
    statement: str,
    reason: str,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    _seed_dashboard_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(statement)

    export_dashboard_data(_config(database_path), output_path)

    conditions = _read_json(output_path, "conditions.json")
    assert len(conditions) == 1
    score = conditions[0]["spanish_mackerel_conditions"]
    assert score == {
        "state": "unavailable",
        "methodology_version": "spanish-mackerel-v1.1.0",
        "unavailable_reasons": [reason],
    }


def test_export_dashboard_data_rejects_outdated_schema_with_dashboard_wording(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    _seed_dashboard_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("drop table source_results")

    with pytest.raises(
        DashboardSchemaError,
        match="dashboard export requires a current SaltBytes database schema",
    ) as exc_info:
        export_dashboard_data(_config(database_path), output_path)

    assert "HTML reporting requires" not in str(exc_info.value)
    assert not output_path.exists()


def test_export_dashboard_data_limits_forecast_history_to_twenty_runs(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    initialize_database(database_path)
    first_start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    forecast_time = datetime(2026, 7, 3, tzinfo=timezone.utc)

    with duckdb.connect(str(database_path)) as connection:
        for index in range(21):
            run_id = f"run-{index:02d}"
            snapshot_id = f"snapshot-{index:02d}"
            started_at = first_start + timedelta(hours=index)
            completed_at = started_at + timedelta(minutes=5)
            connection.execute(
                "insert into pipeline_runs values (?, ?, ?, 'success', 1, null)",
                [run_id, started_at, completed_at],
            )
            connection.execute(
                """
                insert into run_locations values (
                    ?, 'jennettes_pier', 'pier', 90.0, null,
                    'reviewed_map', 'project review', date '2026-07-01',
                    'Approximate seaward reference'
                )
                """,
                [run_id],
            )
            connection.execute(
                """
                insert into forecast_snapshots values (
                    ?, ?, 'jennettes_pier', ?, 'private.json',
                    'ncep_nbm_conus', 35.91, -75.60, 35.90, -75.59
                )
                """,
                [snapshot_id, run_id, started_at],
            )
            connection.execute(
                """
                insert into forecast_hourly values (
                    ?, 'jennettes_pier', ?, 0.0, ?, 120.0, 15.0, 0.0
                )
                """,
                [snapshot_id, forecast_time, float(index)],
            )

    export_dashboard_data(_config(database_path), output_path)

    history = _read_json(output_path, "forecast-history.json")
    run_ids = {row["run_id"] for row in history}
    assert len(history) == 20
    assert "run-00" not in run_ids
    assert {"run-01", "run-20"} <= run_ids


def test_export_dashboard_data_rejects_outdated_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            "create table pipeline_runs (run_id varchar, started_at timestamptz)"
        )

    with pytest.raises(DashboardSchemaError, match="current SaltBytes database schema"):
        export_dashboard_data(_config(database_path), output_path)

    assert not output_path.exists()


def test_export_dashboard_data_requires_completed_successful_run(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    output_path = tmp_path / "dashboard-data"
    initialize_database(database_path)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs values (
                'run-failed',
                timestamptz '2026-07-29 12:00:00+00',
                timestamptz '2026-07-29 12:02:00+00',
                'failed', 0, 'failed'
            )
            """
        )

    with pytest.raises(ValueError, match="no completed successful pipeline run"):
        export_dashboard_data(_config(database_path), output_path)

    assert not output_path.exists()
