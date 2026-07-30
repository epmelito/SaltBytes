from typing import Any

import pytest

from forecast_ops.cli import main


def test_main_runs_local_configuration(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config: dict[str, Any] = {"logging": {"level": "INFO"}}
    result: dict[str, Any] = {
        "run_id": "run123",
        "status": "success",
        "snapshots_written": 2,
        "rows_loaded": 96,
    }
    monkeypatch.setattr("forecast_ops.cli.load_config", lambda: config)
    monkeypatch.setattr("forecast_ops.cli.run_pipeline", lambda _: result)
    monkeypatch.setattr("forecast_ops.cli.configure_logging", lambda _: None)

    main()

    output = capsys.readouterr().out
    assert "run id: run123" in output
    assert "environment" not in output
    assert "status: success" in output
    assert "snapshots written: 2" in output
    assert "rows loaded: 96" in output


def test_main_rejects_invalid_configuration_before_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_called = False

    def reject_config() -> dict[str, Any]:
        raise ValueError("locations[0].sst must be a mapping")

    def record_pipeline_call(config: dict[str, Any]) -> dict[str, Any]:
        nonlocal pipeline_called
        pipeline_called = True
        return {}

    monkeypatch.setattr("forecast_ops.cli.load_config", reject_config)
    monkeypatch.setattr("forecast_ops.cli.run_pipeline", record_pipeline_call)

    with pytest.raises(ValueError, match=r"locations\[0\].sst"):
        main()

    assert pipeline_called is False
