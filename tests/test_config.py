from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

from forecast_ops.config import load_config


def valid_config(environment: str = "dev") -> dict[str, Any]:
    return {
        "environment": environment,
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
            }
        ],
        "api": {
            "base_url": "https://api.open-meteo.com/v1/forecast",
            "model": "ncep_nbm_conus",
            "forecast_days": 7,
            "hourly_fields": [
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "precipitation_probability",
                "precipitation",
            ],
        },
        "wave_api": {
            "base_url": "https://marine-api.open-meteo.com/v1/marine",
            "model": "meteofrance_wave",
            "forecast_days": 7,
            "hourly_fields": [
                "wave_height",
                "wave_direction",
                "wave_period",
            ],
        },
        "sst_api": {
            "base_url": "https://marine-api.open-meteo.com/v1/marine",
            "model": "meteofrance_currents",
            "forecast_days": 7,
            "hourly_fields": ["sea_surface_temperature"],
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
            "raw_data_path": f"data/{environment}/raw",
            "database_path": f"data/{environment}/forecast_ops.duckdb",
        },
        "logging": {"level": "DEBUG"},
    }


def write_config(
    config_dir: Path,
    config: Any,
    environment: str = "dev",
) -> None:
    config_file = config_dir / f"{environment}.yml"
    config_file.write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )


def test_load_config_reads_valid_configuration(
    tmp_path: Path,
) -> None:
    write_config(tmp_path, valid_config())

    config = load_config("dev", config_dir=tmp_path)

    assert config["environment"] == "dev"
    assert config["locations"][0]["id"] == "jennettes_pier"
    assert config["api"]["model"] == "ncep_nbm_conus"
    assert config["api"]["forecast_days"] == 7


@pytest.mark.parametrize("environment", ["dev", "test", "prod"])
def test_repository_config_contains_approved_coastal_contract(
    environment: str,
) -> None:
    config = load_config(environment)

    assert [location["id"] for location in config["locations"]] == [
        "jennettes_pier",
        "ocracoke_ramp_72",
        "fort_macon_ocean",
        "bogue_inlet_pier",
        "fort_fisher",
    ]
    assert config["api"] == {
        "base_url": "https://api.open-meteo.com/v1/forecast",
        "model": "ncep_nbm_conus",
        "forecast_days": 7,
        "hourly_fields": [
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "precipitation_probability",
            "precipitation",
        ],
    }
    assert config["wave_api"] == {
        "base_url": "https://marine-api.open-meteo.com/v1/marine",
        "model": "meteofrance_wave",
        "forecast_days": 7,
        "hourly_fields": [
            "wave_height",
            "wave_direction",
            "wave_period",
        ],
    }
    assert config["sst_api"] == {
        "base_url": "https://marine-api.open-meteo.com/v1/marine",
        "model": "meteofrance_currents",
        "forecast_days": 7,
        "hourly_fields": ["sea_surface_temperature"],
    }
    assert config["tide_api"] == {
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
    }


@pytest.mark.parametrize("environment", ["dev", "test", "prod"])
def test_repository_config_matches_approved_tide_relationships(
    environment: str,
) -> None:
    config = load_config(environment)
    relationships = {
        location["id"]: (
            location["tide"]["station_id"],
            location["tide"]["relationship_type"],
            location["tide"]["reference_station"],
            location["tide"]["high_time_offset_minutes"],
            location["tide"]["low_time_offset_minutes"],
            location["tide"]["high_multiplier"],
            location["tide"]["low_multiplier"],
            location["tide"]["distance_km"],
        )
        for location in config["locations"]
    }

    assert relationships == {
        "jennettes_pier": (
            "8652226",
            "direct",
            "8651370",
            -5,
            1,
            1.04,
            1.43,
            0.448,
        ),
        "ocracoke_ramp_72": (
            "TEC2793",
            "transfer",
            "8654400",
            9,
            11,
            0.63,
            0.83,
            3.697,
        ),
        "fort_macon_ocean": (
            "8656590",
            "transfer",
            None,
            None,
            None,
            None,
            None,
            1.321,
        ),
        "bogue_inlet_pier": (
            "TEC2837",
            "transfer",
            "8654400",
            13,
            15,
            0.73,
            0.83,
            6.164,
        ),
        "fort_fisher": (
            "8658559",
            "transfer",
            "8654400",
            18,
            10,
            1.4,
            1.25,
            9.308,
        ),
    }


