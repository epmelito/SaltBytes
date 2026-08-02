from pathlib import Path
from typing import Any

import pytest

from saltbytes.cli import main


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
    monkeypatch.setattr("saltbytes.cli.load_config", lambda: config)
    monkeypatch.setattr("saltbytes.cli.run_pipeline", lambda _: result)
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)

    main([])

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

    monkeypatch.setattr("saltbytes.cli.load_config", reject_config)
    monkeypatch.setattr("saltbytes.cli.run_pipeline", record_pipeline_call)

    with pytest.raises(ValueError, match=r"locations\[0\].sst"):
        main([])

    assert pipeline_called is False


def test_main_renders_report_without_running_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config: dict[str, Any] = {"logging": {"level": "INFO"}}
    pipeline_called = False

    def record_pipeline_call(_: dict[str, Any]) -> dict[str, Any]:
        nonlocal pipeline_called
        pipeline_called = True
        return {}

    monkeypatch.setattr("saltbytes.cli.load_config", lambda: config)
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)
    monkeypatch.setattr(
        "saltbytes.cli.render_report",
        lambda **kwargs: f"report for {kwargs['run_id']} {kwargs['hours']}",
    )
    monkeypatch.setattr("saltbytes.cli.run_pipeline", record_pipeline_call)

    main(["report", "--run-id", "run123", "--hours", "12"])

    assert capsys.readouterr().out == "report for run123 12\n"
    assert pipeline_called is False


def test_main_writes_html_report_without_running_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config: dict[str, Any] = {"logging": {"level": "INFO"}}
    output_path = tmp_path / "report.html"

    monkeypatch.setattr("saltbytes.cli.load_config", lambda: config)
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)
    monkeypatch.setattr(
        "saltbytes.cli.render_html_report",
        lambda **kwargs: f"<html>{kwargs['run_id']} {kwargs['hours']}</html>",
    )
    monkeypatch.setattr(
        "saltbytes.cli.run_pipeline",
        lambda _: pytest.fail("pipeline must not run while generating a report"),
    )

    main(
        [
            "report",
            "--format",
            "html",
            "--output",
            str(output_path),
            "--run-id",
            "run123",
            "--hours",
            "12",
        ]
    )

    assert output_path.read_text(encoding="utf-8") == "<html>run123 12</html>"


def test_main_requires_output_for_html_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "saltbytes.cli.load_config",
        lambda: {"logging": {"level": "INFO"}},
    )
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)

    with pytest.raises(ValueError, match="--output is required"):
        main(["report", "--format", "html"])
