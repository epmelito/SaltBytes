import math
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_FISHING_CONTEXTS = {"surf", "pier"}


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
    sst_config = _require_mapping(
        location_config.get("sst"),
        f"locations[{index}].sst",
    )
    sst_request_coordinate = _require_mapping(
        sst_config.get("request_coordinate"),
        f"locations[{index}].sst.request_coordinate",
    )
    sst_expected_returned_coordinate = _require_mapping(
        sst_config.get("expected_returned_coordinate"),
        f"locations[{index}].sst.expected_returned_coordinate",
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
        ("sst.request_coordinate", sst_request_coordinate),
        (
            "sst.expected_returned_coordinate",
            sst_expected_returned_coordinate,
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
    _require_string(
        sst_config.get("coastal_regime"),
        f"locations[{index}].sst.coastal_regime",
    )

    tide_config = _require_mapping(
        location_config.get("tide"),
        f"locations[{index}].tide",
    )
    for field_name in (
        "prediction_location",
        "station_id",
        "coastal_relationship",
        "known_limitation",
    ):
        _require_string(
            tide_config.get(field_name),
            f"locations[{index}].tide.{field_name}",
        )

    relationship_type = _require_string(
        tide_config.get("relationship_type"),
        f"locations[{index}].tide.relationship_type",
    )
    if relationship_type not in {"direct", "transfer"}:
        raise ValueError(
            f"locations[{index}].tide.relationship_type must be direct or transfer"
        )

    distance_km = _require_number_in_range(
        tide_config.get("distance_km"),
        f"locations[{index}].tide.distance_km",
        0,
        float("inf"),
    )
    if not math.isfinite(distance_km):
        raise ValueError(
            f"locations[{index}].tide.distance_km must be finite"
        )

    subordinate_fields = (
        "high_time_offset_minutes",
        "low_time_offset_minutes",
        "high_multiplier",
        "low_multiplier",
    )
    required_nullable_fields = ("reference_station", *subordinate_fields)
    missing_nullable_fields = [
        field_name
        for field_name in required_nullable_fields
        if field_name not in tide_config
    ]
    if missing_nullable_fields:
        raise ValueError(
            f"locations[{index}].tide must contain "
            f"{', '.join(missing_nullable_fields)}"
        )

    reference_station = tide_config["reference_station"]
    subordinate_values = [
        tide_config[field_name]
        for field_name in subordinate_fields
    ]
    if reference_station is None:
        if any(value is not None for value in subordinate_values):
            raise ValueError(
                f"locations[{index}].tide subordinate metadata must all be null"
            )
    else:
        _require_string(
            reference_station,
            f"locations[{index}].tide.reference_station",
        )
        for field_name, value in zip(
            subordinate_fields,
            subordinate_values,
            strict=True,
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or not math.isfinite(float(value))
            ):
                raise ValueError(
                    f"locations[{index}].tide.{field_name} must be a finite number"
                )


# validate all required pipeline configuration
def validate_config(
    config: dict[str, Any],
) -> None:
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

    display_timezone = _require_string(
        config.get("display_timezone"),
        "display_timezone",
    )
    try:
        ZoneInfo(display_timezone)
    except ZoneInfoNotFoundError as error:
        raise ValueError(
            f"display_timezone must be a valid IANA timezone: {display_timezone}"
        ) from error


# load and validate local configuration
def load_config(
    config_path: Path | str = "config/local.yml",
) -> dict[str, Any]:
    config_path = Path(config_path)

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

    validate_config(config)

    return config