@pytest.mark.parametrize("environment", ["dev", "test", "prod"])
def test_repository_config_matches_approved_spatial_relationships(
    environment: str,
) -> None:
    config = load_config(environment)

    relationships = {
        location["id"]: {
            "context": location["fishing_context"],
            "display": location["display_coordinate"],
            "request": location["weather"]["request_coordinate"],
            "returned": location["weather"]["expected_returned_coordinate"],
            "regime": location["weather"]["coastal_regime"],
            "wave_request": location["wave"]["request_coordinate"],
            "wave_returned": location["wave"][
                "expected_returned_coordinate"
            ],
            "sst_request": location["sst"]["request_coordinate"],
            "sst_returned": location["sst"][
                "expected_returned_coordinate"
            ],
            "sst_regime": location["sst"]["coastal_regime"],
        }
        for location in config["locations"]
    }

    assert relationships == {
        "jennettes_pier": {
            "context": "pier",
            "display": {"latitude": 35.9096355, "longitude": -75.5966537},
            "request": {"latitude": 35.9096355, "longitude": -75.5966537},
            "returned": {"latitude": 35.89557, "longitude": -75.5936},
            "regime": "Atlantic coastal grid",
            "wave_request": {"latitude": 35.91, "longitude": -75.54},
            "wave_returned": {
                "latitude": 35.875,
                "longitude": -75.54166,
            },
            "sst_request": {"latitude": 35.91, "longitude": -75.54},
            "sst_returned": {
                "latitude": 35.875,
                "longitude": -75.54166,
            },
            "sst_regime": "Atlantic-facing marine grid",
        },
        "ocracoke_ramp_72": {
            "context": "surf",
            "display": {"latitude": 35.0868922, "longitude": -75.9844152},
            "request": {"latitude": 35.0868922, "longitude": -75.9844152},
            "returned": {"latitude": 35.101955, "longitude": -75.983315},
            "regime": "Ocean-side coastal grid",
            "wave_request": {
                "latitude": 35.0868922,
                "longitude": -75.9844152,
            },
            "wave_returned": {
                "latitude": 35.125,
                "longitude": -75.95833,
            },
            "sst_request": {
                "latitude": 35.0868922,
                "longitude": -75.9844152,
            },
            "sst_returned": {
                "latitude": 35.125,
                "longitude": -75.95833,
            },
            "sst_regime": "Ocean-side Atlantic grid",
        },
        "fort_macon_ocean": {
            "context": "surf",
            "display": {"latitude": 34.6949437, "longitude": -76.697391},
            "request": {"latitude": 34.6933, "longitude": -76.7117},
            "returned": {"latitude": 34.68586, "longitude": -76.717896},
            "regime": "Atlantic coastal grid",
            "wave_request": {"latitude": 34.65, "longitude": -76.697},
            "wave_returned": {
                "latitude": 34.625,
                "longitude": -76.70833,
            },
            "sst_request": {"latitude": 34.65, "longitude": -76.697},
            "sst_returned": {
                "latitude": 34.625,
                "longitude": -76.70833,
            },
            "sst_regime": "Atlantic-facing marine grid",
        },
        "bogue_inlet_pier": {
            "context": "pier",
            "display": {"latitude": 34.6601236, "longitude": -77.0337424},
            "request": {"latitude": 34.6601236, "longitude": -77.0337424},
            "returned": {"latitude": 34.671284, "longitude": -76.996414},
            "regime": "Atlantic coastal grid",
            "wave_request": {
                "latitude": 34.6579882,
                "longitude": -77.0331663,
            },
            "wave_returned": {
                "latitude": 34.625,
                "longitude": -77.04166,
            },
            "sst_request": {
                "latitude": 34.6579882,
                "longitude": -77.0331663,
            },
            "sst_returned": {
                "latitude": 34.625,
                "longitude": -77.04166,
            },
            "sst_regime": "Atlantic-facing marine grid",
        },
        "fort_fisher": {
            "context": "surf",
            "display": {"latitude": 33.9534, "longitude": -77.929},
            "request": {"latitude": 33.9534, "longitude": -77.929},
            "returned": {"latitude": 33.954144, "longitude": -77.93454},
            "regime": "Atlantic coastal grid",
            "wave_request": {"latitude": 33.93, "longitude": -77.9},
            "wave_returned": {
                "latitude": 33.875,
                "longitude": -77.87499,
            },
            "sst_request": {"latitude": 33.93, "longitude": -77.9},
            "sst_returned": {
                "latitude": 33.958336,
                "longitude": -77.87499,
            },
            "sst_regime": (
                "Atlantic-facing marine grid distinct from wave grid"
            ),
        },
    }


