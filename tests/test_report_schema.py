from pathlib import Path
from typing import Any

import duckdb
import pytest

from saltbytes.cli import main
from saltbytes.database import initialize_database
from saltbytes.reporting.html import render_html_report
from saltbytes.reporting.schema import ReportSchemaError


def _config(database_path: Path) -> dict[str, Any]:
    return {
        "display_timezone": "America/New_York",
        "storage": {
            "database_path": str(database_path),
        },
        "locations": [
            {
                "id": "test_coast",
                "name": "Test Coast",
                "fishing_context": "surf",
            }
        ],
    }


def test_render_html_report_rejects_outdated_schema(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with duckdb.connect(
        str(database_path)
    ) as connection:
        connection.execute(
            """
            create table legacy_conditions as
            select * exclude (
                shore_normal_azimuth_degrees,
                wind_to_shore_angle_degrees,
                wave_to_shore_angle_degrees
            )
            from coastal_conditions_hourly
            limit 0
            """
        )
        connection.execute(
            "drop view coastal_conditions_hourly"
        )
        connection.execute(
            "alter table legacy_conditions "
            "rename to coastal_conditions_hourly"
        )
        connection.execute(
            "drop table run_locations"
        )

    with pytest.raises(
        ReportSchemaError
    ) as error:
        render_html_report(
            _config(database_path)
        )

    assert str(error.value) == (
        "HTML reporting requires a current "
        "SaltBytes database schema.\n"
        "Missing: run_locations, "
        "coastal_conditions_hourly."
        "shore_normal_azimuth_degrees, "
        "coastal_conditions_hourly."
        "wind_to_shore_angle_degrees, "
        "coastal_conditions_hourly."
        "wave_to_shore_angle_degrees\n"
        "Run ingestion with the current code or "
        "restore a current database before retrying."
    )


def test_main_reports_outdated_schema_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "report.html"
    message = (
        "HTML reporting requires a current "
        "SaltBytes database schema.\n"
        "Missing: run_locations\n"
        "Run ingestion with the current code or "
        "restore a current database before retrying."
    )

    monkeypatch.setattr(
        "saltbytes.cli.load_config",
        lambda: {"logging": {"level": "INFO"}},
    )
    monkeypatch.setattr(
        "saltbytes.cli.configure_logging",
        lambda _: None,
    )

    def reject_schema(**_: Any) -> str:
        raise ReportSchemaError(message)

    monkeypatch.setattr(
        "saltbytes.cli.render_html_report",
        reject_schema,
    )

    with pytest.raises(SystemExit) as error:
        main(
            [
                "report",
                "--format",
                "html",
                "--output",
                str(output_path),
            ]
        )

    assert str(error.value) == f"error: {message}"
    assert not output_path.exists()
