from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pytest

from forecast_ops.pipeline import run_pipeline

HOURLY_FIELDS = [
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation_probability",
    "precipitation",
]
WAVE_FIELDS = [
    "wave_height",
    "wave_direction",
    "wave_period",
]


def pipeline_config(tmp_path: Path) -> dict[str, Any]:
    return {
        "environment": "test",
        "locations": [
            {
                "id": "jennettes_pier",
                "name": "Jennette's Pier",
                "fishing_context": "pier",
                "display_coordinate": {
                    "latitude": 35.9096355,
                    "longitude": -75.5966537,
                },
                "weather": {
                    "request_coordinate": {
                        "latitude": 35.9096355,
                        "longitude": -75.5966537,
                    },
                    "expected_returned_coordinate": {
                        "latitude": 35.89557,
                        "longitude": -75.5936,
                    },
                    "coastal_regime": "Atlantic coastal grid",
                },
                "wave": {
                    "request_coordinate": {
                        "latitude": 35.91,
                        "longitude": -75.54,
                    },
                    "expected_returned_coordinate": {
                        "latitude": 35.875,
                        "longitude": -75.54166,
                    },
                },
            },
            {
                "id": "fort_fisher",
                "name": "Fort Fisher State Recreation Area",
                "fishing_context": "surf",
                "display_coordinate": {
                    "latitude": 33.9534,
                    "longitude": -77.929,
                },
                "weather": {
                    "request_coordinate": {
                        "latitude": 33.9534,
                        "longitude": -77.929,
                    },
                    "expected_returned_coordinate": {
                        "latitude": 33.954144,
                        "longitude": -77.93454,
                    },
                    "coastal_regime": "Atlantic coastal grid",
                },
                "wave": {
                    "request_coordinate": {
                        "latitude": 33.93,
                        "longitude": -77.9,
                    },
                    "expected_returned_coordinate": {
                        "latitude": 33.875,
                        "longitude": -77.87499,
                    },
                },
            },
        ],
        "api": {
            "base_url": "https://example.test/forecast",
            "model": "ncep_nbm_conus",
            "forecast_days": 7,
            "hourly_fields": HOURLY_FIELDS,
        },
        "wave_api": {
            "base_url": "https://example.test/marine",
            "model": "meteofrance_wave",
            "forecast_days": 7,
            "hourly_fields": WAVE_FIELDS,
        },
        "storage": {
            "raw_data_path": str(tmp_path / "raw"),
            "database_path": str(tmp_path / "forecast_ops.duckdb"),
        },
    }


def atmospheric_payload(
    location: dict[str, Any],
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
            "wind_speed_10m": [10.0] * 168,
            "wind_direction_10m": [180.0] * 168,
            "wind_gusts_10m": [15.0] * 168,
            "precipitation_probability": [20.0] * 168,
            "precipitation": [0.0] * 168,
        },
    }


def wave_payload(location: dict[str, Any]) -> dict[str, Any]:
    start = datetime(2026, 7, 28)
    times = [
        (start + timedelta(hours=index)).isoformat(timespec="minutes")
        for index in range(168)
    ]
    returned_coordinate = location["wave"]["expected_returned_coordinate"]

    return {
        "latitude": returned_coordinate["latitude"],
        "longitude": returned_coordinate["longitude"],
        "timezone": "America/New_York",
        "utc_offset_seconds": -14400,
        "hourly": {
            "time": times,
            "wave_height": [1.2] * 168,
            "wave_direction": [90.0] * 168,
            "wave_period": [8.0] * 168,
        },
    }


def test_source_quality_failures_are_independent_and_collected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_weather_locations: list[str] = []
    fetched_wave_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_weather_locations.append(location["id"])
        payload = atmospheric_payload(location)

        if location["id"] == "fort_fisher":
            payload["latitude"] = 0

        return payload

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        wave_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_wave_locations.append(location["id"])
        payload = wave_payload(location)

        if location["id"] == "jennettes_pier":
            payload["longitude"] = 0

        return payload

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select status, rows_loaded, error_message
            from pipeline_runs
            """
        ).fetchone()
        snapshots = connection.execute(
            """
            select location_id, model_selector
            from forecast_snapshots
            order by location_id, model_selector
            """
        ).fetchall()
        weather_locations = connection.execute(
            """
            select location_id, count(*)
            from forecast_hourly
            group by location_id
            """
        ).fetchall()
        wave_locations = connection.execute(
            """
            select location_id, count(*)
            from wave_hourly
            group by location_id
            """
        ).fetchall()
        quality_results = connection.execute(
            """
            select check_name, status
            from quality_results
            """
        ).fetchall()

    assert fetched_weather_locations == ["jennettes_pier", "fort_fisher"]
    assert fetched_wave_locations == ["jennettes_pier", "fort_fisher"]
    assert run is not None
    assert run[0] == "failed"
    assert run[1] == 336
    assert "wave quality checks failed for jennettes_pier" in run[2]
    assert "wave:returned_longitude_matches_expected" in run[2]
    assert "weather quality checks failed for fort_fisher" in run[2]
    assert "weather:returned_latitude_matches_expected" in run[2]
    assert str(error.value) == run[2]
    assert snapshots == [
        ("fort_fisher", "meteofrance_wave"),
        ("jennettes_pier", "ncep_nbm_conus"),
    ]
    assert weather_locations == [("jennettes_pier", 168)]
    assert wave_locations == [("fort_fisher", 168)]
    assert {
        ":".join(check_name.split(":", maxsplit=2)[:2])
        for check_name, _ in quality_results
    } == {
        "jennettes_pier:weather",
        "jennettes_pier:wave",
        "fort_fisher:weather",
        "fort_fisher:wave",
    }
    assert any(status == "fail" for _, status in quality_results)
    assert any(status == "pass" for _, status in quality_results)
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 2


def test_api_failure_is_recorded_and_aborts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_locations.append(location["id"])
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
            select status, rows_loaded, error_message
            from pipeline_runs
            """
        ).fetchone()

    assert fetched_locations == ["jennettes_pier"]
    assert run == ("failed", 0, "forecast api unavailable")


