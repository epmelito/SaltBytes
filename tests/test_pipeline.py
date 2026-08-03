import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import httpx
import pytest

import saltbytes.database as database
from saltbytes.pipeline import run_pipeline
from saltbytes.solar import solar_calculation_provenance


def pipeline_config(tmp_path: Path) -> dict[str, Any]:
    return {
        "display_timezone": "America/New_York",
        "locations": [
            {
                "id": "jennettes_pier",
                "name": "Jennette's Pier",
                "fishing_context": "pier",
                "orientation": {
                    "shore_normal_azimuth_degrees": 75,
                    "pier_seaward_azimuth_degrees": 70,
                    "orientation_method": "manual satellite review",
                    "orientation_source": "reviewed satellite image",
                    "orientation_reviewed_at": "2026-08-01",
                    "orientation_limitation": (
                        "local shoreline segment only"
                    ),
                },
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
                "orientation": {
                    "shore_normal_azimuth_degrees": 105,
                    "pier_seaward_azimuth_degrees": None,
                    "orientation_method": "manual satellite review",
                    "orientation_source": "reviewed satellite image",
                    "orientation_reviewed_at": "2026-08-01",
                    "orientation_limitation": (
                        "local shoreline segment only"
                    ),
                },
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
        "storage": {
            "raw_data_path": str(tmp_path / "raw"),
            "database_path": str(tmp_path / "saltbytes.duckdb"),
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
        "timezone": "GMT",
        "utc_offset_seconds": 0,
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
        "timezone": "GMT",
        "utc_offset_seconds": 0,
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
        "timezone": "GMT",
        "utc_offset_seconds": 0,
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
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        return sst_payload(location)

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_sst_forecast",
        fake_fetch_sst_forecast,
    )

    def fake_fetch_tide_predictions(
        params: dict[str, Any],
    ) -> dict[str, Any]:
        return tide_payload(params)

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_tide_predictions",
        fake_fetch_tide_predictions,
    )


def test_pipeline_reuses_and_closes_open_meteo_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    clients: list[Any] = []
    request_clients: list[Any] = []

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            assert timeout == 10.0
            self.closed = False
            clients.append(self)

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            self.closed = True

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        request_clients.append(client)
        return atmospheric_payload(location)

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        request_clients.append(client)
        return wave_payload(location)

    def fake_fetch_sst_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        request_clients.append(client)
        return sst_payload(location)

    monkeypatch.setattr("saltbytes.pipeline.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast", fake_fetch_forecast
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast", fake_fetch_wave_forecast
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_sst_forecast", fake_fetch_sst_forecast
    )

    result = run_pipeline(config)

    assert len(clients) == 1
    assert request_clients == [clients[0]] * 6
    assert clients[0].closed is True

    with duckdb.connect(
        str(config["storage"]["database_path"]), read_only=True
    ) as connection:
        contexts = connection.execute(
            """
            select
                display_latitude,
                display_longitude,
                display_timezone,
                calculation_contract,
                calculation_library,
                calculation_library_version
            from run_location_solar_context
            where run_id = ?
            order by location_id
            """,
            [result["run_id"]],
        ).fetchall()

    provenance = solar_calculation_provenance()
    assert contexts == [
        (33.9534, -77.929, "America/New_York", *provenance.values()),
        (35.9096355, -75.5966537, "America/New_York", *provenance.values()),
    ]


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
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_weather_locations.append(location["id"])
        payload = atmospheric_payload(location)

        if location["id"] == "fort_fisher":
            payload["latitude"] = 0

        return payload

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_wave_locations.append(location["id"])
        payload = wave_payload(location)

        if location["id"] == "jennettes_pier":
            payload["longitude"] = 0

        return payload

    def fake_fetch_sst_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_sst_locations.append(location["id"])
        payload = sst_payload(location)

        if location["id"] == "jennettes_pier":
            payload["latitude"] = 0

        return payload

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_sst_forecast",
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
        source_results = connection.execute(
            """
            select location_id, source, status, detail
            from source_results
            order by location_id, source
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
    assert source_results == [
        ("fort_fisher", "sst", "success", None),
        ("fort_fisher", "tide", "success", None),
        ("fort_fisher", "wave", "success", None),
        (
            "fort_fisher",
            "weather",
            "validation_failed",
            "weather:returned_latitude_matches_expected",
        ),
        (
            "jennettes_pier",
            "sst",
            "validation_failed",
            "sst:returned_latitude_matches_expected",
        ),
        ("jennettes_pier", "tide", "success", None),
        (
            "jennettes_pier",
            "wave",
            "validation_failed",
            "wave:returned_longitude_matches_expected",
        ),
        ("jennettes_pier", "weather", "success", None),
    ]
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 5


def test_rejected_tide_payload_does_not_block_later_location(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_tide_stations: list[str] = []

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        lambda location, client: atmospheric_payload(location),
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        lambda location, client: wave_payload(location),
    )

    def fetch_tide_with_first_result_invalid(
        params: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_tide_stations.append(params["station"])
        payload = tide_payload(params)

        if params["station"] == "8652226":
            payload["predictions"][4]["type"] = "H"

        return payload

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_tide_predictions",
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
        tide_results = connection.execute(
            """
            select location_id, status, detail
            from source_results
            where source = 'tide'
            order by location_id
            """
        ).fetchall()

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
    assert tide_results == [
        ("fort_fisher", "success", None),
        (
            "jennettes_pier",
            "validation_failed",
            "tide:prediction_events_alternate, tide:phase_bounds_complete",
        ),
    ]
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 7


def test_weather_api_failure_is_isolated_and_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_locations.append(location["id"])
        raise httpx.ConnectTimeout("forecast api timed out")

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        lambda location, client: wave_payload(location),
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
        source_results = connection.execute(
            """
            select location_id, status, detail
            from source_results
            where source = 'weather'
            order by location_id
            """
        ).fetchall()

    expected_error = (
        "weather API fetch failed for jennettes_pier: "
        "forecast api timed out; "
        "weather API fetch failed for fort_fisher: "
        "forecast api timed out"
    )
    assert fetched_locations == ["jennettes_pier", "fort_fisher"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1086, expected_error)
    assert source_results == [
        ("fort_fisher", "fetch_failed", "forecast api timed out"),
        ("jennettes_pier", "fetch_failed", "forecast api timed out"),
    ]


def test_wave_api_failure_is_isolated_and_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_wave_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fail_fetch_wave_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_wave_locations.append(location["id"])
        raise RuntimeError("wave api unavailable")

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        fail_fetch_wave_forecast,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()
        source_results = connection.execute(
            """
            select location_id, status, detail
            from source_results
            where source = 'wave'
            order by location_id
            """
        ).fetchall()

    expected_error = (
        "wave API fetch failed for jennettes_pier: wave api unavailable; "
        "wave API fetch failed for fort_fisher: wave api unavailable"
    )
    assert fetched_wave_locations == ["jennettes_pier", "fort_fisher"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1086, expected_error)
    assert source_results == [
        ("fort_fisher", "fetch_failed", "wave api unavailable"),
        ("jennettes_pier", "fetch_failed", "wave api unavailable"),
    ]


def test_raw_storage_failure_aborts_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    config = pipeline_config(tmp_path)
    caplog.set_level(logging.INFO, logger="saltbytes.pipeline")
    fetched_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_locations.append(location["id"])
        return atmospheric_payload(location)

    def fail_raw_storage(**kwargs: Any) -> dict[str, Any]:
        raise OSError("raw storage unavailable")

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.write_raw_snapshot",
        fail_raw_storage,
    )

    with pytest.raises(RuntimeError, match="weather source persistence failed"):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            """
            select status, rows_loaded, error_message
            from pipeline_runs
            """
        ).fetchone()
        source_result = connection.execute(
            """
            select status, detail
            from source_results
            where location_id = 'jennettes_pier' and source = 'weather'
            """
        ).fetchone()
    assert fetched_locations == ["jennettes_pier"]
    assert run == (
        "failed",
        0,
        "weather source persistence failed for jennettes_pier at "
        "raw snapshot: raw storage unavailable",
    )
    assert source_result == (
        "persistence_failed",
        "raw snapshot: raw storage unavailable",
    )
    assert "weather quality checks passed" in caplog.text
    assert "weather source persistence failed" in caplog.text
    assert "weather source persistence completed" not in caplog.text
    assert "pipeline failed" in caplog.text


def test_sst_api_failure_is_isolated_and_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_sst_locations: list[str] = []

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        return atmospheric_payload(location)

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        return wave_payload(location)

    def fail_fetch_sst_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_sst_locations.append(location["id"])
        raise RuntimeError("sst api unavailable")

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_sst_forecast",
        fail_fetch_sst_forecast,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()
        source_results = connection.execute(
            """
            select location_id, status, detail
            from source_results
            where source = 'sst'
            order by location_id
            """
        ).fetchall()

    expected_error = (
        "sst API fetch failed for jennettes_pier: sst api unavailable; "
        "sst API fetch failed for fort_fisher: sst api unavailable"
    )
    assert fetched_sst_locations == ["jennettes_pier", "fort_fisher"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1086, expected_error)
    assert source_results == [
        ("fort_fisher", "fetch_failed", "sst api unavailable"),
        ("jennettes_pier", "fetch_failed", "sst api unavailable"),
    ]


@pytest.mark.parametrize(
    (
        "source",
        "database_helper",
        "model_selector",
        "normalized_table",
        "completed_sources",
    ),
    [
        (
            "weather",
            "insert_forecast_hourly",
            "ncep_nbm_conus",
            "forecast_hourly",
            [],
        ),
        (
            "wave",
            "insert_wave_hourly",
            "meteofrance_wave",
            "wave_hourly",
            ["weather"],
        ),
        (
            "sst",
            "insert_sst_hourly",
            "meteofrance_currents",
            "sst_hourly",
            ["weather", "wave"],
        ),
    ],
)
def test_normalized_persistence_failure_rolls_back_source_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    database_helper: str,
    model_selector: str,
    normalized_table: str,
    completed_sources: list[str],
) -> None:
    config = pipeline_config(tmp_path)
    fetched_sources: list[str] = []
    message = f"{source} normalized storage unavailable"

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_sources.append(f"weather:{location['id']}")
        return atmospheric_payload(location)

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_sources.append(f"wave:{location['id']}")
        return wave_payload(location)

    def fake_fetch_sst_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        fetched_sources.append(f"sst:{location['id']}")
        return sst_payload(location)

    def fail_normalized_write(*args: Any, **kwargs: Any) -> int:
        raise RuntimeError(message)

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_sst_forecast",
        fake_fetch_sst_forecast,
    )
    monkeypatch.setattr(database, database_helper, fail_normalized_write)

    with pytest.raises(RuntimeError, match=f"{source} source persistence failed"):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    detail = f"normalized rows: {message}"
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, error_message from pipeline_runs"
        ).fetchone()
        source_result = connection.execute(
            """
            select status, detail
            from source_results
            where source = ? and location_id = 'jennettes_pier'
            """,
            [source],
        ).fetchone()
        failed_snapshot_count = connection.execute(
            """
            select count(*) from forecast_snapshots
            where model_selector = ?
            """,
            [model_selector],
        ).fetchone()[0]
        failed_normalized_count = connection.execute(
            f"""
            select count(*) from {normalized_table}
            where snapshot_id in (
                select snapshot_id from forecast_snapshots
                where model_selector = ?
            )
            """,
            [model_selector],
        ).fetchone()[0]
        successful_failed_source_count = connection.execute(
            """
            select count(*) from source_results
            where source = ? and status = 'success'
            """,
            [source],
        ).fetchone()[0]
        successful_sources = connection.execute(
            """
            select distinct source from source_results
            where status = 'success'
            order by source
            """
        ).fetchall()

    assert run == (
        "failed",
        f"{source} source persistence failed for jennettes_pier at {detail}",
    )
    assert source_result == ("persistence_failed", detail)
    assert failed_snapshot_count == 0
    assert failed_normalized_count == 0
    assert successful_failed_source_count == 0
    assert successful_sources == [(name,) for name in sorted(completed_sources)]
    assert fetched_sources[-1] == f"{source}:jennettes_pier"
    assert f"{source}:fort_fisher" not in fetched_sources


def test_tide_api_failure_is_isolated_and_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)
    fetched_tide_stations: list[str] = []

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        lambda location, client: atmospheric_payload(location),
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        lambda location, client: wave_payload(location),
    )

    def fail_fetch_tide_predictions(
        params: dict[str, Any],
    ) -> dict[str, Any]:
        fetched_tide_stations.append(params["station"])
        raise RuntimeError("tide api unavailable")

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_tide_predictions",
        fail_fetch_tide_predictions,
    )

    with pytest.raises(ValueError) as error:
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()
        source_results = connection.execute(
            """
            select location_id, status, detail
            from source_results
            where source = 'tide'
            order by location_id
            """
        ).fetchall()

    expected_error = (
        "tide API fetch failed for jennettes_pier: tide api unavailable; "
        "tide API fetch failed for fort_fisher: tide api unavailable"
    )
    assert fetched_tide_stations == ["8652226", "8658559"]
    assert str(error.value) == expected_error
    assert run == ("failed", 1008, expected_error)
    assert source_results == [
        ("fort_fisher", "fetch_failed", "tide api unavailable"),
        ("jennettes_pier", "fetch_failed", "tide api unavailable"),
    ]


@pytest.mark.parametrize(
    ("failure_point", "stage", "message"),
    [
        ("snapshot", "snapshot provenance", "tide snapshot database unavailable"),
        ("events", "normalized events", "tide event storage unavailable"),
        ("phase", "normalized phases", "tide phase storage unavailable"),
        ("result", "source result", "tide source result storage unavailable"),
    ],
)
def test_tide_persistence_failures_abort_immediately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
    stage: str,
    message: str,
) -> None:
    config = pipeline_config(tmp_path)

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        lambda location, client: atmospheric_payload(location),
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        lambda location, client: wave_payload(location),
    )

    target = {
        "snapshot": "insert_tide_snapshot",
        "events": "insert_tide_events",
        "phase": "insert_tide_phase_hourly",
        "result": "insert_source_result",
    }[failure_point]
    if failure_point == "result":
        real_insert_source_result = database.insert_source_result

        def fail_tide_source_result(*args: Any, **kwargs: Any) -> None:
            if kwargs["source"] == "tide":
                raise RuntimeError(message)
            real_insert_source_result(*args, **kwargs)

        monkeypatch.setattr(database, target, fail_tide_source_result)
    else:
        monkeypatch.setattr(
            database,
            target,
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(message)),
        )

    with pytest.raises(RuntimeError, match="tide source persistence failed"):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded, error_message from pipeline_runs"
        ).fetchone()
        tide_counts = connection.execute(
            """
            select
                (select count(*) from forecast_snapshots where model_selector is null),
                (select count(*) from tide_snapshots),
                (select count(*) from tide_events),
                (select count(*) from tide_phase_hourly),
                (select count(*) from source_results where source = 'tide' and status = 'success')
            """
        ).fetchone()
        source_result = connection.execute(
            """
            select status, detail from source_results
            where source = 'tide' and location_id = 'jennettes_pier'
            """
        ).fetchone()

    detail = f"{stage}: {message}"
    assert run == (
        "failed",
        504,
        f"tide source persistence failed for jennettes_pier at {detail}",
    )
    assert tide_counts == (0, 0, 0, 0, 0)
    assert source_result == ("persistence_failed", detail)

def test_pipeline_persists_run_locations_before_all_sources_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = pipeline_config(tmp_path)

    def fail_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("weather unavailable")

    def fail_wave(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("wave unavailable")

    def fail_sst(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("sst unavailable")

    def fail_tide(
        params: dict[str, Any],
    ) -> dict[str, Any]:
        raise RuntimeError("tide unavailable")

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fail_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        fail_wave,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_sst_forecast",
        fail_sst,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_tide_predictions",
        fail_tide,
    )

    with pytest.raises(ValueError):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        run = connection.execute(
            "select status, rows_loaded from pipeline_runs"
        ).fetchone()
        locations = connection.execute(
            """
            select
                location_id,
                fishing_context,
                shore_normal_azimuth_degrees,
                pier_seaward_azimuth_degrees,
                orientation_method,
                orientation_source,
                orientation_reviewed_at,
                orientation_limitation
            from run_locations
            order by location_id
            """
        ).fetchall()
        source_result_count = connection.execute(
            "select count(*) from source_results"
        ).fetchone()

    assert run == ("failed", 0)
    assert locations == [
        (
            "fort_fisher",
            "surf",
            105.0,
            None,
            "manual satellite review",
            "reviewed satellite image",
            datetime(2026, 8, 1).date(),
            "local shoreline segment only",
        ),
        (
            "jennettes_pier",
            "pier",
            75.0,
            70.0,
            "manual satellite review",
            "reviewed satellite image",
            datetime(2026, 8, 1).date(),
            "local shoreline segment only",
        ),
    ]
    assert source_result_count == (8,)

@pytest.mark.parametrize(
    (
        "source",
        "field_name",
        "invalid_value",
        "table_name",
        "expected_detail",
    ),
    [
        (
            "weather",
            "wind_speed_10m",
            float("nan"),
            "forecast_hourly",
            "weather:wind_speed_10m_values_are_finite",
        ),
        (
            "weather",
            "wind_direction_10m",
            -1.0,
            "forecast_hourly",
            "weather:wind_direction_10m_values_are_in_range",
        ),
        (
            "wave",
            "wave_direction",
            float("inf"),
            "wave_hourly",
            (
                "wave:wave_direction_values_are_finite, "
                "wave:wave_direction_values_are_in_range"
            ),
        ),
    ],
)
def test_invalid_direction_fails_before_normalized_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    field_name: str,
    invalid_value: float,
    table_name: str,
    expected_detail: str,
) -> None:
    config = pipeline_config(tmp_path)

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        payload = atmospheric_payload(location)
        if source == "weather" and location["id"] == "jennettes_pier":
            payload["hourly"][field_name][0] = invalid_value
        return payload

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        payload = wave_payload(location)
        if source == "wave" and location["id"] == "jennettes_pier":
            payload["hourly"][field_name][0] = invalid_value
        return payload

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_forecast",
        fake_fetch_forecast,
    )
    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_wave_forecast",
        fake_fetch_wave_forecast,
    )

    with pytest.raises(ValueError):
        run_pipeline(config)

    database_path = Path(config["storage"]["database_path"])
    with duckdb.connect(str(database_path), read_only=True) as connection:
        source_result = connection.execute(
            """
            select status, detail
            from source_results
            where location_id = 'jennettes_pier'
                and source = ?
            """,
            [source],
        ).fetchone()
        rejected_location_count = connection.execute(
            f"""
            select count(*)
            from {table_name}
            where location_id = 'jennettes_pier'
            """
        ).fetchone()
        accepted_location_count = connection.execute(
            f"""
            select count(*)
            from {table_name}
            where location_id = 'fort_fisher'
            """
        ).fetchone()
        rejected_snapshot_count = connection.execute(
            """
            select count(*) from forecast_snapshots
            where location_id = 'jennettes_pier' and model_selector = 'ncep_nbm_conus'
            """
        ).fetchone()

    assert source_result == ("validation_failed", expected_detail)
    assert rejected_location_count == (0,)
    assert accepted_location_count == (168,)
    if source == "weather":
        assert rejected_snapshot_count == (0,)
