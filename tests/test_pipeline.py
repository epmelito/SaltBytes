from pathlib import Path
from typing import Any

import duckdb
import pytest

from forecast_ops.pipeline import run_pipeline


def test_run_pipeline_loads_all_locations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
        "environment": "test",
        "locations": [
            {
                "id": "prague",
                "latitude": 50.0755,
                "longitude": 14.4378,
            },
            {
                "id": "ocracoke",
                "latitude": 35.1262,
                "longitude": -75.9196,
            },
        ],
        "api": {
            "base_url": "https://example.test/forecast",
            "forecast_days": 2,
            "hourly_fields": [
                "temperature_2m",
                "precipitation_probability",
                "wind_speed_10m",
            ],
        },
        "storage": {
            "raw_data_path": str(tmp_path / "raw"),
            "database_path": str(tmp_path / "forecast_ops.duckdb"),
        },
    }

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "timezone": "UTC",
            "hourly": {
                "time": [
                    "2026-07-28T12:00",
                    "2026-07-28T13:00",
                ],
                "temperature_2m": [18.2, 19.1],
                "precipitation_probability": [10, 20],
                "wind_speed_10m": [8.4, 9.1],
            },
        }

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )

    result = run_pipeline(config)

    assert result["status"] == "success"
    assert result["snapshots_written"] == 2
    assert result["rows_loaded"] == 4

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select
                environment,
                status,
                rows_loaded,
                error_message
            from pipeline_runs
            where run_id = ?
            """,
            [result["run_id"]],
        ).fetchone()

        snapshot_count = connection.execute(
            """
            select count(*)
            from forecast_snapshots
            where run_id = ?
            """,
            [result["run_id"]],
        ).fetchone()

        hourly_count = connection.execute(
            """
            select count(*)
            from forecast_hourly
            """
        ).fetchone()

        quality_count = connection.execute(
            """
            select count(*)
            from quality_results
            where run_id = ?
            """,
            [result["run_id"]],
        ).fetchone()

    assert run == ("test", "success", 4, None)
    assert snapshot_count == (2,)
    assert hourly_count == (4,)
    assert quality_count == (10,)


def test_run_pipeline_records_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
        "environment": "test",
        "locations": [
            {
                "id": "prague",
                "latitude": 50.0755,
                "longitude": 14.4378,
            }
        ],
        "api": {
            "base_url": "https://example.test/forecast",
            "forecast_days": 2,
            "hourly_fields": ["temperature_2m"],
        },
        "storage": {
            "raw_data_path": str(tmp_path / "raw"),
            "database_path": str(tmp_path / "forecast_ops.duckdb"),
        },
    }

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        raise RuntimeError("forecast api unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )

    with pytest.raises(
        RuntimeError,
        match="forecast api unavailable",
    ):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select
                status,
                rows_loaded,
                error_message
            from pipeline_runs
            """
        ).fetchone()

    assert run == (
        "failed",
        0,
        "forecast api unavailable",
    )


def test_run_pipeline_fails_when_quality_checks_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
        "environment": "test",
        "locations": [
            {
                "id": "prague",
                "latitude": 50.0755,
                "longitude": 14.4378,
            }
        ],
        "api": {
            "base_url": "https://example.test/forecast",
            "forecast_days": 2,
            "hourly_fields": [
                "temperature_2m",
                "precipitation_probability",
                "wind_speed_10m",
            ],
        },
        "storage": {
            "raw_data_path": str(tmp_path / "raw"),
            "database_path": str(tmp_path / "forecast_ops.duckdb"),
        },
    }

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "timezone": "UTC",
            "hourly": {
                "time": [
                    "2026-07-28T12:00",
                    "2026-07-28T13:00",
                ],
                "temperature_2m": [18.2],
                "precipitation_probability": [10, 20],
                "wind_speed_10m": [8.4, 9.1],
            },
        }

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )

    with pytest.raises(
        ValueError,
        match="forecast quality checks failed for prague",
    ):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select
                status,
                rows_loaded,
                error_message
            from pipeline_runs
            """
        ).fetchone()

        failed_quality_count = connection.execute(
            """
            select count(*)
            from quality_results
            where status = 'fail'
            """
        ).fetchone()

        snapshot_count = connection.execute(
            """
            select count(*)
            from forecast_snapshots
            """
        ).fetchone()

    assert run is not None
    assert run[0] == "failed"
    assert run[1] == 0
    assert "temperature_2m_count_matches_time" in run[2]
    assert failed_quality_count == (1,)
    assert snapshot_count == (0,)