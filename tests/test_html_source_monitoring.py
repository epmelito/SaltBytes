from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

from saltbytes.database import initialize_database
from saltbytes.html_source_monitoring import render_source_monitoring_section


def test_source_monitoring_reports_rates_failures_and_missing_coverage(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs values
                ('run-old', timestamptz '2026-08-01 00:00:00+00',
                    timestamptz '2026-08-01 00:01:00+00',
                    'failed', 0, null),
                ('run-new', timestamptz '2026-08-01 06:00:00+00',
                    timestamptz '2026-08-01 06:01:00+00',
                    'success', 1, null);

            insert into source_results values
                ('run-new', 'coast-a', 'weather', 'success', null,
                    timestamptz '2026-08-01 06:00:10+00'),
                ('run-new', 'coast-a', 'wave', 'fetch_failed',
                    '<bad>wave</bad>',
                    timestamptz '2026-08-01 06:00:11+00'),
                ('run-new', 'coast-a', 'sst', 'success', null,
                    timestamptz '2026-08-01 06:00:12+00'),
                ('run-new', 'coast-b', 'weather', 'success', null,
                    timestamptz '2026-08-01 06:00:13+00'),
                ('run-new', 'coast-b', 'wave', 'success', null,
                    timestamptz '2026-08-01 06:00:14+00'),
                ('run-new', 'coast-b', 'sst', 'success', null,
                    timestamptz '2026-08-01 06:00:15+00'),
                ('run-new', 'coast-b', 'tide', 'success', null,
                    timestamptz '2026-08-01 06:00:16+00'),
                ('run-old', 'coast-a', 'weather', 'success', null,
                    timestamptz '2026-08-01 00:00:10+00'),
                ('run-old', 'coast-a', 'wave', 'success', null,
                    timestamptz '2026-08-01 00:00:11+00'),
                ('run-old', 'coast-a', 'tide', 'validation_failed', null,
                    timestamptz '2026-08-01 00:00:12+00'),
                ('run-new', 'not-selected', 'weather', 'fetch_failed',
                    'ignore me',
                    timestamptz '2026-08-01 06:00:20+00');
            """
        )
        connection.execute("set TimeZone = 'UTC'")
        section = render_source_monitoring_section(
            connection,
            [
                {"id": "coast-a", "name": "Coast <A>"},
                {"id": "coast-b", "name": "Coast B"},
            ],
            ZoneInfo("America/New_York"),
        )

    assert "Missing source results: 6 of 16 expected records." in section
    assert "Source success rates" in section
    assert "weather: 75.0%" in section
    assert "wave: 50.0%" in section
    assert "sst: 50.0%" in section
    assert "tide: 25.0%" in section
    assert "<td>weather</td><td>3</td><td>0</td><td>1</td><td>75.0%</td>" in section
    assert "<td>wave</td><td>2</td><td>1</td><td>1</td><td>50.0%</td>" in section
    assert "<td>sst</td><td>2</td><td>0</td><td>2</td><td>50.0%</td>" in section
    assert "<td>tide</td><td>1</td><td>1</td><td>2</td><td>25.0%</td>" in section
    assert section.count('data-source-run="') == 4
    assert "Coast &lt;A&gt;" in section
    assert "not recorded" in section
    assert "fetch_failed" in section
    assert "validation_failed" in section
    assert "&lt;bad&gt;wave&lt;/bad&gt;" in section
    assert "2026-08-01 02:00 EDT" in section
    assert "not-selected" not in section
    assert "ignore me" not in section


def test_source_monitoring_handles_empty_history(tmp_path: Path) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("set TimeZone = 'UTC'")
        section = render_source_monitoring_section(
            connection,
            [{"id": "coast-a", "name": "Coast A"}],
            ZoneInfo("America/New_York"),
        )

    assert "Missing source results: 0 of 0 expected records." in section
    assert "No pipeline runs recorded." in section
    assert "No recent source failures." in section
    assert "Source success rates: Unavailable." in section
    assert section.count("Unavailable") == 5
