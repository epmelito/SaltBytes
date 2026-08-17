import json
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pytest

from saltbytes.config import load_config
from saltbytes.pipeline import run_pipeline


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
        "timezone": "GMT",
        "utc_offset_seconds": 0,
        "hourly": {
            "time": times,
            "wind_speed_10m": [10.0 + value_offset] * 168,
            "wind_direction_10m": [180.0 + value_offset] * 168,
            "wind_gusts_10m": [15.0 + value_offset] * 168,
            "precipitation_probability": [20.0 + value_offset] * 168,
            "precipitation": [value_offset] * 168,
        },
    }


def wave_payload(
    location: dict[str, Any],
    value_offset: float,
) -> dict[str, Any]:
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
            "wave_height": [1.0 + value_offset] * 168,
            "wave_direction": [90.0 + value_offset] * 168,
            "wave_period": [8.0 + value_offset] * 168,
        },
    }


def sst_payload(
    location: dict[str, Any],
    value_offset: float,
) -> dict[str, Any]:
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
            "sea_surface_temperature": [25.0 + value_offset] * 168,
        },
    }


def tide_payload(
    params: dict[str, Any],
    value_offset: float,
) -> dict[str, Any]:
    start = datetime.strptime(params["begin_date"], "%Y%m%d")

    return {
        "predictions": [
            {
                "t": (
                    start + timedelta(hours=index * 6)
                ).strftime("%Y-%m-%d %H:%M"),
                "v": str(
                    (0.1 if index % 2 == 0 else 1.2) + value_offset
                ),
                "type": "L" if index % 2 == 0 else "H",
            }
            for index in range(39)
        ]
    }


