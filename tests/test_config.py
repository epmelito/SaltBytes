from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

from saltbytes.config import load_config


def write_config(path: Path, config: Any) -> None:
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def test_local_config_contains_approved_locations_and_variable_settings() -> None:
    config = load_config()

    assert [location["id"] for location in config["locations"]] == [
        "jennettes_pier",
        "ocracoke_ramp_72",
        "fort_macon_ocean",
        "bogue_inlet_pier",
        "fort_fisher",
        "sunset_beach_pier",
        "little_bridge_sound_access",
    ]
    assert set(config) == {"locations", "storage", "logging", "display_timezone"}
    assert config["display_timezone"] == "America/New_York"
    assert config["storage"] == {
        "raw_data_path": "data/local/raw",
        "database_path": "data/local/saltbytes.duckdb",
    }


def test_local_config_retains_tide_relationships() -> None:
    config = load_config()

    assert {
        location["id"]: location["tide"]["station_id"]
        for location in config["locations"]
    } == {
        "jennettes_pier": "8652226",
        "ocracoke_ramp_72": "TEC2793",
        "fort_macon_ocean": "8656590",
        "bogue_inlet_pier": "TEC2837",
        "fort_fisher": "8658559",
        "sunset_beach_pier": "8659897",
        "little_bridge_sound_access": "8652591",
    }


def test_load_config_rejects_missing_location_coordinate(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    del config["locations"][0]["weather"]["request_coordinate"]["latitude"]
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="weather.request_coordinate.latitude"):
        load_config(config_path)


def test_load_config_requires_pressure_relationship(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    del config["locations"][0]["pressure"]
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="locations\\[0\\].pressure must be a mapping"):
        load_config(config_path)


def test_load_config_rejects_invalid_pressure_grid_coordinate(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    config["locations"][0]["pressure"]["expected_returned_coordinate"]["latitude"] = 100
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="pressure.expected_returned_coordinate.latitude"):
        load_config(config_path)


def test_load_config_rejects_invalid_tide_relationship(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    config["locations"][0]["tide"]["relationship_type"] = "nearby"
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="relationship_type must be direct or transfer"):
        load_config(config_path)


def test_load_config_rejects_invalid_logging_level(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    config["logging"]["level"] = "VERBOSE"
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="unsupported logging level: VERBOSE"):
        load_config(config_path)


def test_load_config_rejects_invalid_display_timezone(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    config["display_timezone"] = "invalid/timezone"
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="valid IANA timezone"):
        load_config(config_path)


def test_load_config_requires_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="configuration file not found"):
        load_config(tmp_path / "missing.yml")


def test_load_config_requires_mapping_root(tmp_path: Path) -> None:
    config_path = tmp_path / "local.yml"
    config_path.write_text("- location\n", encoding="utf-8")

    with pytest.raises(ValueError, match="configuration must contain a yaml mapping"):
        load_config(config_path)


def test_local_config_retains_reviewed_site_orientation() -> None:
    config = load_config()

    assert {
        location["id"]: (
            location["orientation"]["shore_normal_azimuth_degrees"],
            location["orientation"]["pier_seaward_azimuth_degrees"],
        )
        for location in config["locations"]
    } == {
        "jennettes_pier": (75, 70),
        "ocracoke_ramp_72": (135, None),
        "fort_macon_ocean": (185, None),
        "bogue_inlet_pier": (165, 175),
        "fort_fisher": (105, None),
        "sunset_beach_pier": (165, 180),
        "little_bridge_sound_access": (60, None),
    }

    for location in config["locations"]:
        orientation = location["orientation"]
        assert orientation["orientation_method"]
        assert orientation["orientation_source"]
        expected_review_date = (
            "2026-08-13"
            if location["id"] in {"sunset_beach_pier", "little_bridge_sound_access"}
            else "2026-08-01"
        )
        assert orientation["orientation_reviewed_at"] == expected_review_date
        assert orientation["orientation_limitation"]


def test_local_config_contains_approved_sunset_relationships() -> None:
    config = load_config()
    sunset = next(
        location
        for location in config["locations"]
        if location["id"] == "sunset_beach_pier"
    )

    assert sunset["name"] == "Sunset Beach Pier"
    assert sunset["fishing_context"] == "pier"
    assert sunset["display_coordinate"] == {
        "latitude": 33.865,
        "longitude": -78.5067,
    }
    assert sunset["weather"]["request_coordinate"] == sunset[
        "display_coordinate"
    ]
    assert sunset["weather"]["expected_returned_coordinate"] == {
        "latitude": 33.875553,
        "longitude": -78.49414,
    }
    assert sunset["wave"] == {
        "request_coordinate": {
            "latitude": 33.8389394,
            "longitude": -78.4982931,
        },
        "expected_returned_coordinate": {
            "latitude": 33.791664,
            "longitude": -78.45833,
        },
    }
    assert sunset["sst"]["request_coordinate"] == sunset["wave"][
        "request_coordinate"
    ]
    assert sunset["sst"]["expected_returned_coordinate"] == {
        "latitude": 33.875,
        "longitude": -78.45833,
    }
    assert sunset["tide"]["relationship_type"] == "direct"
    assert sunset["tide"]["reference_station"] is None
    assert all(
        sunset["tide"][field] is None
        for field in (
            "high_time_offset_minutes",
            "low_time_offset_minutes",
            "high_multiplier",
            "low_multiplier",
        )
    )


