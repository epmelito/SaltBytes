import json
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pytest

from forecast_ops.config import load_config
from forecast_ops.pipeline import run_pipeline


def atmospheric_payload(
    location: dict[str, Any],
    value_offset: float,
) -> dict[str, Any]:
    start = datetime(2026, 7, 28)
    times = [
        (start + timedelta(hours=index)).isoformat(timespec="minutes")
        for index in range(168)
    ]
    returned_coordinate = location["weather"][
        "expected_returned_coordinate"
    ]

    return {
        "latitude": returned_coordinate["latitude"],
        "longitude": returned_coordinate["longitude"],
        "timezone": "America/New_York",
        "utc_offset_seconds": -14400,
        "hourly": {
            "time": times,
            "wind_speed_10m": [10.0 + value_offset] * 168,
            "wind_direction_10m": [180.0 + value_offset] * 168,
            "wind_gusts_10m": [15.0 + value_offset] * 168,
            "precipitation_probability": [20.0 + value_offset] * 168,
            "precipitation": [value_offset] * 168,
        },
    }


def test_run_pipeline_ingests_all_five_coastal_locations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = deepcopy(load_config("test"))
    config["storage"] = {
        "raw_data_path": str(tmp_path / "raw"),
        "database_path": str(tmp_path / "forecast_ops.duckdb"),
    }
    payloads: dict[str, dict[str, Any]] = {}

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        value_offset = float(
            next(
                index
                for index, configured_location in enumerate(
                    config["locations"]
                )
                if configured_location["id"] == location["id"]
            )
        )
        payload = atmospheric_payload(location, value_offset)
        payloads[location["id"]] = payload
        return payload

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )

    result = run_pipeline(config)

    assert result["status"] == "success"
    assert result["snapshots_written"] == 5
    assert result["rows_loaded"] == 840

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select status, rows_loaded, error_message
            from pipeline_runs
            where run_id = ?
            """,
            [result["run_id"]],
        ).fetchone()
        snapshots = connection.execute(
            """
            select
                location_id,
                raw_file_path,
                model_selector,
                request_latitude,
                request_longitude,
                returned_latitude,
                returned_longitude,
                response_timezone,
                response_utc_offset_seconds
            from forecast_snapshots
            order by location_id
            """
        ).fetchall()
        hourly_counts = connection.execute(
            """
            select location_id, count(*)
            from forecast_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()
        first_rows = connection.execute(
            """
            select
                location_id,
                temperature_2m,
                wind_speed_10m,
                wind_direction_10m,
                wind_gusts_10m,
                precipitation_probability,
                precipitation
            from forecast_hourly
            qualify row_number() over (
                partition by location_id
                order by forecast_time
            ) = 1
            order by location_id
            """
        ).fetchall()
        quality_results = connection.execute(
            """
            select check_name, status
            from quality_results
            """
        ).fetchall()

    locations_by_id = {
        location["id"]: location
        for location in config["locations"]
    }

    assert run == ("success", 840, None)
    assert hourly_counts == [
        ("bogue_inlet_pier", 168),
        ("fort_fisher", 168),
        ("fort_macon_ocean", 168),
        ("jennettes_pier", 168),
        ("ocracoke_ramp_72", 168),
    ]
    assert len(first_rows) == 5
    assert all(row[1] is None for row in first_rows)
    assert all(all(value is not None for value in row[2:]) for row in first_rows)
    assert len(quality_results) == 155
    assert all(status == "pass" for _, status in quality_results)

    for snapshot in snapshots:
        location_id = snapshot[0]
        raw_file_path = Path(snapshot[1])
        location = locations_by_id[location_id]
        request_coordinate = location["weather"]["request_coordinate"]
        returned_coordinate = location["weather"][
            "expected_returned_coordinate"
        ]

        assert snapshot[2:] == (
            "ncep_nbm_conus",
            request_coordinate["latitude"],
            request_coordinate["longitude"],
            returned_coordinate["latitude"],
            returned_coordinate["longitude"],
            "America/New_York",
            -14400,
        )
        assert raw_file_path.exists()
        assert json.loads(raw_file_path.read_text(encoding="utf-8")) == (
            payloads[location_id]
        )

    assert len(snapshots) == 5
    assert len({snapshot[1] for snapshot in snapshots}) == 5