def test_run_pipeline_ingests_all_seven_coastal_locations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = deepcopy(load_config())
    config["storage"] = {
        "raw_data_path": str(tmp_path / "raw"),
        "database_path": str(tmp_path / "saltbytes.duckdb"),
    }
    weather_payloads: dict[str, dict[str, Any]] = {}
    wave_payloads: dict[str, dict[str, Any]] = {}
    sst_payloads: dict[str, dict[str, Any]] = {}
    tide_payloads: dict[str, dict[str, Any]] = {}

    def fake_fetch_forecast(
        location: dict[str, Any],
        client: Any | None = None,
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
        weather_payloads[location["id"]] = payload
        return payload

    def fake_fetch_wave_forecast(
        location: dict[str, Any],
        client: Any | None = None,
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
        payload = wave_payload(location, value_offset)
        wave_payloads[location["id"]] = payload
        return payload

    def fake_fetch_sst_forecast(
        location: dict[str, Any],
        client: Any | None = None,
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
        payload = sst_payload(location, value_offset)
        sst_payloads[location["id"]] = payload
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

    def fake_fetch_tide_predictions(
        params: dict[str, Any],
    ) -> dict[str, Any]:
        location = next(
            location
            for location in config["locations"]
            if location["tide"]["station_id"] == params["station"]
        )
        value_offset = float(config["locations"].index(location))
        payload = tide_payload(params, value_offset)
        tide_payloads[location["id"]] = payload
        return payload

    monkeypatch.setattr(
        "saltbytes.pipeline.fetch_tide_predictions",
        fake_fetch_tide_predictions,
    )
    fixed_now = datetime(2026, 7, 28)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz: object = None) -> datetime:
            return fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr("saltbytes.pipeline.datetime", FixedDatetime)

    result = run_pipeline(config)

    assert result["status"] == "success"
    assert result["snapshots_written"] == 28
    assert result["rows_loaded"] == 4977

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
                returned_longitude
            from forecast_snapshots
            order by location_id, model_selector
            """
        ).fetchall()
        weather_hourly_counts = connection.execute(
            """
            select location_id, count(*)
            from forecast_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()
        wave_hourly_counts = connection.execute(
            """
            select location_id, count(*)
            from wave_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()
        sst_hourly_counts = connection.execute(
            """
            select location_id, count(*)
            from sst_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()
        tide_event_counts = connection.execute(
            """
            select location_id, count(*)
            from tide_events
            group by location_id
            order by location_id
            """
        ).fetchall()
        tide_phase_counts = connection.execute(
            """
            select location_id, count(*)
            from tide_phase_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()
        tide_relationships = connection.execute(
            """
            select
                snapshots.location_id,
                tide.station_id,
                tide.relationship_type,
                tide.high_multiplier,
                tide.low_multiplier,
                tide.height_offset_high_tide,
                tide.height_offset_low_tide,
                tide.subordinate_station_type,
                tide.height_adjusted_type
            from tide_snapshots as tide
            inner join forecast_snapshots as snapshots
                on tide.snapshot_id = snapshots.snapshot_id
            order by snapshots.location_id
            """
        ).fetchall()
        first_weather_rows = connection.execute(
            """
            select
                location_id,
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
        first_wave_rows = connection.execute(
            """
            select
                location_id,
                wave_height,
                wave_direction,
                wave_period
            from wave_hourly
            qualify row_number() over (
                partition by location_id
                order by forecast_time
            ) = 1
            order by location_id
            """
        ).fetchall()
        first_sst_rows = connection.execute(
            """
            select
                location_id,
                sea_surface_temperature
            from sst_hourly
            qualify row_number() over (
                partition by location_id
                order by forecast_time
            ) = 1
            order by location_id
            """
        ).fetchall()
        source_results = connection.execute(
            """
            select location_id, source, status, detail
            from source_results
            order by location_id, source
            """
        ).fetchall()
        run_locations = connection.execute(
            """
            select
                location_id,
                shore_normal_azimuth_degrees,
                pier_seaward_azimuth_degrees
            from run_locations
            order by location_id
            """
        ).fetchall()
        integrated_row_count = connection.execute(
            "select count(*) from coastal_conditions_hourly"
        ).fetchone()
        integrated_location_counts = connection.execute(
            """
            select location_id, count(*)
            from coastal_conditions_hourly
            group by location_id
            order by location_id
            """
        ).fetchall()
        integrated_complete_rows = connection.execute(
            """
            select count(*)
            from coastal_conditions_hourly
            where weather_status = 'success'
                and wave_status = 'success'
                and sst_status = 'success'
                and tide_status = 'success'
                and weather_snapshot_id is not null
                and wave_snapshot_id is not null
                and sst_snapshot_id is not null
                and tide_snapshot_id is not null
                and shore_normal_azimuth_degrees is not null
                and wind_speed_10m is not null
                and wind_to_shore_angle_degrees is not null
                and wave_height is not null
                and wave_to_shore_angle_degrees is not null
                and sea_surface_temperature is not null
                and tide_phase is not null
            """
        ).fetchone()

    locations_by_id = {
        location["id"]: location
        for location in config["locations"]
    }

    assert run == ("success", 4977, None)
    assert weather_hourly_counts == [
        ("bogue_inlet_pier", 168),
        ("fort_fisher", 168),
        ("fort_macon_ocean", 168),
        ("jennettes_pier", 168),
        ("little_bridge_sound_access", 168),
        ("ocracoke_ramp_72", 168),
        ("sunset_beach_pier", 168),
    ]
    assert wave_hourly_counts == weather_hourly_counts
    assert sst_hourly_counts == weather_hourly_counts
    assert tide_event_counts == [
        ("bogue_inlet_pier", 39),
        ("fort_fisher", 39),
        ("fort_macon_ocean", 39),
        ("jennettes_pier", 39),
        ("little_bridge_sound_access", 39),
        ("ocracoke_ramp_72", 39),
        ("sunset_beach_pier", 39),
    ]
    assert tide_phase_counts == weather_hourly_counts
    assert tide_relationships == [
        ("bogue_inlet_pier", "TEC2837", "transfer", 0.73, 0.83, None, None, None, None),
        ("fort_fisher", "8658559", "transfer", 1.4, 1.25, None, None, None, None),
        ("fort_macon_ocean", "8656590", "transfer", None, None, None, None, None, None),
        ("jennettes_pier", "8652226", "direct", 1.04, 1.43, None, None, None, None),
        ("little_bridge_sound_access", "8652591", "transfer", None, None, 0.47, 0.14, "S", "R"),
        ("ocracoke_ramp_72", "TEC2793", "transfer", 0.63, 0.83, None, None, None, None),
        ("sunset_beach_pier", "8659897", "direct", None, None, None, None, None, None),
    ]
    assert len(first_weather_rows) == 7
    assert all(
        all(value is not None for value in row[1:])
        for row in first_weather_rows
    )
    assert len(first_wave_rows) == 7
    assert all(
        all(value is not None for value in row[1:])
        for row in first_wave_rows
    )
    assert len(first_sst_rows) == 7
    assert all(row[1] is not None for row in first_sst_rows)
    assert run_locations == [
        ("bogue_inlet_pier", 165.0, 175.0),
        ("fort_fisher", 105.0, None),
        ("fort_macon_ocean", 185.0, None),
        ("jennettes_pier", 75.0, 70.0),
        ("little_bridge_sound_access", 60.0, None),
        ("ocracoke_ramp_72", 135.0, None),
        ("sunset_beach_pier", 165.0, 180.0),
    ]
    assert len(source_results) == 28
    assert all(status == "success" for _, _, status, _ in source_results)
    assert {source for _, source, _, _ in source_results} == {
        "weather",
        "wave",
        "sst",
        "tide",
    }
    assert all(detail is None for _, _, _, detail in source_results)
    assert integrated_row_count == (1176,)
    assert integrated_location_counts == weather_hourly_counts
    assert integrated_complete_rows == (1176,)

    for snapshot in snapshots:
        location_id = snapshot[0]
        raw_file_path = Path(snapshot[1])
        location = locations_by_id[location_id]
        model_selector = snapshot[2]
        if model_selector == "ncep_nbm_conus":
            source_relationship = location["weather"]
            expected_payload = weather_payloads[location_id]
        elif model_selector == "meteofrance_wave":
            source_relationship = location["wave"]
            expected_payload = wave_payloads[location_id]
        elif model_selector == "meteofrance_currents":
            source_relationship = location["sst"]
            expected_payload = sst_payloads[location_id]
        else:
            assert snapshot[3:] == (None, None, None, None)
            expected_payload = tide_payloads[location_id]
            assert raw_file_path.exists()
            assert json.loads(
                raw_file_path.read_text(encoding="utf-8")
            ) == expected_payload
            continue
        request_coordinate = source_relationship["request_coordinate"]
        returned_coordinate = source_relationship[
            "expected_returned_coordinate"
        ]

        assert snapshot[3:] == (
            request_coordinate["latitude"],
            request_coordinate["longitude"],
            returned_coordinate["latitude"],
            returned_coordinate["longitude"],
        )
        assert raw_file_path.exists()
        assert json.loads(
            raw_file_path.read_text(encoding="utf-8")
        ) == expected_payload

    assert len(snapshots) == 28
    assert {
        snapshot[2]
        for snapshot in snapshots
    } == {
        "ncep_nbm_conus",
        "meteofrance_wave",
        "meteofrance_currents",
        None,
    }
    assert len({snapshot[1] for snapshot in snapshots}) == 28

    expected_raw_directory = (
        tmp_path
        / "raw"
        / "2026"
        / "07"
        / "28"
        / f"000000Z_{result['run_id']}"
    )
    assert {
        Path(snapshot[1]).parent
        for snapshot in snapshots
    } == {expected_raw_directory}
