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
SST_FIELDS = ["sea_surface_temperature"]


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
                "sst": {
                    "request_coordinate": {
                        "latitude": 35.91,
                        "longitude": -75.54,
                    },
                    "expected_returned_coordinate": {
                        "latitude": 35.875,
                        "longitude": -75.54166,
                    },
                    "coastal_regime": "Atlantic-facing marine grid",
                },
                "tide": {
                    "prediction_location": (
                        "Jennettes Pier, Nags Head (ocean)"
                    ),
                    "station_id": "8652226",
                    "relationship_type": "direct",
                    "reference_station": "8651370",
                    "high_time_offset_minutes": -5,
                    "low_time_offset_minutes": 1,
                    "high_multiplier": 1.04,
                    "low_multiplier": 1.43,
                    "distance_km": 0.448,
                    "coastal_relationship": (
                        "Direct use at the Atlantic-facing pier"
                    ),
                    "known_limitation": (
                        "Prediction behavior remains distinct from observed "
                        "water levels"
                    ),
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
                "sst": {
                    "request_coordinate": {
                        "latitude": 33.93,
                        "longitude": -77.9,
                    },
                    "expected_returned_coordinate": {
                        "latitude": 33.958336,
                        "longitude": -77.87499,
                    },
                    "coastal_regime": (
                        "Atlantic-facing marine grid distinct from wave grid"
                    ),
                },
                "tide": {
                    "prediction_location": "Wilmington Beach",
                    "station_id": "8658559",
                    "relationship_type": "transfer",
                    "reference_station": "8654400",
                    "high_time_offset_minutes": 18,
                    "low_time_offset_minutes": 10,
                    "high_multiplier": 1.4,
                    "low_multiplier": 1.25,
                    "distance_km": 9.308,
                    "coastal_relationship": (
                        "Explicit transfer from the nearest reviewed "
                        "ocean-facing relationship"
                    ),
                    "known_limitation": (
                        "The prediction relationship is materially north of "
                        "the destination"
                    ),
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
        "sst_api": {
            "base_url": "https://example.test/marine",
            "model": "meteofrance_currents",
            "forecast_days": 7,
            "hourly_fields": SST_FIELDS,
        },
        "tide_api": {
            "base_url": (
                "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
            ),
            "product": "predictions",
            "interval": "hilo",
            "datum": "MLLW",
            "time_zone": "gmt",
            "units": "metric",
            "format": "json",
            "forecast_days": 7,
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


def sst_payload(location: dict[str, Any]) -> dict[str, Any]:
    start = datetime(2026, 7, 28)
    times = [
        (start + timedelta(hours=index)).isoformat(timespec="minutes")
        for index in range(168)
    ]
    returned_coordinate = location["sst"]["expected_returned_coordinate"]

    return {
        "latitude": returned_coordinate["latitude"],
        "longitude": returned_coordinate["longitude"],
        "timezone": "America/New_York",
        "utc_offset_seconds": -14400,
        "hourly": {
            "time": times,
            "sea_surface_temperature": [25.1] * 168,
        },
    }


def tide_payload(params: dict[str, Any]) -> dict[str, Any]:
    start = datetime.strptime(params["begin_date"], "%Y%m%d")

    return {
        "predictions": [
            {
                "t": (
                    start + timedelta(hours=index * 6)
                ).strftime("%Y-%m-%d %H:%M"),
                "v": str(0.1 if index % 2 == 0 else 1.2),
                "type": "L" if index % 2 == 0 else "H",
            }
            for index in range(39)
        ]
    }


@pytest.fixture(autouse=True)
def stub_later_source_fetches(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch_sst_forecast(
        location: dict[str, Any],
        sst_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        return sst_payload(location)

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_sst_forecast",
        fake_fetch_sst_forecast,
    )

    def fake_fetch_tide_predictions(
        tide_api_config: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        return tide_payload(params)

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_tide_predictions",
        fake_fetch_tide_predictions,
    )


def test_source_quality_failures_are_independent_and_collected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_weather_locations: list[str] = []
    fetched_wave_locations: list[str] = []
    fetched_sst_locations: list[str] = []

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

    def fake_fetch_sst_forecast(
        location: dict[str, Any],
        sst_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_sst_locations.append(location["id"])
        payload = sst_payload(location)

        if location["id"] == "jennettes_pier":
            payload["latitude"] = 0

        return payload

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_sst_forecast",
        fake_fetch_sst_forecast,
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
        sst_locations = connection.execute(
            """
            select location_id, count(*)
            from sst_hourly
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
    assert fetched_sst_locations == ["jennettes_pier", "fort_fisher"]
    assert run is not None
    assert run[0] == "failed"
    assert run[1] == 918
    assert "wave quality checks failed for jennettes_pier" in run[2]
    assert "wave:returned_longitude_matches_expected" in run[2]
    assert "weather quality checks failed for fort_fisher" in run[2]
    assert "weather:returned_latitude_matches_expected" in run[2]
    assert "sst quality checks failed for jennettes_pier" in run[2]
    assert "sst:returned_latitude_matches_expected" in run[2]
    assert str(error.value) == run[2]
    assert snapshots == [
        ("fort_fisher", "meteofrance_currents"),
        ("fort_fisher", "meteofrance_wave"),
        ("fort_fisher", None),
        ("jennettes_pier", "ncep_nbm_conus"),
        ("jennettes_pier", None),
    ]
    assert weather_locations == [("jennettes_pier", 168)]
    assert wave_locations == [("fort_fisher", 168)]
    assert sst_locations == [("fort_fisher", 168)]
    assert {
        ":".join(check_name.split(":", maxsplit=2)[:2])
        for check_name, _ in quality_results
    } == {
        "jennettes_pier:weather",
        "jennettes_pier:wave",
        "jennettes_pier:sst",
        "jennettes_pier:tide",
        "fort_fisher:weather",
        "fort_fisher:wave",
        "fort_fisher:sst",
        "fort_fisher:tide",
    }
    assert any(status == "fail" for _, status in quality_results)
    assert any(status == "pass" for _, status in quality_results)
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 5


def _test_sst_preflight_rejection_preserves_independent_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    del config["locations"][0]["sst"]
    config["locations"][1]["sst"]["coastal_regime"] = ""
    fetched_weather_locations: list[str] = []
    fetched_wave_locations: list[str] = []
    fetched_sst_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_weather_locations.append(location["id"])
        return atmospheric_payload(location)

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        wave_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_wave_locations.append(location["id"])
        return wave_payload(location)

    def fake_fetch_sst_forecast(
        location: dict[str, Any],
        sst_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_sst_locations.append(location["id"])
        return sst_payload(location)

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_sst_forecast",
        fake_fetch_sst_forecast,
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
            order by location_id
            """
        ).fetchall()
        wave_locations = connection.execute(
            """
            select location_id, count(*)
            from wave_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()
        sst_row_count = connection.execute(
            "select count(*) from sst_hourly"
        ).fetchone()
        failed_quality_checks = connection.execute(
            """
            select check_name
            from quality_results
            where status = 'fail'
            order by check_name
            """
        ).fetchall()

    expected_source_rows = [
        ("fort_fisher", 168),
        ("jennettes_pier", 168),
    ]

    assert fetched_weather_locations == ["jennettes_pier", "fort_fisher"]
    assert fetched_wave_locations == ["jennettes_pier", "fort_fisher"]
    assert fetched_sst_locations == []
    assert run is not None
    assert run[0] == "failed"
    assert run[1] == 1086
    assert str(error.value) == run[2]
    assert "sst quality checks failed for jennettes_pier" in run[2]
    assert "sst:relationship_present" in run[2]
    assert "sst quality checks failed for fort_fisher" in run[2]
    assert "sst:coastal_regime_present" in run[2]
    assert snapshots == [
        ("fort_fisher", "meteofrance_wave"),
        ("fort_fisher", "ncep_nbm_conus"),
        ("fort_fisher", None),
        ("jennettes_pier", "meteofrance_wave"),
        ("jennettes_pier", "ncep_nbm_conus"),
        ("jennettes_pier", None),
    ]
    assert weather_locations == expected_source_rows
    assert wave_locations == expected_source_rows
    assert sst_row_count == (0,)
    assert failed_quality_checks == [
        ("fort_fisher:sst:coastal_regime_present",),
        ("jennettes_pier:sst:coastal_regime_present",),
        ("jennettes_pier:sst:expected_returned_coordinate_usable",),
        ("jennettes_pier:sst:relationship_present",),
        ("jennettes_pier:sst:request_coordinate_usable",),
    ]
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 6


def _test_tide_preflight_rejection_preserves_other_sources_and_locations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    del config["locations"][0]["tide"]
    config["locations"][1]["tide"]["coastal_relationship"] = ""
    fetched_tide_stations: list[str] = []

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        lambda location, api_config: atmospheric_payload(location),
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        lambda location, wave_api_config: wave_payload(location),
    )

    def record_tide_fetch(
        tide_api_config: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_tide_stations.append(params["station"])
        return tide_payload(params)

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_tide_predictions",
        record_tide_fetch,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()
        source_counts = {
            table_name: connection.execute(
                f"select count(*) from {table_name}"
            ).fetchone()
            for table_name in (
                "forecast_hourly",
                "wave_hourly",
                "sst_hourly",
                "tide_snapshots",
                "tide_events",
                "tide_phase_hourly",
            )
        }
        failed_checks = connection.execute(
            """
            select check_name
            from quality_results
            where status = 'fail'
            order by check_name
            """
        ).fetchall()

    assert fetched_tide_stations == []
    assert run is not None
    assert run[0] == "failed"
    assert run[1] == 1008
    assert str(error.value) == run[2]
    assert "tide quality checks failed for jennettes_pier" in run[2]
    assert "tide:relationship_present" in run[2]
    assert "tide quality checks failed for fort_fisher" in run[2]
    assert "tide:relationship_metadata_usable" in run[2]
    assert source_counts == {
        "forecast_hourly": (336,),
        "wave_hourly": (336,),
        "sst_hourly": (336,),
        "tide_snapshots": (0,),
        "tide_events": (0,),
        "tide_phase_hourly": (0,),
    }
    assert (
        "jennettes_pier:tide:relationship_present",
    ) in failed_checks
    assert (
        "fort_fisher:tide:relationship_metadata_usable",
    ) in failed_checks
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 6


def test_rejected_tide_payload_does_not_block_later_location(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_tide_stations: list[str] = []

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        lambda location, api_config: atmospheric_payload(location),
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        lambda location, wave_api_config: wave_payload(location),
    )

    def fetch_tide_with_first_result_invalid(
        tide_api_config: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_tide_stations.append(params["station"])
        payload = tide_payload(params)

        if params["station"] == "8652226":
            payload["predictions"][4]["type"] = "H"

        return payload

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_tide_predictions",
        fetch_tide_with_first_result_invalid,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()
        tide_snapshots = connection.execute(
            """
            select snapshots.location_id, tide.station_id
            from tide_snapshots as tide
            inner join forecast_snapshots as snapshots
                on tide.snapshot_id = snapshots.snapshot_id
            """
        ).fetchall()
        tide_event_count = connection.execute(
            "select count(*) from tide_events"
        ).fetchone()
        tide_phase_count = connection.execute(
            "select count(*) from tide_phase_hourly"
        ).fetchone()

    assert fetched_tide_stations == ["8652226", "8658559"]
    assert run is not None
    assert run[0] == "failed"
    assert run[1] == 1215
    assert str(error.value) == run[2]
    assert "tide quality checks failed for jennettes_pier" in run[2]
    assert "tide:prediction_events_alternate" in run[2]
    assert tide_snapshots == [("fort_fisher", "8658559")]
    assert tide_event_count == (39,)
    assert tide_phase_count == (168,)
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 7


def test_weather_api_failure_is_isolated_and_recorded(
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
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        lambda location, wave_api_config: wave_payload(location),
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

    expected_error = (
        "weather API fetch failed for jennettes_pier: "
        "forecast api unavailable; "
        "weather API fetch failed for fort_fisher: "
        "forecast api unavailable"
    )
    assert fetched_locations == ["jennettes_pier", "fort_fisher"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1086, expected_error)


def test_wave_api_failure_is_isolated_and_recorded(
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

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()

    expected_error = (
        "wave API fetch failed for jennettes_pier: wave api unavailable; "
        "wave API fetch failed for fort_fisher: wave api unavailable"
    )
    assert fetched_wave_locations == ["jennettes_pier", "fort_fisher"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1086, expected_error)


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


def _test_wave_raw_storage_failure_aborts_immediately(
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


def _test_wave_snapshot_database_failure_aborts_immediately(
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


def test_sst_api_failure_is_isolated_and_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_sst_locations: list[str] = []

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

    def fail_fetch_sst_forecast(
        location: dict[str, Any],
        sst_api_config: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_sst_locations.append(location["id"])
        raise RuntimeError("sst api unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_sst_forecast",
        fail_fetch_sst_forecast,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()

    expected_error = (
        "sst API fetch failed for jennettes_pier: sst api unavailable; "
        "sst API fetch failed for fort_fisher: sst api unavailable"
    )
    assert fetched_sst_locations == ["jennettes_pier", "fort_fisher"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1086, expected_error)


@pytest.mark.parametrize(
    ("failure_point", "message"),
    [
        ("normalized", "sst normalized storage unavailable"),
    ],
)
def test_sst_persistence_failures_abort_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
    message: str,
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

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )

    if failure_point == "quality":
        from forecast_ops.database import (
            insert_quality_result as real_quality_insert,
        )

        def fail_sst_quality_insert(**kwargs: Any) -> None:
            if ":sst:" in kwargs["check_name"]:
                raise RuntimeError(message)
            real_quality_insert(**kwargs)

        monkeypatch.setattr(
            "forecast_ops.pipeline.insert_quality_result",
            fail_sst_quality_insert,
        )
    elif failure_point == "raw":
        from forecast_ops.storage import write_raw_snapshot as real_write

        raw_write_count = 0

        def fail_sst_raw_write(**kwargs: Any) -> dict[str, Any]:
            nonlocal raw_write_count
            raw_write_count += 1
            if raw_write_count == 3:
                raise OSError(message)
            return real_write(**kwargs)

        monkeypatch.setattr(
            "forecast_ops.pipeline.write_raw_snapshot",
            fail_sst_raw_write,
        )
    elif failure_point == "snapshot":
        from forecast_ops.database import (
            insert_forecast_snapshot as real_snapshot_insert,
        )

        def fail_sst_snapshot_insert(
            database_path: Path | str,
            metadata: dict[str, Any],
        ) -> None:
            if metadata["model_selector"] == "meteofrance_currents":
                raise RuntimeError(message)
            real_snapshot_insert(database_path, metadata)

        monkeypatch.setattr(
            "forecast_ops.pipeline.insert_forecast_snapshot",
            fail_sst_snapshot_insert,
        )
    else:
        def fail_sst_hourly_insert(**kwargs: Any) -> int:
            raise RuntimeError(message)

        monkeypatch.setattr(
            "forecast_ops.pipeline.insert_sst_hourly",
            fail_sst_hourly_insert,
        )

    with pytest.raises((OSError, RuntimeError), match=message):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()

    assert run == ("failed", 336, message)


def test_tide_api_failure_is_isolated_and_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_tide_stations: list[str] = []

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        lambda location, api_config: atmospheric_payload(location),
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        lambda location, wave_api_config: wave_payload(location),
    )

    def fail_fetch_tide_predictions(
        tide_api_config: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_tide_stations.append(params["station"])
        raise RuntimeError("tide api unavailable")

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_tide_predictions",
        fail_fetch_tide_predictions,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()

    expected_error = (
        "tide API fetch failed for jennettes_pier: tide api unavailable; "
        "tide API fetch failed for fort_fisher: tide api unavailable"
    )
    assert fetched_tide_stations == ["8652226", "8658559"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1008, expected_error)


@pytest.mark.parametrize(
    ("failure_point", "message"),
    [
        ("snapshot", "tide snapshot database unavailable"),
        ("events", "tide event storage unavailable"),
        ("phase", "tide phase storage unavailable"),
    ],
)
def test_tide_persistence_failures_abort_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
    message: str,
) -> None:
    config = pipeline_config(tmp_path)

    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_forecast",
        lambda location, api_config: atmospheric_payload(location),
    )
    monkeypatch.setattr(
        "forecast_ops.pipeline.fetch_wave_forecast",
        lambda location, wave_api_config: wave_payload(location),
    )

    if failure_point == "quality":
        from forecast_ops.database import (
            insert_quality_result as real_quality_insert,
        )

        def fail_tide_quality_insert(**kwargs: Any) -> None:
            if ":tide:" in kwargs["check_name"]:
                raise RuntimeError(message)
            real_quality_insert(**kwargs)

        monkeypatch.setattr(
            "forecast_ops.pipeline.insert_quality_result",
            fail_tide_quality_insert,
        )
    elif failure_point == "raw":
        from forecast_ops.storage import write_raw_snapshot as real_write

        raw_write_count = 0

        def fail_tide_raw_write(**kwargs: Any) -> dict[str, Any]:
            nonlocal raw_write_count
            raw_write_count += 1
            if raw_write_count == 4:
                raise OSError(message)
            return real_write(**kwargs)

        monkeypatch.setattr(
            "forecast_ops.pipeline.write_raw_snapshot",
            fail_tide_raw_write,
        )
    elif failure_point == "snapshot":
        monkeypatch.setattr(
            "forecast_ops.pipeline.insert_tide_snapshot",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError(message)),
        )
    elif failure_point == "events":
        monkeypatch.setattr(
            "forecast_ops.pipeline.insert_tide_events",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError(message)),
        )
    else:
        monkeypatch.setattr(
            "forecast_ops.pipeline.insert_tide_phase_hourly",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError(message)),
        )

    with pytest.raises((OSError, RuntimeError), match=message):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()

    assert run == ("failed", 504, message)
