from pathlib import Path
from typing import Any

import yaml


# load the configuration for the selected environment
def load_config(environment: str, config_dir: Path | str = "config") -> dict[str, Any]:
    config_path = Path(config_dir) / f"{environment}.yml"

    # fail early when the expected file does not exist
    if not config_path.exists():
        raise FileNotFoundError(f"configuration file not found: {config_path}")

    # safe_load limits yaml parsing to standard data types
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    # the root of each config file must be a yaml mapping
    if not isinstance(config, dict):
        raise ValueError(f"configuration must contain a yaml mapping: {config_path}")

    # prevent loading a mislabeled environment file
    if config.get("environment") != environment:
        raise ValueError(
            f"configuration environment must match requested environment: {environment}"
        )

    return config