def test_wave_api_failure_is_recorded_and_aborts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_wave_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fail_fetch_wave_forecast(
        location: dict[str, Any],
        wave_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_wave_locations.append(location["id"])
        raise RuntimeError("wave api unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fail_fetch_wave_forecast,
    )

    with pytest.raises(RuntimeError, match="wave api unavailable"):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()

    assert fetched_wave_locations == ["jennettes_pier"]
    assert run == ("failed", 168, "wave api unavailable")


def test_quality_persistence_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fail_quality_insert(**kwargs: Any) -> None:
        raise RuntimeError("quality database unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.insert_quality_result",
        fail_quality_insert,
    )

    with pytest.raises(RuntimeError, match="quality database unavailable"):
        run_pipeline(config)


def test_raw_storage_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_locations.append(location["id"])
        return atmospheric_payload(location)

    def fail_raw_storage(**kwargs: Any) -> dict[str, Any]:
        raise OSError("raw storage unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.write_raw_snapshot",
        fail_raw_storage,
    )

    with pytest.raises(OSError, match="raw storage unavailable"):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select status, rows_loaded, error_message
            from pipeline_runs
            """
        ).fetchone()

    assert fetched_locations == ["jennettes_pier"]
    assert run == ("failed", 0, "raw storage unavailable")


def test_snapshot_database_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_locations.append(location["id"])
        return atmospheric_payload(location)

    def fail_snapshot_insert(**kwargs: Any) -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.insert_forecast_snapshot",
        fail_snapshot_insert,
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select status, rows_loaded, error_message
            from pipeline_runs
            """
        ).fetchone()

    assert fetched_locations == ["jennettes_pier"]
    assert run == ("failed", 0, "database unavailable")


def test_atmospheric_normalized_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fail_forecast_hourly_insert(**kwargs: Any) -> int:
        raise RuntimeError("atmospheric normalized storage unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.insert_forecast_hourly",
        fail_forecast_hourly_insert,
    )

    with pytest.raises(
        RuntimeError,
        match="atmospheric normalized storage unavailable",
    ):
        run_pipeline(config)


def test_wave_raw_storage_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    raw_write_count = 0

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        wave_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return wave_payload(location)

    from forecast_ops.storage import write_raw_snapshot as real_write

    def fail_second_raw_write(**kwargs: Any) -> dict[str, Any]:
        nonlocal raw_write_count
        raw_write_count += 1
        if raw_write_count == 2:
            raise OSError("wave raw storage unavailable")
        return real_write(**kwargs)

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.write_raw_snapshot",
        fail_second_raw_write,
    )

    with pytest.raises(OSError, match="wave raw storage unavailable"):
        run_pipeline(config)


def test_wave_snapshot_database_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        wave_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return wave_payload(location)

    from forecast_ops.database import (
        insert_forecast_snapshot as real_insert_snapshot,
    )

    def fail_wave_snapshot_insert(
        database_path: Path | str,
        metadata: dict[str, Any],
    ) -> None:
        if metadata["model_selector"] == "meteofrance_wave":
            raise RuntimeError("wave snapshot database unavailable")
        real_insert_snapshot(database_path, metadata)

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.insert_forecast_snapshot",
        fail_wave_snapshot_insert,
    )

    with pytest.raises(
        RuntimeError,
        match="wave snapshot database unavailable",
    ):
        run_pipeline(config)


def test_wave_normalized_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        wave_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return wave_payload(location)

    def fail_wave_hourly_insert(**kwargs: Any) -> int:
        raise RuntimeError("wave normalized storage unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.insert_wave_hourly",
        fail_wave_hourly_insert,
    )

    with pytest.raises(
        RuntimeError,
        match="wave normalized storage unavailable",
    ):
        run_pipeline(config)
