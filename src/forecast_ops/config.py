from pathlib import Path
from typing import Any

import yaml

VALID_ENVIRONMENTS = {"dev", "test", "prod"}
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_FISHING_CONTEXTS = {"surf", "pier"}
REQUIRED_MODEL = "ncep_nbm_conus"
REQUIRED_HOURLY_FIELDS = {
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation_probability",
    "precipitation",
}
REQUIRED_WAVE_MODEL = "meteofrance_wave"
REQUIRED_WAVE_FIELDS = {
    "wave_height",
    "wave_direction",
    "wave_period",
}
REQUIRED_SST_MODEL = "meteofrance_currents"
REQUIRED_SST_FIELDS = {"sea_surface_temperature"}
REQUIRED_TIDE_REQUEST = {
    "product": "predictions",
    "interval": "hilo",
    "datum": "MLLW",
    "time_zone": "gmt",
    "units": "metric",
    "format": "json",
}


# require a mapping and return it with a useful type
def _require_mapping(
    value: Any,
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")

    return value


# require a nonempty string
def _require_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")

    return value


# require a numeric value within the expected range
def _require_number_in_range(
    value: Any,
    field_name: str,
    minimum: float,
    maximum: float,
) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a number")

    numeric_value = float(value)

    if not minimum <= numeric_value <= maximum:
        raise ValueError(
            f"{field_name} must be between {minimum} and {maximum}"
        )

    return numeric_value


# validate one configured location
def _validate_location(
    location: Any,
    index: int,
) -> None:
    location_config = _require_mapping(
        location,
        f"locations[{index}]",
    )

    _require_string(
        location_config.get("id"),
        f"locations[{index}].id",
    )
    _require_string(
        location_config.get("name"),
        f"locations[{index}].name",
    )

    fishing_context = _require_string(
        location_config.get("fishing_context"),
        f"locations[{index}].fishing_context",
    )

    if fishing_context not in VALID_FISHING_CONTEXTS:
        raise ValueError(
            f"unsupported fishing context: {fishing_context}"
        )

    display_coordinate = _require_mapping(
        location_config.get("display_coordinate"),
        f"locations[{index}].display_coordinate",
    )
    weather_config = _require_mapping(
        location_config.get("weather"),
        f"locations[{index}].weather",
    )
    request_coordinate = _require_mapping(
        weather_config.get("request_coordinate"),
        f"locations[{index}].weather.request_coordinate",
    )
    expected_returned_coordinate = _require_mapping(
        weather_config.get("expected_returned_coordinate"),
        f"locations[{index}].weather.expected_returned_coordinate",
    )
    wave_config = _require_mapping(
        location_config.get("wave"),
        f"locations[{index}].wave",
    )
    wave_request_coordinate = _require_mapping(
        wave_config.get("request_coordinate"),
        f"locations[{index}].wave.request_coordinate",
    )
    wave_expected_returned_coordinate = _require_mapping(
        wave_config.get("expected_returned_coordinate"),
        f"locations[{index}].wave.expected_returned_coordinate",
    )
    coordinates = (
        ("display_coordinate", display_coordinate),
        ("weather.request_coordinate", request_coordinate),
        (
            "weather.expected_returned_coordinate",
            expected_returned_coordinate,
        ),
        ("wave.request_coordinate", wave_request_coordinate),
        (
            "wave.expected_returned_coordinate",
            wave_expected_returned_coordinate,
        ),
    )

    for coordinate_name, coordinate in coordinates:
        _require_number_in_range(
            coordinate.get("latitude"),
            f"locations[{index}].{coordinate_name}.latitude",
            -90,
            90,
        )
        _require_number_in_range(
            coordinate.get("longitude"),
            f"locations[{index}].{coordinate_name}.longitude",
            -180,
            180,
        )

    _require_string(
        weather_config.get("coastal_regime"),
        f"locations[{index}].weather.coastal_regime",
    )


# validate all required pipeline configuration
def validate_config(
    config: dict[str, Any],
    requested_environment: str,
) -> None:
    environment = config.get("environment")

    if environment != requested_environment:
        raise ValueError(
            "configuration environment must match requested environment: "
            f"{requested_environment}"
        )

    if environment not in VALID_ENVIRONMENTS:
        raise ValueError(f"unsupported environment: {environment}")

    locations = config.get("locations")

    if not isinstance(locations, list) or not locations:
        raise ValueError("locations must be a nonempty list")

    location_ids: set[str] = set()

    for index, location in enumerate(locations):
        _validate_location(location, index)

        location_id = location["id"]

        if location_id in location_ids:
            raise ValueError(f"location id must be unique: {location_id}")

        location_ids.add(location_id)

    api_config = _require_mapping(config.get("api"), "api")
    base_url = _require_string(
        api_config.get("base_url"),
        "api.base_url",
    )

    if not base_url.startswith("https://"):
        raise ValueError("api.base_url must use https")

    model = _require_string(
        api_config.get("model"),
        "api.model",
    )

    if model != REQUIRED_MODEL:
        raise ValueError(f"unsupported api model: {model}")

    if api_config.get("forecast_days") != 7:
        raise ValueError("api.forecast_days must be 7")

    hourly_fields = api_config.get("hourly_fields")

    if not isinstance(hourly_fields, list) or not all(
        isinstance(field, str) and field
        for field in hourly_fields
    ):
        raise ValueError("api.hourly_fields must be a nonempty list of strings")

    configured_hourly_fields = set(hourly_fields)

    if (
        len(hourly_fields) != len(REQUIRED_HOURLY_FIELDS)
        or configured_hourly_fields != REQUIRED_HOURLY_FIELDS
    ):
        expected_fields = ", ".join(sorted(REQUIRED_HOURLY_FIELDS))
        raise ValueError(
            "api.hourly_fields must contain exactly: "
            f"{expected_fields}"
        )

    wave_api_config = _require_mapping(
        config.get("wave_api"),
        "wave_api",
    )
    wave_base_url = _require_string(
        wave_api_config.get("base_url"),
        "wave_api.base_url",
    )

    if not wave_base_url.startswith("https://"):
        raise ValueError("wave_api.base_url must use https")

    wave_model = _require_string(
        wave_api_config.get("model"),
        "wave_api.model",
    )

    if wave_model != REQUIRED_WAVE_MODEL:
        raise ValueError(f"unsupported wave api model: {wave_model}")

    if wave_api_config.get("forecast_days") != 7:
        raise ValueError("wave_api.forecast_days must be 7")

    wave_fields = wave_api_config.get("hourly_fields")

    if not isinstance(wave_fields, list) or not all(
        isinstance(field, str) and field
        for field in wave_fields
    ):
        raise ValueError(
            "wave_api.hourly_fields must be a nonempty list of strings"
        )

    configured_wave_fields = set(wave_fields)

    if (
        len(wave_fields) != len(REQUIRED_WAVE_FIELDS)
        or configured_wave_fields != REQUIRED_WAVE_FIELDS
    ):
        expected_wave_fields = ", ".join(sorted(REQUIRED_WAVE_FIELDS))
        raise ValueError(
            "wave_api.hourly_fields must contain exactly: "
            f"{expected_wave_fields}"
        )

    sst_api_config = _require_mapping(
        config.get("sst_api"),
        "sst_api",
    )
    sst_base_url = _require_string(
        sst_api_config.get("base_url"),
        "sst_api.base_url",
    )

    if not sst_base_url.startswith("https://"):
        raise ValueError("sst_api.base_url must use https")

    sst_model = _require_string(
        sst_api_config.get("model"),
        "sst_api.model",
    )

    if sst_model != REQUIRED_SST_MODEL:
        raise ValueError(f"unsupported sst api model: {sst_model}")

    if sst_api_config.get("forecast_days") != 7:
        raise ValueError("sst_api.forecast_days must be 7")

    sst_fields = sst_api_config.get("hourly_fields")

    if not isinstance(sst_fields, list) or not all(
        isinstance(field, str) and field
        for field in sst_fields
    ):
        raise ValueError(
            "sst_api.hourly_fields must be a nonempty list of strings"
        )

    configured_sst_fields = set(sst_fields)

    if (
        len(sst_fields) != len(REQUIRED_SST_FIELDS)
        or configured_sst_fields != REQUIRED_SST_FIELDS
    ):
        expected_sst_fields = ", ".join(sorted(REQUIRED_SST_FIELDS))
        raise ValueError(
            "sst_api.hourly_fields must contain exactly: "
            f"{expected_sst_fields}"
        )

    tide_api_config = _require_mapping(
        config.get("tide_api"),
        "tide_api",
    )
    tide_base_url = _require_string(
        tide_api_config.get("base_url"),
        "tide_api.base_url",
    )

    if not tide_base_url.startswith("https://"):
        raise ValueError("tide_api.base_url must use https")

    for field_name, expected_value in REQUIRED_TIDE_REQUEST.items():
        configured_value = _require_string(
            tide_api_config.get(field_name),
            f"tide_api.{field_name}",
        )

        if configured_value != expected_value:
            raise ValueError(
                f"unsupported tide api {field_name}: {configured_value}"
            )

    if tide_api_config.get("forecast_days") != 7:
        raise ValueError("tide_api.forecast_days must be 7")

    storage_config = _require_mapping(
        config.get("storage"),
        "storage",
    )
    _require_string(
        storage_config.get("raw_data_path"),
        "storage.raw_data_path",
    )
    _require_string(
        storage_config.get("database_path"),
        "storage.database_path",
    )

    logging_config = _require_mapping(
        config.get("logging"),
        "logging",
    )
    logging_level = _require_string(
        logging_config.get("level"),
        "logging.level",
    )

    if logging_level not in VALID_LOG_LEVELS:
        raise ValueError(f"unsupported logging level: {logging_level}")


# load and validate the configuration for the selected environment
def load_config(
    environment: str,
    config_dir: Path | str = "config",
) -> dict[str, Any]:
    config_path = Path(config_dir) / f"{environment}.yml"

    # fail early when the expected file does not exist
    if not config_path.exists():
        raise FileNotFoundError(
            f"configuration file not found: {config_path}"
        )

    # safe_load limits yaml parsing to standard data types
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    # the root of each config file must be a yaml mapping
    if not isinstance(config, dict):
        raise ValueError(
            f"configuration must contain a yaml mapping: {config_path}"
        )

    validate_config(config, requested_environment=environment)

    return config
