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


def test_main_exits_nonzero_after_failed_pipeline_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config: dict[str, Any] = {"logging": {"level": "INFO"}}
    result: dict[str, Any] = {
        "run_id": "run-failed",
        "status": "failed",
        "snapshots_written": 2,
        "rows_loaded": 24,
    }
    monkeypatch.setattr("saltbytes.cli.load_config", lambda: config)
    monkeypatch.setattr("saltbytes.cli.run_pipeline", lambda _: result)
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)

    with pytest.raises(SystemExit) as error:
        main([])

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "run id: run-failed" in output
    assert "status: failed" in output
    assert "snapshots written: 2" in output
    assert "rows loaded: 24" in output


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


def test_main_requires_explicit_report_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "saltbytes.cli.load_config",
        lambda: pytest.fail("configuration must not load"),
    )

    with pytest.raises(SystemExit) as error:
        main(["report"])

    assert error.value.code == 2


@pytest.mark.parametrize(
    ("report_type", "renderer_name"),
    (
        ("conditions", "render_conditions_report"),
        ("operations", "render_operations_report"),
    ),
)
def test_main_renders_explicit_text_report_without_running_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    report_type: str,
    renderer_name: str,
) -> None:
    config: dict[str, Any] = {"logging": {"level": "INFO"}}

    monkeypatch.setattr("saltbytes.cli.load_config", lambda: config)
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)
    monkeypatch.setattr(
        f"saltbytes.cli.{renderer_name}",
        lambda **kwargs: f"{report_type} {kwargs['run_id']} {kwargs['hours']}",
    )
    monkeypatch.setattr(
        "saltbytes.cli.run_pipeline",
        lambda _: pytest.fail("pipeline must not run while generating a report"),
    )

    main(
        [
            "report",
            report_type,
            "--run-id",
            "run123",
            "--hours",
            "12",
        ]
    )

    assert capsys.readouterr().out == f"{report_type} run123 12\n"


@pytest.mark.parametrize(
    ("report_type", "renderer_name"),
    (
        ("conditions", "render_conditions_html_report"),
        ("operations", "render_operations_html_report"),
    ),
)
def test_main_writes_explicit_html_report_without_running_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    report_type: str,
    renderer_name: str,
) -> None:
    config: dict[str, Any] = {"logging": {"level": "INFO"}}
    output_path = tmp_path / "report.html"

    monkeypatch.setattr("saltbytes.cli.load_config", lambda: config)
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)
    monkeypatch.setattr(
        f"saltbytes.cli.{renderer_name}",
        lambda **kwargs: (
            f"<html>{report_type} {kwargs['run_id']} {kwargs['hours']}</html>"
        ),
    )
    monkeypatch.setattr(
        "saltbytes.cli.run_pipeline",
        lambda _: pytest.fail("pipeline must not run while generating a report"),
    )

    main(
        [
            "report",
            report_type,
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

    assert output_path.read_text(encoding="utf-8") == (
        f"<html>{report_type} run123 12</html>"
    )


def test_main_requires_output_for_html_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "saltbytes.cli.load_config",
        lambda: {"logging": {"level": "INFO"}},
    )
    monkeypatch.setattr("saltbytes.cli.configure_logging", lambda _: None)

    with pytest.raises(ValueError, match="--output is required"):
        main(["report", "conditions", "--format", "html"])


def test_observation_command_uses_explicit_database_without_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "observations.duckdb"
    monkeypatch.setattr(
        "saltbytes.cli.load_config",
        lambda: pytest.fail("explicit observation database must not load configuration"),
    )
    monkeypatch.setattr(
        "saltbytes.cli.run_pipeline",
        lambda _: pytest.fail("observation ingestion must not run the pipeline"),
    )
    monkeypatch.setattr(
        "saltbytes.cli.retrieve_and_record_jennettes_pier_attempt",
        lambda path: {
            "reports": 2,
            "assertions": 3,
            "review_candidates": 1,
            "new_review_patterns": 1,
            "previously_seen_review_patterns": 0,
            "outstanding_review_patterns": 1,
        },
    )

    main(["observations", "ingest-jennettes", "--database", str(database_path)])

    assert capsys.readouterr().out == (
        "reports persisted: 2\n"
        "assertions persisted: 3\n"
        "review candidates persisted: 1\n"
        "new review patterns: 1\n"
        "previously seen review patterns: 0\n"
        "outstanding review patterns: 1\n"
    )


def test_observation_review_command_uses_explicit_database_without_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "saltbytes.cli.load_config",
        lambda: pytest.fail("explicit observation database must not load configuration"),
    )
    monkeypatch.setattr(
        "saltbytes.cli.review_observation_candidates",
        lambda *_: {
            "outstanding_patterns": 1,
            "patterns": [
                {
                    "pattern_id": "pattern123",
                    "source": "jennettes_pier",
                    "reason": "fishing terminology",
                    "raw_segment": "Anglers were nearby.",
                    "occurrence_count": 1,
                    "occurrences": [
                        {
                            "report_id": "report123",
                            "content_hash": "content123",
                            "report_time_text": "DATE",
                        }
                    ],
                }
            ],
        },
    )

    main(["observations", "review-candidates", "--database", str(tmp_path / "db")])

    assert "outstanding review patterns: 1" in capsys.readouterr().out


def test_observation_command_reports_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "saltbytes.cli.retrieve_and_record_jennettes_pier_attempt",
        lambda _: (_ for _ in ()).throw(ValueError("report entries missing")),
    )

    with pytest.raises(SystemExit, match="Jennette's Pier observation ingestion failed"):
        main(["observations", "ingest-jennettes", "--database", str(tmp_path / "db")])


def test_current_observation_command_reports_each_source_and_fails_after_isolation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "saltbytes.cli.retrieve_and_record_observation_attempts",
        lambda _: {
            "jennettes_pier": {
                "status": "success",
                "reports": 1,
                "assertions": 2,
                "review_candidates": 0,
            },
            "sunset_beach_pier": {
                "status": "failed",
                "error": "untrusted page shape changed",
            },
        },
    )

    with pytest.raises(
        SystemExit,
        match="completed with source failures: Sunset Beach Pier",
    ):
        main(
            [
                "observations",
                "ingest-current",
                "--database",
                str(tmp_path / "db"),
            ]
        )

    captured = capsys.readouterr()
    assert "Jennette's Pier status: completed" in captured.out
    assert (
        "Sunset Beach Pier status: failed: untrusted page shape changed"
        in captured.err
    )


def test_current_observation_command_bounds_failure_reason(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "saltbytes.cli.retrieve_and_record_observation_attempts",
        lambda _: {
            "jennettes_pier": {"status": "failed", "error": "bad\n" + "x" * 400},
            "sunset_beach_pier": {"status": "failed", "error": "timed out"},
        },
    )

    with pytest.raises(SystemExit):
        main(
            [
                "observations",
                "ingest-current",
                "--database",
                str(tmp_path / "db"),
            ]
        )

    error_lines = capsys.readouterr().err.splitlines()
    assert len(error_lines) == 2
    assert error_lines[0].startswith("Jennette's Pier status: failed: bad x")
    assert error_lines[0].endswith("…")
    assert len(error_lines[0]) < 300
    assert error_lines[1] == "Sunset Beach Pier status: failed: timed out"
