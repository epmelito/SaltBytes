from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import duckdb
import pytest

from saltbytes.database import initialize_database
from saltbytes.reporting.html import (
    _line_chart_html,
    render_conditions_html_report,
    render_operations_html_report,
)
from saltbytes.reporting.presentation import kilometers_per_hour_to_miles_per_hour


def _config(database_path: Path) -> dict[str, Any]:
    return {
        "display_timezone": "America/New_York",
        "storage": {"database_path": str(database_path)},
        "locations": [
            {
                "id": "test_coast",
                "name": "<Test Coast>",
                "fishing_context": "surf & pier",
            },
            {
                "id": "other_coast",
                "name": "Other Coast",
                "fishing_context": "surf",
            },
        ],
    }


def _insert_run(database_path: Path) -> None:
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs values
            (
                'run-0',
                timestamptz '2026-08-01 06:00:00+00',
                timestamptz '2026-08-01 06:01:00+00',
                'success',
                3,
                null
            ),
            (
                'run-1',
                timestamptz '2026-08-01 12:00:00+00',
                timestamptz '2026-08-01 12:01:00+00',
                'failed',
                3,
                'partial source failure'
            );
            insert into run_locations values (
                'run-1',
                'test_coast',
                'surf',
                90,
                null,
                'reviewed method',
                'reviewed source',
                date '2026-08-01',
                'review limitation'
            );
            insert into forecast_snapshots (
                snapshot_id, run_id, location_id, captured_at, raw_file_path
            ) values
                ('weather-0', 'run-0', 'test_coast',
                    timestamptz '2026-08-01 06:00:00+00', 'raw/weather-0.json'),
                ('wave-0', 'run-0', 'test_coast',
                    timestamptz '2026-08-01 06:00:00+00', 'raw/wave-0.json'),
                ('sst-0', 'run-0', 'test_coast',
                    timestamptz '2026-08-01 06:00:00+00', 'raw/sst-0.json'),
                ('weather-0-other', 'run-0', 'unconfigured_coast',
                    timestamptz '2026-08-01 06:00:00+00', 'raw/other-0.json'),
                ('weather-1-other', 'run-1', 'unconfigured_coast',
                    timestamptz '2026-08-01 12:00:00+00', 'raw/other-1.json'),
                ('weather-1', 'run-1', 'test_coast',
                    timestamptz '2026-08-01 12:00:00+00', 'raw/weather.json'),
                ('wave-1', 'run-1', 'test_coast',
                    timestamptz '2026-08-01 12:00:00+00', 'raw/wave.json'),
                ('sst-1', 'run-1', 'test_coast',
                    timestamptz '2026-08-01 12:00:00+00', 'raw/sst.json'),
                ('tide-1', 'run-1', 'test_coast',
                    timestamptz '2026-08-01 12:00:00+00', 'raw/tide.json');
            insert into forecast_hourly (
                snapshot_id,
                location_id,
                forecast_time,
                precipitation_probability,
                wind_speed_10m,
                wind_direction_10m,
                wind_gusts_10m,
                precipitation
            ) values
                ('weather-0', 'test_coast',
                    timestamptz '2026-08-01 13:00:00+00', 20, 16.0, 115, 24.0, 0.0),
                ('weather-0', 'test_coast',
                    timestamptz '2026-08-01 14:00:00+00', 20, 999.0, 115, 24.0, 0.0),
                ('weather-1', 'test_coast',
                    timestamptz '2026-08-01 13:00:00+00', 25, 18.5, 120, 27.0, null),
                ('weather-1', 'test_coast',
                    timestamptz '2026-08-01 14:00:00+00', 30, 88.8, 130, 90.0, 0.5),
                ('weather-0-other', 'unconfigured_coast',
                    timestamptz '2026-08-01 13:00:00+00', 0, 777.0, 0, 0, 0),
                ('weather-1-other', 'unconfigured_coast',
                    timestamptz '2026-08-01 13:00:00+00', 0, 778.0, 0, 0, 0);
            insert into wave_hourly values
                ('wave-0', 'test_coast',
                    timestamptz '2026-08-01 13:00:00+00', 1.0, 105, 7.5),
                ('wave-1', 'test_coast',
                    timestamptz '2026-08-01 13:00:00+00', 1.2, 110, 8.0),
                ('wave-1', 'test_coast',
                    timestamptz '2026-08-01 14:00:00+00', 1.4, 115, 8.5);
            insert into sst_hourly values
                ('sst-0', 'test_coast',
                    timestamptz '2026-08-01 13:00:00+00', 24.0),
                ('sst-1', 'test_coast',
                    timestamptz '2026-08-01 13:00:00+00', 24.6),
                ('sst-1', 'test_coast',
                    timestamptz '2026-08-01 14:00:00+00', 24.8);
            insert into tide_snapshots (
                snapshot_id,
                station_id,
                prediction_location,
                relationship_type,
                product,
                interval,
                datum,
                time_zone,
                units,
                response_format,
                request_begin_date,
                request_end_date,
                distance_km,
                coastal_relationship,
                known_limitation
            ) values (
                'tide-1',
                'station-1',
                'Test Coast',
                'direct',
                'predictions',
                'hilo',
                'MLLW',
                'gmt',
                'metric',
                'json',
                date '2026-07-31',
                date '2026-08-09',
                1.0,
                'direct relationship',
                'prediction limitation'
            );
            insert into tide_events values
                ('tide-1', 'test_coast',
                    timestamptz '2026-08-01 12:30:00+00', 'low', 0.2),
                ('tide-1', 'test_coast',
                    timestamptz '2026-08-01 18:30:00+00', 'high', 1.4);
            insert into tide_phase_hourly values (
                'tide-1',
                'test_coast',
                timestamptz '2026-08-01 13:00:00+00',
                'rising'
            );
            insert into source_results values
                ('run-1', 'test_coast', 'weather', 'success', null,
                    timestamptz '2026-08-01 12:00:00+00'),
                ('run-1', 'test_coast', 'wave', 'success', null,
                    timestamptz '2026-08-01 12:00:00+00'),
                ('run-1', 'test_coast', 'sst', 'success', null,
                    timestamptz '2026-08-01 12:00:00+00'),
                ('run-1', 'test_coast', 'tide', 'success', null,
                    timestamptz '2026-08-01 12:00:00+00'),
                ('run-1', 'other_coast', 'wave', 'fetch_failed',
                    '<script>wave failed</script>',
                    timestamptz '2026-08-01 12:00:00+00');
            """
        )


def test_render_conditions_html_report_shows_forecast_output(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    _insert_run(database_path)

    report = render_conditions_html_report(
        _config(database_path),
        location_id="test_coast",
    )

    assert report.startswith("<!doctype html>")
    assert "<title>SaltBytes coastal conditions</title>" in report
    assert "run-1" in report
    assert "failed" in report
    assert "2026-08-01 08:00 EDT" in report
    assert "2026-08-01 08:01 EDT" in report
    assert "2026-08-01 09:00 EDT" in report
    assert "&lt;Test Coast&gt;" in report
    assert "surf &amp; pier" in report
    assert "11.5 mph" in report
    assert "16.8 mph" in report
    assert "120 degrees" in report
    assert "30 degrees" in report
    assert "3.9 ft" in report
    assert "110 degrees" in report
    assert "20 degrees" in report
    assert "8.0 s" in report
    assert "76 °F" in report
    assert 'y="24">78 °F</text>' in report
    assert 'y="150">75 °F</text>' in report
    assert "78.0 °F" not in report
    assert "75.3 °F" not in report
    assert "rising" in report
    assert "low at 2026-08-01 08:30 EDT (0.7 ft)" in report
    assert "high at 2026-08-01 14:30 EDT (4.6 ft)" in report
    assert "90 degrees" in report
    assert "<dt>Precipitation</dt><dd>Unavailable</dd>" in report
    assert "88.8 mph" not in report
    assert "Wind speed and gust trend" in report
    assert "Wave height trend" in report
    assert "Sea surface temperature trend" in report
    assert "Tide phase and adjacent extrema" in report
    assert "Wind and wave angle to shore trend" in report
    assert "Angle reference: 0 degrees is directly onshore" in report
    assert 'class="reference"' in report
    assert report.count("<svg") == 5
    assert 'id="revisions"' not in report
    assert 'id="monitoring"' not in report
    assert 'id="source-monitoring"' not in report
    assert 'id="sources"' not in report
    assert 'id="provenance"' not in report
    assert "reviewed method" not in report
    assert "weather-1" not in report
    assert "Other Coast" not in report
    assert "https://" not in report


def test_render_operations_html_report_shows_pipeline_output(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    _insert_run(database_path)

    report = render_operations_html_report(
        _config(database_path),
        location_id="test_coast",
    )

    assert report.startswith("<!doctype html>")
    assert "<title>SaltBytes pipeline operations</title>" in report
    assert "run-1" in report
    assert "failed" in report
    assert "Rows loaded" in report
    assert "Time since completion" in report
    assert "Generated" in report
    assert 'href="#revisions"' in report
    assert 'id="revisions"' in report
    assert 'href="#monitoring"' in report
    assert 'id="monitoring"' in report
    assert 'href="#source-monitoring"' in report
    assert 'id="source-monitoring"' in report
    assert 'href="#sources"' in report
    assert 'id="sources"' in report
    assert 'href="#provenance"' in report
    assert 'id="provenance"' in report
    assert "reviewed method" in report
    assert "reviewed source" in report
    assert "review limitation" in report
    assert "weather-1" in report
    assert "wave-1" in report
    assert "sst-1" in report
    assert "tide-1" in report
    assert "raw/weather.json" not in report
    assert "Forecast valid time:</strong> 2026-08-01 09:00 EDT" in report
    assert "Pipeline run start time remains distinct" in report
    assert "2026-08-01 02:00 EDT" in report
    assert "9.9 mph" in report
    assert "11.5 mph" in report
    assert "3.3 ft" in report
    assert "75 °F" in report
    assert "999.0 mph" not in report
    assert "777.0 mph" not in report
    assert "778.0 mph" not in report
    assert report.count("<svg") == 4
    assert 'id="conditions"' not in report
    assert 'id="condition-trends"' not in report
    assert "Wind speed and gust trend" not in report
    assert "Other Coast" not in report
    assert "https://" not in report


def test_render_operations_html_report_escapes_stored_failure_detail(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    _insert_run(database_path)

    report = render_operations_html_report(_config(database_path))

    assert "<script>" not in report
    assert "&lt;script&gt;wave failed&lt;/script&gt;" in report


def test_render_conditions_html_report_marks_missing_location_data(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)
    _insert_run(database_path)

    report = render_conditions_html_report(_config(database_path))

    assert "No integrated forecast hour" in report
    assert "Wind speed and gust trend: Unavailable" in report
    assert "Wave height trend: Unavailable" in report
    assert "Sea surface temperature trend: Unavailable" in report
    assert "Tide phase and adjacent extrema: Unavailable" in report
    assert "Wind and wave angle to shore trend: Unavailable" in report


@pytest.mark.parametrize(
    "renderer",
    (
        render_conditions_html_report,
        render_operations_html_report,
    ),
)
def test_html_reports_reject_invalid_selection_and_database(
    tmp_path: Path,
    renderer: Any,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with pytest.raises(ValueError, match="no pipeline run found"):
        renderer(_config(database_path))

    with pytest.raises(ValueError, match="unknown location"):
        renderer(_config(database_path), location_id="missing")

    with pytest.raises(ValueError, match="hours must be greater than zero"):
        renderer(_config(database_path), hours=0)

    with pytest.raises(ValueError, match="database does not exist"):
        renderer(_config(tmp_path / "missing.duckdb"))


def test_render_operations_html_report_shows_insufficient_revision_history(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "saltbytes.duckdb"
    initialize_database(database_path)

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            insert into pipeline_runs values (
                'run-only',
                timestamptz '2026-08-01 12:00:00+00',
                timestamptz '2026-08-01 12:01:00+00',
                'success',
                1,
                null
            );
            insert into forecast_snapshots (
                snapshot_id, run_id, location_id, captured_at, raw_file_path
            ) values (
                'weather-only',
                'run-only',
                'test_coast',
                timestamptz '2026-08-01 12:00:00+00',
                'raw/weather-only.json'
            );
            insert into forecast_hourly (
                snapshot_id, location_id, forecast_time, wind_speed_10m
            ) values (
                'weather-only',
                'test_coast',
                timestamptz '2026-08-01 13:00:00+00',
                18.5
            );
            """
        )

    report = render_operations_html_report(
        _config(database_path),
        location_id="test_coast",
    )

    assert "Insufficient persisted history" in report


def test_line_chart_marks_missing_series_unavailable() -> None:
    chart = _line_chart_html(
        "Wind speed and gust trend",
        [
            (
                "test_coast",
                datetime(2026, 8, 1, 13, tzinfo=timezone.utc),
                18.5,
                None,
            ),
            (
                "test_coast",
                datetime(2026, 8, 1, 14, tzinfo=timezone.utc),
                20.0,
                None,
            ),
        ],
        (("Wind speed", 2), ("Gust", 3)),
        "mph",
        ZoneInfo("America/New_York"),
        convert=kilometers_per_hour_to_miles_per_hour,
    )

    assert "<svg" in chart
    assert "Wind speed (solid)" in chart
    assert "Gust (Unavailable)" in chart
