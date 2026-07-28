from pathlib import Path

import pytest

from forecast_ops.config import load_config


def write_config(
    config_dir: Path,
    environment: str = "dev",
    overrides: str = "",
) -> None:
    config_file = config_dir / f"{environment}.yml"
    config_file.write_text(
        f"""
environment: {environment}

locations:
  - id: prague
    name: Prague
    latitude: 50.0755
    longitude: 14.4378

api:
  base_url: https://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
    - precipitation_probability
    - wind_speed_10m

storage:
  raw_data_path: data/dev/raw
  database_path: data/dev/forecast_ops.duckdb

logging:
  level: DEBUG

{overrides}
""".strip(),
        encoding="utf-8",
    )


def test_load_config_reads_valid_configuration(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)

    config = load_config("dev", config_dir=tmp_path)

    assert config["environment"] == "dev"
    assert config["locations"][0]["id"] == "prague"
    assert config["api"]["forecast_days"] == 2


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
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        "- item_one\n- item_two\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="configuration must contain a yaml mapping",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_requires_matching_environment(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        """
environment: prod

locations:
  - id: prague
    name: Prague
    latitude: 50.0755
    longitude: 14.4378

api:
  base_url: https://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
    - precipitation_probability
    - wind_speed_10m

storage:
  raw_data_path: data/prod/raw
  database_path: data/prod/forecast_ops.duckdb

logging:
  level: INFO
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="configuration environment must match requested environment",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_requires_locations(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        """
environment: dev
locations: []
api:
  base_url: https://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
    - precipitation_probability
    - wind_speed_10m
storage:
  raw_data_path: data/dev/raw
  database_path: data/dev/forecast_ops.duckdb
logging:
  level: DEBUG
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="locations must be a nonempty list",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_rejects_duplicate_location_ids(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        """
environment: dev
locations:
  - id: prague
    name: Prague
    latitude: 50.0755
    longitude: 14.4378
  - id: prague
    name: Prague duplicate
    latitude: 50.1
    longitude: 14.5
api:
  base_url: https://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
    - precipitation_probability
    - wind_speed_10m
storage:
  raw_data_path: data/dev/raw
  database_path: data/dev/forecast_ops.duckdb
logging:
  level: DEBUG
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="location id must be unique: prague",
    ):
        load_config("dev", config_dir=tmp_path)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("latitude", 91),
        ("longitude", -181),
    ],
)
def test_load_config_rejects_invalid_coordinates(
    tmp_path: Path,
    field_name: str,
    field_value: int,
) -> None:
    latitude = field_value if field_name == "latitude" else 50.0755
    longitude = field_value if field_name == "longitude" else 14.4378

    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        f"""
environment: dev
locations:
  - id: prague
    name: Prague
    latitude: {latitude}
    longitude: {longitude}
api:
  base_url: https://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
    - precipitation_probability
    - wind_speed_10m
storage:
  raw_data_path: data/dev/raw
  database_path: data/dev/forecast_ops.duckdb
logging:
  level: DEBUG
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=rf"locations\[0\].{field_name} must be between",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_requires_https_api_url(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        """
environment: dev
locations:
  - id: prague
    name: Prague
    latitude: 50.0755
    longitude: 14.4378
api:
  base_url: http://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
    - precipitation_probability
    - wind_speed_10m
storage:
  raw_data_path: data/dev/raw
  database_path: data/dev/forecast_ops.duckdb
logging:
  level: DEBUG
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="api.base_url must use https",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_requires_all_hourly_fields(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        """
environment: dev
locations:
  - id: prague
    name: Prague
    latitude: 50.0755
    longitude: 14.4378
api:
  base_url: https://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
storage:
  raw_data_path: data/dev/raw
  database_path: data/dev/forecast_ops.duckdb
logging:
  level: DEBUG
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="api.hourly_fields is missing required fields",
    ):
        load_config("dev", config_dir=tmp_path)


def test_load_config_rejects_invalid_logging_level(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        """
environment: dev
locations:
  - id: prague
    name: Prague
    latitude: 50.0755
    longitude: 14.4378
api:
  base_url: https://api.open-meteo.com/v1/forecast
  forecast_days: 2
  hourly_fields:
    - temperature_2m
    - precipitation_probability
    - wind_speed_10m
storage:
  raw_data_path: data/dev/raw
  database_path: data/dev/forecast_ops.duckdb
logging:
  level: VERBOSE
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="unsupported logging level: VERBOSE",
    ):
        load_config("dev", config_dir=tmp_path)