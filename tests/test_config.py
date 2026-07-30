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
    }


def test_load_config_rejects_missing_location_coordinate(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    del config["locations"][0]["weather"]["request_coordinate"]["latitude"]
    config_path = tmp_path / "local.yml"
    write_config(config_path, config)

    with pytest.raises(ValueError, match="weather.request_coordinate.latitude"):
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
