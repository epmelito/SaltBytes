from pathlib import Path

import pytest

from forecast_ops.config import load_config


def test_load_config_reads_yaml_mapping(tmp_path: Path) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text(
        """
environment: dev

locations:
  - id: prague
    name: Prague
    latitude: 50.0755
    longitude: 14.4378
""".strip(),
        encoding="utf-8",
    )

    config = load_config("dev", config_dir=tmp_path)

    assert config["environment"] == "dev"
    assert config["locations"][0]["id"] == "prague"


def test_load_config_raises_when_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="configuration file not found"):
        load_config("missing", config_dir=tmp_path)


def test_load_config_requires_yaml_mapping(tmp_path: Path) -> None:
    config_file = tmp_path / "dev.yml"
    config_file.write_text("- item_one\n- item_two\n", encoding="utf-8")

    with pytest.raises(ValueError, match="configuration must contain a yaml mapping"):
        load_config("dev", config_dir=tmp_path)

def test_load_config_requires_matching_environment(tmp_path: Path) -> None:
    config_file = tmp_path / "prod.yml"
    config_file.write_text("environment: dev\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="configuration environment must match requested environment",
    ):
        load_config("prod", config_dir=tmp_path)