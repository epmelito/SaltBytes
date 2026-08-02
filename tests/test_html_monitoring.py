from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

from saltbytes.database import initialize_database
from saltbytes.reporting.monitoring import render_monitoring_section


def test_monitoring_uses_recent_twenty_runs_and_preserves_status(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with duckdb.connect(str(database_path)) as connection:
        for index in range(21):
            status = "success" if index == 0 else "failed"
            rows_loaded = 5 if index == 20 else 0
            connection.execute(
                """
                insert into pipeline_runs values (
                    ?,
                    timestamptz '2026-08-01 00:00:00+00'
                        + ? * interval '1 hour',
                    timestamptz '2026-08-01 00:01:00+00'
                        + ? * interval '1 hour',
                    ?,
                    ?,
                    null
                )
                """,
                [f"run-{index:02d}", index, index, status, rows_loaded],
            )

        connection.execute(
            """
            insert into forecast_snapshots (
                snapshot_id,
                run_id,
                location_id,
                captured_at,
                raw_file_path
            ) values (
                'snapshot-20',
                'run-20',
                'test-coast',
                timestamptz '2026-08-01 20:00:00+00',
                'raw/snapshot-20.json'
            )
            """
        )
        connection.execute("set TimeZone = 'UTC'")
        section = render_monitoring_section(
            connection,
            datetime(2026, 8, 2, 0, 1, tzinfo=timezone.utc),
            ZoneInfo("America/New_York"),
        )

    assert section.count('data-run-id="') == 20
    assert 'data-run-id="run-20"' in section
    assert 'data-run-id="run-00"' not in section
    assert "run-00 at 2026-07-31 20:01 EDT" in section
    assert "Elapsed since latest success</dt><dd>1d 0h 0m" in section
    assert "Consecutive failed runs</dt><dd>20" in section
    assert "Recent successful runs</dt><dd>0" in section
    assert "Recent failed runs</dt><dd>20" in section
    assert "Displayed runs</dt><dd>20" in section
    assert "Recent run status timeline" in section
    assert section.count('data-status-marker="') == 20
    assert "Recent run duration" in section
    assert "Rows loaded by run" in section
    assert "60.0 seconds" in section
    assert "5.0 rows" in section
    assert "run-20" in section
    assert "failed" in section
    assert "60 s" in section
    assert "<td>5</td><td>1</td><td>partial data</td>" in section


def test_monitoring_charts_show_unavailable_without_runs(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("set TimeZone = 'UTC'")
        section = render_monitoring_section(
            connection,
            datetime(2026, 8, 2, 0, 1, tzinfo=timezone.utc),
            ZoneInfo("America/New_York"),
        )

    assert "Recent run status timeline: Unavailable." in section
    assert "Recent run duration: Unavailable." in section
    assert "Rows loaded by run: Unavailable." in section
    assert "No pipeline runs recorded." in section
