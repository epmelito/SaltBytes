import sys
from typing import Any

import pytest

from forecast_ops.cli import main, parse_args


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
