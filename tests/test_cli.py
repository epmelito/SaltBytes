import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from forecast_ops.cli import main, parse_args
from forecast_ops.config import load_config


def test_parse_args_defaults_to_dev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["forecast-ops"])

    args = parse_args()

    assert args.environment == "dev"


def test_parse_args_accepts_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["forecast-ops", "--environment", "prod"],
    )

    args = parse_args()

    assert args.environment == "prod"


def test_main_runs_selected_environment(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = {
        "environment": "test",
    }
    result: dict[str, Any] = {
        "run_id": "run123",
        "environment": "test",
        "status": "success",
        "snapshots_written": 2,
        "rows_loaded": 96,
    }

    monkeypatch.setattr(
        sys,
        "argv",
        ["forecast-ops", "--environment", "test"],
    )
    monkeypatch.setattr(
        "forecast_ops.cli.load_config",
        lambda environment: config,
    )
    monkeypatch.setattr(
        "forecast_ops.cli.run_pipeline",
        lambda loaded_config: result,
    )
    monkeypatch.setattr(
        "forecast_ops.cli.configure_logging",
        lambda loaded_config: None,
    )

    main()

    output = capsys.readouterr().out

    assert "run id: run123" in output
    assert "environment: test" in output
    assert "status: success" in output
    assert "snapshots written: 2" in output
    assert "rows loaded: 96" in output


def test_main_reaches_pipeline_with_incomplete_sst_prerequisites(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = yaml.safe_load(
        Path("config/test.yml").read_text(encoding="utf-8")
    )
    del config["locations"][0]["sst"]
    config["locations"][1]["sst"]["coastal_regime"] = ""
    (tmp_path / "test.yml").write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )
    loaded_configs: list[dict[str, Any]] = []

    def load_local_config(environment: str) -> dict[str, Any]:
        return load_config(environment, config_dir=tmp_path)

    def record_pipeline_call(
        loaded_config: dict[str, Any],
    ) -> dict[str, Any]:
        loaded_configs.append(loaded_config)
        return {
            "run_id": "run123",
            "environment": "test",
            "status": "failed",
            "snapshots_written": 0,
            "rows_loaded": 0,
        }

    monkeypatch.setattr(
        sys,
        "argv",
        ["forecast-ops", "--environment", "test"],
    )
    monkeypatch.setattr(
        "forecast_ops.cli.load_config",
        load_local_config,
    )
    monkeypatch.setattr(
        "forecast_ops.cli.run_pipeline",
        record_pipeline_call,
    )
    monkeypatch.setattr(
        "forecast_ops.cli.configure_logging",
        lambda loaded_config: None,
    )

    main()

    assert len(loaded_configs) == 1
    assert "sst" not in loaded_configs[0]["locations"][0]
    assert loaded_configs[0]["locations"][1]["sst"]["coastal_regime"] == ""