def test_load_config_rejects_missing_orientation_field(
    tmp_path: Path,
) -> None:
    config = deepcopy(load_config())
    del config["locations"][0]["orientation"]["orientation_source"]
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(
        ValueError,
        match="orientation must contain orientation_source",
    ):
        load_config(config_path)


@pytest.mark.parametrize(
    "value",
    [-1, 360, float("inf"), float("nan"), "east"],
)
def test_load_config_rejects_invalid_shore_normal_azimuth(
    tmp_path: Path,
    value: Any,
) -> None:
    config = deepcopy(load_config())
    config["locations"][0]["orientation"][
        "shore_normal_azimuth_degrees"
    ] = value
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(
        ValueError,
        match="shore_normal_azimuth_degrees must be a finite azimuth",
    ):
        load_config(config_path)


@pytest.mark.parametrize(
    ("location_index", "value", "message"),
    [
        (
            0,
            None,
            "pier_seaward_azimuth_degrees must be a finite azimuth",
        ),
        (
            1,
            90,
            "pier_seaward_azimuth_degrees must be null for non-pier locations",
        ),
    ],
)
def test_load_config_enforces_pier_orientation_by_fishing_context(
    tmp_path: Path,
    location_index: int,
    value: float | None,
    message: str,
) -> None:
    config = deepcopy(load_config())
    config["locations"][location_index]["orientation"][
        "pier_seaward_azimuth_degrees"
    ] = value
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match=message):
        load_config(config_path)


def test_load_config_rejects_sound_side_pier_alignment(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    sound_side = next(
        location
        for location in config["locations"]
        if location["fishing_context"] == "sound-side"
    )
    sound_side["orientation"]["pier_seaward_azimuth_degrees"] = 90
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(
        ValueError,
        match="pier_seaward_azimuth_degrees must be null for non-pier locations",
    ):
        load_config(config_path)


def test_load_config_rejects_unsupported_fishing_context(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    config["locations"][0]["fishing_context"] = "estuary"
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="unsupported fishing context: estuary"):
        load_config(config_path)


def test_local_config_contains_approved_little_bridge_relationships() -> None:
    config = load_config()
    little_bridge = next(
        location
        for location in config["locations"]
        if location["id"] == "little_bridge_sound_access"
    )

    assert little_bridge["name"] == "Little Bridge Sound Access"
    assert little_bridge["fishing_context"] == "sound-side"
    assert little_bridge["display_coordinate"] == {
        "latitude": 35.898075,
        "longitude": -75.61635,
    }
    assert little_bridge["orientation"]["shore_normal_azimuth_degrees"] == 60
    assert little_bridge["orientation"]["pier_seaward_azimuth_degrees"] is None
    assert little_bridge["weather"] == {
        "request_coordinate": little_bridge["display_coordinate"],
        "expected_returned_coordinate": {
            "latitude": 35.898766,
            "longitude": -75.62099,
        },
        "coastal_regime": "Roanoke Sound atmospheric grid",
    }
    assert little_bridge["wave"] == {
        "request_coordinate": little_bridge["display_coordinate"],
        "expected_returned_coordinate": {
            "latitude": 35.875,
            "longitude": -75.62499,
        },
    }
    assert little_bridge["sst"] == {
        "request_coordinate": little_bridge["display_coordinate"],
        "expected_returned_coordinate": {
            "latitude": 35.875,
            "longitude": -75.62499,
        },
        "coastal_regime": "Roanoke Sound marine grid",
    }
    assert little_bridge["tide"] == {
        "prediction_location": "Roanoke Sound Channel",
        "station_id": "8652591",
        "relationship_type": "transfer",
        "reference_station": "8652587",
        "subordinate_station_type": "S",
        "high_time_offset_minutes": 97,
        "low_time_offset_minutes": 77,
        "high_multiplier": None,
        "low_multiplier": None,
        "height_offset_high_tide": 0.47,
        "height_offset_low_tide": 0.14,
        "height_adjusted_type": "R",
        "distance_km": 11.487,
        "coastal_relationship": (
            "Approved transferred astronomical high and low tide relationship "
            "through the NOAA subordinate station"
        ),
        "known_limitation": (
            "Prediction is not an observed water level, local current, or "
            "site-specific condition"
        ),
    }


def test_load_config_rejects_invalid_orientation_review_date(
    tmp_path: Path,
) -> None:
    config = deepcopy(load_config())
    config["locations"][0]["orientation"][
        "orientation_reviewed_at"
    ] = "August 1, 2026"
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="must be an ISO date"):
        load_config(config_path)