def test_load_config_raises_when_file_is_missing(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="configuration file not found",
    ):
        load_config("missing", config_dir=tmp_path)


def test_load_config_requires_yaml_mapping(
    tmp_path: Path,
) -> None:
    write_config(tmp_path, ["item_one", "item_two"])

    with pytest.raises(
        ValueError,
        match="configuration must contain a yaml mapping",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_requires_matching_environment(
    tmp_path: Path,
) -> None:
    config = valid_config(environment="prod")
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="configuration environment must match requested environment",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_requires_locations(
    tmp_path: Path,
) -> None:
    config = valid_config()
    config["locations"] = []
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="locations must be a nonempty list",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_rejects_duplicate_location_ids(
    tmp_path: Path,
) -> None:
    config = valid_config()
    duplicate_location = deepcopy(config["locations"][0])
    config["locations"].append(duplicate_location)
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="location id must be unique: jennettes_pier",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize(
    ("coordinate_name", "field_name", "field_value"),
    [
        ("display_coordinate", "latitude", 91),
        ("display_coordinate", "longitude", -181),
        ("request_coordinate", "latitude", "invalid"),
        ("expected_returned_coordinate", "longitude", None),
    ],
)
def test_load_config_rejects_invalid_coordinates(
    tmp_path: Path,
    coordinate_name: str,
    field_name: str,
    field_value: Any,
) -> None:
    config = valid_config()

    if coordinate_name == "display_coordinate":
        coordinate = config["locations"][0]["display_coordinate"]
    else:
        coordinate = config["locations"][0]["weather"][coordinate_name]

    coordinate[field_name] = field_value
    write_config(tmp_path, config)

    with pytest.raises(ValueError, match=field_name):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize(
    ("field_path", "expected_message"),
    [
        (
            ("display_coordinate",),
            r"locations\[0\].display_coordinate must be a mapping",
        ),
        (
            ("weather",),
            r"locations\[0\].weather must be a mapping",
        ),
        (
            ("weather", "request_coordinate"),
            r"locations\[0\].weather.request_coordinate must be a mapping",
        ),
        (
            ("weather", "expected_returned_coordinate"),
            r"locations\[0\].weather.expected_returned_coordinate must be a mapping",
        ),
        (
            ("wave",),
            r"locations\[0\].wave must be a mapping",
        ),
        (
            ("wave", "request_coordinate"),
            r"locations\[0\].wave.request_coordinate must be a mapping",
        ),
        (
            ("wave", "expected_returned_coordinate"),
            r"locations\[0\].wave.expected_returned_coordinate must be a mapping",
        ),
    ],
)
def test_load_config_requires_complete_spatial_relationships(
    tmp_path: Path,
    field_path: tuple[str, ...],
    expected_message: str,
) -> None:
    config = valid_config()
    target = config["locations"][0]

    for key in field_path[:-1]:
        target = target[key]

    del target[field_path[-1]]
    write_config(tmp_path, config)

    with pytest.raises(ValueError, match=expected_message):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize(
    "field_path",
    [
        ("sst",),
        ("sst", "request_coordinate"),
        ("sst", "expected_returned_coordinate"),
        ("sst", "coastal_regime"),
    ],
)
def test_load_config_defers_incomplete_sst_relationships_to_pipeline(
    tmp_path: Path,
    field_path: tuple[str, ...],
) -> None:
    config = valid_config()
    target = config["locations"][0]

    for key in field_path[:-1]:
        target = target[key]

    del target[field_path[-1]]
    write_config(tmp_path, config)

    loaded_config = load_config("dev", config_dir=tmp_path)

    assert loaded_config["locations"][0]["id"] == "jennettes_pier"


@pytest.mark.parametrize(
    "field_path",
    [
        ("tide",),
        ("tide", "station_id"),
        ("tide", "relationship_type"),
        ("tide", "coastal_relationship"),
    ],
)
def test_load_config_defers_incomplete_tide_relationships_to_pipeline(
    tmp_path: Path,
    field_path: tuple[str, ...],
) -> None:
    config = valid_config()
    target = config["locations"][0]

    for key in field_path[:-1]:
        target = target[key]

    del target[field_path[-1]]
    write_config(tmp_path, config)

    loaded_config = load_config("dev", config_dir=tmp_path)

    assert loaded_config["locations"][0]["id"] == "jennettes_pier"


@pytest.mark.parametrize("fishing_context", ["boat", "", None])
def test_load_config_rejects_invalid_fishing_context(
    tmp_path: Path,
    fishing_context: Any,
) -> None:
    config = valid_config()
    config["locations"][0]["fishing_context"] = fishing_context
    write_config(tmp_path, config)

    with pytest.raises(ValueError, match="fishing_context|fishing context"):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("coastal_regime", ["", "   ", None])
def test_load_config_rejects_empty_coastal_regime(
    tmp_path: Path,
    coastal_regime: Any,
) -> None:
    config = valid_config()
    config["locations"][0]["weather"]["coastal_regime"] = coastal_regime
    write_config(tmp_path, config)

    with pytest.raises(ValueError, match="coastal_regime"):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize(
    ("coordinate_name", "field_name", "field_value"),
    [
        ("request_coordinate", "latitude", 91),
        ("request_coordinate", "longitude", "invalid"),
        ("expected_returned_coordinate", "latitude", None),
        ("expected_returned_coordinate", "longitude", -181),
    ],
)
def test_load_config_rejects_invalid_wave_coordinates(
    tmp_path: Path,
    coordinate_name: str,
    field_name: str,
    field_value: Any,
) -> None:
    config = valid_config()
    coordinate = config["locations"][0]["wave"][coordinate_name]
    coordinate[field_name] = field_value
    write_config(tmp_path, config)

    with pytest.raises(ValueError, match=field_name):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize(
    ("coordinate_name", "field_name", "field_value"),
    [
        ("request_coordinate", "latitude", 91),
        ("request_coordinate", "longitude", "invalid"),
        ("expected_returned_coordinate", "latitude", None),
        ("expected_returned_coordinate", "longitude", -181),
    ],
)
def test_load_config_defers_invalid_sst_coordinates_to_pipeline(
    tmp_path: Path,
    coordinate_name: str,
    field_name: str,
    field_value: Any,
) -> None:
    config = valid_config()
    coordinate = config["locations"][0]["sst"][coordinate_name]
    coordinate[field_name] = field_value
    write_config(tmp_path, config)

    loaded_config = load_config("dev", config_dir=tmp_path)

    assert loaded_config["locations"][0]["sst"][coordinate_name][
        field_name
    ] == field_value

@pytest.mark.parametrize("coastal_regime", ["", "   ", None])
def test_load_config_defers_empty_sst_coastal_regime_to_pipeline(
    tmp_path: Path,
    coastal_regime: Any,
) -> None:
    config = valid_config()
    config["locations"][0]["sst"]["coastal_regime"] = coastal_regime
    write_config(tmp_path, config)

    loaded_config = load_config("dev", config_dir=tmp_path)

    assert (
        loaded_config["locations"][0]["sst"]["coastal_regime"]
        == coastal_regime
    )


def test_load_config_requires_https_api_url(
    tmp_path: Path,
) -> None:
    config = valid_config()
    config["api"]["base_url"] = "http://api.open-meteo.com/v1/forecast"
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="api.base_url must use https",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_rejects_unapproved_model(
    tmp_path: Path,
) -> None:
    config = valid_config()
    config["api"]["model"] = "auto"
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="unsupported api model: auto",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("forecast_days", [2, 8, True, None])
def test_load_config_requires_seven_forecast_days(
    tmp_path: Path,
    forecast_days: Any,
) -> None:
    config = valid_config()
    config["api"]["forecast_days"] = forecast_days
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="api.forecast_days must be 7",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate"])
def test_load_config_requires_exact_hourly_fields(
    tmp_path: Path,
    change: str,
) -> None:
    config = valid_config()
    hourly_fields = config["api"]["hourly_fields"]

    if change == "missing":
        hourly_fields.remove("precipitation")
    elif change == "extra":
        hourly_fields.append("temperature_2m")
    else:
        hourly_fields[-1] = "wind_speed_10m"

    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="api.hourly_fields must contain exactly",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_rejects_unapproved_wave_model(
    tmp_path: Path,
) -> None:
    config = valid_config()
    config["wave_api"]["model"] = "auto"
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="unsupported wave api model: auto",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("forecast_days", [2, 8, True, None])
def test_load_config_requires_seven_wave_forecast_days(
    tmp_path: Path,
    forecast_days: Any,
) -> None:
    config = valid_config()
    config["wave_api"]["forecast_days"] = forecast_days
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="wave_api.forecast_days must be 7",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate"])
def test_load_config_requires_exact_wave_fields(
    tmp_path: Path,
    change: str,
) -> None:
    config = valid_config()
    wave_fields = config["wave_api"]["hourly_fields"]

    if change == "missing":
        wave_fields.remove("wave_period")
    elif change == "extra":
        wave_fields.append("sea_surface_temperature")
    else:
        wave_fields[-1] = "wave_height"

    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="wave_api.hourly_fields must contain exactly",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_rejects_unapproved_sst_model(
    tmp_path: Path,
) -> None:
    config = valid_config()
    config["sst_api"]["model"] = "auto"
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="unsupported sst api model: auto",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("forecast_days", [2, 8, True, None])
def test_load_config_requires_seven_sst_forecast_days(
    tmp_path: Path,
    forecast_days: Any,
) -> None:
    config = valid_config()
    config["sst_api"]["forecast_days"] = forecast_days
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="sst_api.forecast_days must be 7",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate"])
def test_load_config_requires_exact_sst_fields(
    tmp_path: Path,
    change: str,
) -> None:
    config = valid_config()
    sst_fields = config["sst_api"]["hourly_fields"]

    if change == "missing":
        sst_fields.clear()
    elif change == "extra":
        sst_fields.append("ocean_current_velocity")
    else:
        sst_fields.append("sea_surface_temperature")

    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="sst_api.hourly_fields must contain exactly",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("product", "water_level"),
        ("interval", "h"),
        ("datum", "MSL"),
        ("time_zone", "lst_ldt"),
        ("units", "english"),
        ("format", "csv"),
    ],
)
def test_load_config_rejects_unapproved_tide_request_contract(
    tmp_path: Path,
    field_name: str,
    invalid_value: str,
) -> None:
    config = valid_config()
    config["tide_api"][field_name] = invalid_value
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match=f"unsupported tide api {field_name}",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_requires_https_tide_api_url(
    tmp_path: Path,
) -> None:
    config = valid_config()
    config["tide_api"]["base_url"] = (
        "http://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    )
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="tide_api.base_url must use https",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize("forecast_days", [2, 8, True, None])
def test_load_config_requires_seven_tide_forecast_days(
    tmp_path: Path,
    forecast_days: Any,
) -> None:
    config = valid_config()
    config["tide_api"]["forecast_days"] = forecast_days
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="tide_api.forecast_days must be 7",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_rejects_invalid_logging_level(
    tmp_path: Path,
) -> None:
    config = valid_config()
    config["logging"]["level"] = "VERBOSE"
    write_config(tmp_path, config)

    with pytest.raises(
        ValueError,
        match="unsupported logging level: VERBOSE",
    ):
        load_config("dev", config_dir=tmp_path)
