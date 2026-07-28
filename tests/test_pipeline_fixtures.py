import json
from pathlib import Path
from typing import Any

import duckdb
import pytest

from forecast_ops.pipeline import run_pipeline

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_run_pipeline_with_fixed_forecast_fixtures(
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
        fixture_path = FIXTURE_DIR / f"{location['id']}_forecast.json"

        return json.loads(
            fixture_path.read_text(encoding="utf-8")
        )

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
        runs = connection.execute(
            """
            select
                environment,
                status,
                rows_loaded
            from pipeline_runs
            """
        ).fetchall()

        snapshots = connection.execute(
            """
            select
                location_id,
                raw_file_path
            from forecast_snapshots
            order by location_id
            """
        ).fetchall()

        hourly_rows = connection.execute(
            """
            select
                location_id,
                count(*)
            from forecast_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()

        quality_results = connection.execute(
            """
            select
                status,
                count(*)
            from quality_results
            group by status
            """
        ).fetchall()

    assert runs == [("test", "success", 4)]

    assert [snapshot[0] for snapshot in snapshots] == [
        "ocracoke",
        "prague",
    ]

    assert all(
        Path(snapshot[1]).exists()
        for snapshot in snapshots
    )

    assert hourly_rows == [
        ("ocracoke", 2),
        ("prague", 2),
    ]

    assert quality_results == [
        ("pass", 10),
    ]