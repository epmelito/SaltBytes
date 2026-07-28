from pathlib import Path
from typing import Any

import yaml

VALID_ENVIRONMENTS = {"dev", "test", "prod"}
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
REQUIRED_HOURLY_FIELDS = {
    "temperature_2m",
    "precipitation_probability",
    "wind_speed_10m",
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
    _require_number_in_range(
        location_config.get("latitude"),
        f"locations[{index}].latitude",
        -90,
        90,
    )
    _require_number_in_range(
        location_config.get("longitude"),
        f"locations[{index}].longitude",
        -180,
        180,
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

    forecast_days = api_config.get("forecast_days")

    if (
        isinstance(forecast_days, bool)
        or not isinstance(forecast_days, int)
        or forecast_days < 1
        or forecast_days > 16
    ):
        raise ValueError("api.forecast_days must be between 1 and 16")

    hourly_fields = api_config.get("hourly_fields")

    if not isinstance(hourly_fields, list) or not all(
        isinstance(field, str) and field
        for field in hourly_fields
    ):
        raise ValueError("api.hourly_fields must be a nonempty list of strings")

    missing_hourly_fields = REQUIRED_HOURLY_FIELDS - set(hourly_fields)

    if missing_hourly_fields:
        missing_fields = ", ".join(sorted(missing_hourly_fields))
        raise ValueError(
            f"api.hourly_fields is missing required fields: {missing_fields}"
        )

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