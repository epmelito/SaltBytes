from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from saltbytes.database import initialize_database
from saltbytes.report import render_report


def _config(database_path: Path) -> dict[str, object]:
    return {
        "display_timezone": "America/New_York",
        "storage": {"database_path": str(database_path)},
        "locations": [
            {
                "id": "jennettes_pier",
                "name": "Jennette's Pier",
                "fishing_context": "pier",
            },
            {
                "id": "fort_fisher",
                "name": "Fort Fisher",
                "fishing_context": "surf",
            },
        ],
    }


def _insert_run_data(database_path: Path) -> None:
    with duckdb.connect(str(database_path)) as connection:
        connection.executemany(
            """
            insert into pipeline_runs values (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "old-run",
                    datetime(2026, 7, 30, 9, tzinfo=timezone.utc),
                    datetime(2026, 7, 30, 9, 5, tzinfo=timezone.utc),
                    "success",
                    1,
                    None,
                ),
                (
                    "latest-run",
                    datetime(2026, 7, 30, 12, 30, tzinfo=timezone.utc),
                    datetime(2026, 7, 30, 12, 35, tzinfo=timezone.utc),
                    "failed",
                    1,
                    "wave fetch failed",
                ),
            ],
        )
        connection.executemany(
            """
            insert into forecast_snapshots (
                snapshot_id, run_id, location_id, captured_at, raw_file_path
            ) values (?, ?, ?, ?, ?)
            """,
            [
                (
                    "old-weather",
                    "old-run",
                    "jennettes_pier",
                    datetime(2026, 7, 30, 9, tzinfo=timezone.utc),
                    "raw/2026/07/30/old-run/"
                    "jennettes_pier_old-weather.json",
                ),
                (
                    "latest-weather",
                    "latest-run",
                    "jennettes_pier",
                    datetime(2026, 7, 30, 12, 30, tzinfo=timezone.utc),
                    "raw/2026/07/30/123000Z_latest-run/"
                    "jennettes_pier_latest-weather.json",
                ),
            ],
        )
        connection.executemany(
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
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "old-weather",
                    "jennettes_pier",
                    datetime(2026, 7, 30, 10, tzinfo=timezone.utc),
                    1.0,
                    90.0,
                    2.0,
                    10.0,
                    0.0,
                ),
                (
                    "latest-weather",
                    "jennettes_pier",
                    datetime(2026, 7, 30, 13, tzinfo=timezone.utc),
                    4.5,
                    135.0,
                    6.0,
                    20.0,
                    1.5,
                ),
                (
                    "latest-weather",
                    "jennettes_pier",
                    datetime(2026, 7, 30, 14, tzinfo=timezone.utc),
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ],
        )
        connection.executemany(
            """
            insert into source_results values (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "latest-run",
                    "jennettes_pier",
                    "weather",
                    "success",
                    None,
                    datetime(2026, 7, 30, 12, 30, tzinfo=timezone.utc),
                ),
                (
                    "latest-run",
                    "jennettes_pier",
                    "wave",
                    "fetch_failed",
                    "provider unavailable",
                    datetime(2026, 7, 30, 12, 30, tzinfo=timezone.utc),
                ),
                (
                    "latest-run",
                    "jennettes_pier",
                    "sst",
                    "validation_failed",
                    "returned coordinate",
                    datetime(2026, 7, 30, 12, 30, tzinfo=timezone.utc),
                ),
                (
                    "latest-run",
                    "jennettes_pier",
                    "tide",
                    "success",
                    None,
                    datetime(2026, 7, 30, 12, 30, tzinfo=timezone.utc),
                ),
            ],
        )


def test_render_report_uses_latest_attempted_run_and_preserves_failures(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    _insert_run_data(database_path)

    report = render_report(_config(database_path), hours=1)

    assert "Run: latest-run" in report
    assert "Status: failed" in report
    assert "Forecast window: 2026-07-30 09:00 EDT through 2026-07-30 09:00 EDT" in report
    assert "weather: success" in report
    assert "wave: fetch_failed (provider unavailable)" in report
    assert "sst: validation_failed (returned coordinate)" in report
    assert "2026-07-30 09:00 EDT | 4.5 | 135 | 6.0 | 20 | 1.5 | - | - | - | - | -" in report
    assert "Wind km/h | Dir deg | Gust km/h" in report
    assert "Wind m/s" not in report
    assert "old-run" not in report


def test_render_report_supports_run_and_location_filters(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    _insert_run_data(database_path)

    report = render_report(
        _config(database_path),
        run_id="old-run",
        hours=2,
        location_id="jennettes_pier",
    )

    assert "Run: old-run" in report
    assert "Jennette's Pier (pier)" in report
    assert "Fort Fisher" not in report
    assert "2026-07-30 06:00 EDT | 1.0 | 90 | 2.0 | 10 | 0.0" in report


def test_render_report_rejects_unknown_selection(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with pytest.raises(ValueError, match="unknown location"):
        render_report(_config(database_path), location_id="unknown")

    with pytest.raises(ValueError, match="hours must be greater than zero"):
        render_report(_config(database_path), hours=0)

    with pytest.raises(ValueError, match="no pipeline run found"):
        render_report(_config(database_path), run_id="missing")
