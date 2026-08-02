from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import duckdb

from saltbytes.report import _select_run
from saltbytes.reporting.monitoring import render_monitoring_section
from saltbytes.reporting.provenance import render_provenance_section
from saltbytes.reporting.revisions import render_revision_section
from saltbytes.reporting.schema import validate_report_schema
from saltbytes.reporting.source_monitoring import render_source_monitoring_section

_SOURCES = ("weather", "wave", "sst", "tide")


def _text(value: object | None) -> str:
    return "Unavailable" if value is None else escape(str(value))


def _time(value: datetime | None, display_timezone: ZoneInfo) -> str:
    if value is None:
        return "Unavailable"
    return value.astimezone(display_timezone).strftime("%Y-%m-%d %H:%M %Z")


def _elapsed(value: datetime | None, generated_at: datetime) -> str:
    if value is None:
        return "Unavailable"

    minutes = max(int((generated_at - value).total_seconds() // 60), 0)
    days, remaining_minutes = divmod(minutes, 24 * 60)
    hours, remaining_minutes = divmod(remaining_minutes, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{remaining_minutes}m")
    return " ".join(parts)


def _number(
    value: float | None,
    unit: str = "",
    precision: int = 1,
) -> str:
    if value is None:
        return "Unavailable"

    suffix = f" {unit}" if unit else ""
    return f"{value:.{precision}f}{suffix}"


def _extremum(
    extremum_type: str | None,
    extremum_time: datetime | None,
    predicted_level: float | None,
    display_timezone: ZoneInfo,
) -> str:
    if extremum_type is None and extremum_time is None and predicted_level is None:
        return "Unavailable"

    return (
        f"{_text(extremum_type)} at {_time(extremum_time, display_timezone)} "
        f"({_number(predicted_level, 'm')})"
    )


def _line_chart_html(
    title: str,
    rows: list[tuple[Any, ...]],
    series: tuple[tuple[str, int], ...],
    unit: str,
    display_timezone: ZoneInfo,
    fixed_minimum: float | None = None,
    fixed_maximum: float | None = None,
    reference_value: float | None = None,
) -> str:
    values = [
        float(row[column])
        for row in rows
        for _, column in series
        if row[column] is not None
    ]
    if not values:
        return (
            f'<div class="chart"><h4>{_text(title)}</h4>'
            f'<p>{_text(title)}: Unavailable in the selected window.</p></div>'
        )

    width, height = 640, 190
    left, right, top, bottom = 52, 16, 20, 40
    plot_width = width - left - right
    plot_height = height - top - bottom
    minimum = min(values)
    maximum = max(values)
    if fixed_minimum is not None and fixed_maximum is not None:
        lower = fixed_minimum
        upper = fixed_maximum
    else:
        padding = max((maximum - minimum) * 0.1, 1.0)
        lower = minimum - padding
        upper = maximum + padding
    start_time = rows[0][1]
    end_time = rows[-1][1]
    time_span = max((end_time - start_time).total_seconds(), 1.0)

    def x_position(value: datetime) -> float:
        elapsed = (value - start_time).total_seconds()
        return left + (elapsed / time_span) * plot_width

    def y_position(value: float) -> float:
        return top + ((upper - value) / (upper - lower)) * plot_height

    reference_line = ""
    if reference_value is not None and lower <= reference_value <= upper:
        reference_y = y_position(reference_value)
        reference_line = (
            f'<line class="reference" x1="{left}" y1="{reference_y:.1f}" '
            f'x2="{width - right}" y2="{reference_y:.1f}" />'
        )

    lines = []
    legend = []
    for series_index, (label, column) in enumerate(series):
        segments: list[list[str]] = []
        segment: list[str] = []
        for row in rows:
            value = row[column]
            if value is None:
                if segment:
                    segments.append(segment)
                    segment = []
                continue
            segment.append(
                f"{x_position(row[1]):.1f},{y_position(float(value)):.1f}"
            )
        if segment:
            segments.append(segment)

        if not segments:
            legend.append(f'<span>{_text(label)} (Unavailable)</span>')
            continue

        dash = ' stroke-dasharray="8 5"' if series_index else ""
        for points in segments:
            if len(points) == 1:
                x_value, y_value = points[0].split(",")
                lines.append(
                    f'<circle cx="{x_value}" cy="{y_value}" r="3" />'
                )
            else:
                lines.append(
                    f'<polyline points="{" ".join(points)}"{dash} />'
                )
        style = "dashed" if series_index else "solid"
        legend.append(f'<span>{_text(label)} ({style})</span>')

    return (
        f'<div class="chart"><h4>{_text(title)}</h4>'
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{_text(title)}">'
        f'<title>{_text(title)}</title>'
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" />'
        f'<line class="axis" x1="{left}" y1="{height - bottom}" '
        f'x2="{width - right}" y2="{height - bottom}" />'
        f'{reference_line}'
        f'<text x="4" y="{top + 4}">{upper:.1f} {_text(unit)}</text>'
        f'<text x="4" y="{height - bottom}">{lower:.1f} {_text(unit)}</text>'
        f'<text x="{left}" y="{height - 10}">{_time(start_time, display_timezone)}</text>'
        f'<text x="{width - right}" y="{height - 10}" text-anchor="end">'
        f'{_time(end_time, display_timezone)}</text>'
        f'{"".join(lines)}</svg>'
        f'<p class="legend">{" · ".join(legend)}</p></div>'
    )


def _tide_context_chart_html(
    rows: list[tuple[Any, ...]],
    display_timezone: ZoneInfo,
) -> str:
    title = "Tide phase and adjacent extrema"
    pairs: dict[tuple[datetime, datetime], tuple[Any, ...]] = {}

    for row in rows:
        phase = row[8]
        previous_time = row[9]
        previous_type = row[10]
        previous_level = row[11]
        next_time = row[12]
        next_type = row[13]
        next_level = row[14]
        if (
            previous_time is None
            or previous_type is None
            or next_time is None
            or next_type is None
        ):
            continue
        pairs[(previous_time, next_time)] = (
            phase,
            previous_time,
            previous_type,
            previous_level,
            next_time,
            next_type,
            next_level,
        )

    if not pairs:
        return (
            f'<div class="chart"><h4>{title}</h4>'
            f'<p>{title}: Unavailable in the selected window.</p></div>'
        )

    ordered_pairs = sorted(pairs.values(), key=lambda pair: pair[1])
    start_time = min(pair[1] for pair in ordered_pairs)
    end_time = max(pair[4] for pair in ordered_pairs)
    time_span = max((end_time - start_time).total_seconds(), 1.0)
    width, height = 640, 170
    left, right = 52, 16
    plot_width = width - left - right

    def x_position(value: datetime) -> float:
        elapsed = (value - start_time).total_seconds()
        return left + (elapsed / time_span) * plot_width

    timeline_y = 78.0
    segments = []
    events: dict[tuple[datetime, str], float | None] = {}
    for (
        phase,
        previous_time,
        previous_type,
        previous_level,
        next_time,
        next_type,
        next_level,
    ) in ordered_pairs:
        previous_x = x_position(previous_time)
        next_x = x_position(next_time)
        midpoint_x = (previous_x + next_x) / 2
        segments.append(
            f'<line class="tide-segment" x1="{previous_x:.1f}" '
            f'y1="{timeline_y:.1f}" x2="{next_x:.1f}" y2="{timeline_y:.1f}" />'
            f'<text x="{midpoint_x:.1f}" y="{timeline_y - 10:.1f}" '
            f'text-anchor="middle">{_text(phase)}</text>'
        )
        events[(previous_time, previous_type)] = previous_level
        events[(next_time, next_type)] = next_level

    markers = []
    for (event_time, event_type), level in sorted(events.items()):
        event_x = x_position(event_time)
        label_y = 42.0 if event_type == "high" else 118.0
        markers.append(
            f'<circle cx="{event_x:.1f}" cy="{timeline_y:.1f}" r="4" />'
            f'<text x="{event_x:.1f}" y="{label_y:.1f}" text-anchor="middle">'
            f'{_text(event_type)} {_number(level, "m")}</text>'
        )

    return (
        f'<div class="chart"><h4>{title}</h4>'
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
        f'<title>{title}</title>{"".join(segments)}{"".join(markers)}'
        f'<text x="{left}" y="{height - 8}">{_time(start_time, display_timezone)}</text>'
        f'<text x="{width - right}" y="{height - 8}" text-anchor="end">'
        f'{_time(end_time, display_timezone)}</text></svg></div>'
    )


def _source_status_html(
    location_id: str,
    source_results: dict[str, dict[str, tuple[str, str | None]]],
) -> str:
    items = []

    for source in _SOURCES:
        status, detail = source_results.get(location_id, {}).get(
            source,
            ("not recorded", None),
        )
        detail_html = f" ({_text(detail)})" if detail else ""
        items.append(
            f"<li><strong>{source}</strong>: {_text(status)}{detail_html}</li>"
        )

    return f'<ul class="source-status">{"".join(items)}</ul>'


def _condition_summary_html(
    location: dict[str, Any],
    row: tuple[Any, ...] | None,
    display_timezone: ZoneInfo,
) -> str:
    location_id = escape(location["id"])
    heading = f"<h3>{_text(location['name'])}</h3>"

    if row is None:
        return (
            f'<article id="conditions-{location_id}">{heading}'
            "<p>No integrated forecast hour is available in the selected window.</p>"
            "</article>"
        )

    (
        _,
        forecast_time,
        shore_normal,
        wind_speed,
        wind_direction,
        wind_to_shore_angle,
        wind_gust,
        precipitation_probability,
        precipitation,
        wave_height,
        wave_direction,
        wave_to_shore_angle,
        wave_period,
        sea_surface_temperature,
        tide_phase,
        previous_extremum_time,
        previous_extremum_type,
        previous_predicted_level,
        next_extremum_time,
        next_extremum_type,
        next_predicted_level,
        predicted_tidal_range,
    ) = row

    metrics = (
        ("Wind speed", _number(wind_speed, "km/h")),
        ("Wind direction", _number(wind_direction, "degrees", 0)),
        ("Wind gust", _number(wind_gust, "km/h")),
        ("Precipitation probability", _number(precipitation_probability, "%", 0)),
        ("Precipitation", _number(precipitation, "mm")),
        ("Wave height", _number(wave_height, "m")),
        ("Incoming wave direction", _number(wave_direction, "degrees", 0)),
        ("Wave period", _number(wave_period, "s")),
        ("Sea surface temperature", _number(sea_surface_temperature, "°C")),
        ("Tide phase", _text(tide_phase)),
        (
            "Previous tide extremum",
            _extremum(
                previous_extremum_type,
                previous_extremum_time,
                previous_predicted_level,
                display_timezone,
            ),
        ),
        (
            "Next tide extremum",
            _extremum(
                next_extremum_type,
                next_extremum_time,
                next_predicted_level,
                display_timezone,
            ),
        ),
        ("Predicted tidal range", _number(predicted_tidal_range, "m")),
        ("Persisted shore normal", _number(shore_normal, "degrees", 0)),
        ("Wind to shore angle", _number(wind_to_shore_angle, "degrees", 0)),
        ("Wave to shore angle", _number(wave_to_shore_angle, "degrees", 0)),
    )
    metric_html = "".join(
        f"<div><dt>{label}</dt><dd>{value}</dd></div>" for label, value in metrics
    )

    return (
        f'<article id="conditions-{location_id}">{heading}'
        f"<p>{_text(location['fishing_context'])}</p>"
        f"<p><strong>First valid forecast hour:</strong> "
        f"{_time(forecast_time, display_timezone)}</p>"
        f'<dl class="summary">{metric_html}</dl></article>'
    )


_CSS = """
body { margin: 0 auto; max-width: 72rem; padding: 2rem; font-family: sans-serif; }
nav a { margin-right: 1rem; }
.summary { display: flex; flex-wrap: wrap; gap: 1rem; }
.summary div { min-width: 12rem; max-width: 24rem; }
article { border-top: 1px solid #bbb; margin-top: 1.5rem; padding-top: .5rem; }
dt { font-weight: 700; }
dd { margin: .25rem 0 0; }
.source-status { line-height: 1.6; }
.chart { margin: 1rem 0 2rem; }
.chart svg { display: block; max-width: 100%; }
.chart polyline, .chart circle { fill: none; stroke: currentColor; stroke-width: 2; }
.chart circle { fill: currentColor; }
.chart .axis, .chart .tide-segment, .chart .reference { stroke: currentColor; stroke-width: 1; }
.chart .reference { stroke-dasharray: 4 4; }
.chart text { font-size: 12px; }
.legend { display: flex; flex-wrap: wrap; gap: 1rem; }
.table-scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid #bbb; padding: .5rem; text-align: left; }
@media (max-width: 40rem) { body { padding: 1rem; } .summary div { min-width: 100%; } }
"""


def _report_inputs(
    config: dict[str, Any],
    hours: int,
    location_id: str | None,
) -> tuple[list[dict[str, Any]], Path, ZoneInfo, datetime]:
    if hours <= 0:
        raise ValueError("hours must be greater than zero")

    locations = config["locations"]
    locations_by_id = {location["id"]: location for location in locations}
    if location_id is not None and location_id not in locations_by_id:
        raise ValueError(f"unknown location: {location_id}")

    selected_locations = [locations_by_id[location_id]] if location_id else locations
    database_path = Path(config["storage"]["database_path"])
    if not database_path.is_file():
        raise ValueError(f"database does not exist: {database_path}")

    return (
        selected_locations,
        database_path,
        ZoneInfo(config["display_timezone"]),
        datetime.now(timezone.utc),
    )


def _forecast_window(
    connection: duckdb.DuckDBPyConnection,
    run_id: str,
    started_at: datetime,
    hours: int,
) -> tuple[datetime | None, datetime | None]:
    first_hour = connection.execute(
        """
        select min(forecast_time)
        from coastal_conditions_hourly
        where run_id = ? and forecast_time >= ?
        """,
        [run_id, started_at],
    ).fetchone()[0]
    window_end = first_hour + timedelta(hours=hours) if first_hour else None
    return first_hour, window_end


def _window_text(
    first_hour: datetime | None,
    window_end: datetime | None,
    display_timezone: ZoneInfo,
) -> str:
    if first_hour is None or window_end is None:
        return "No integrated forecast hours at or after the selected run start."

    final_hour = window_end - timedelta(hours=1)
    return (
        f"{_time(first_hour, display_timezone)} through "
        f"{_time(final_hour, display_timezone)}"
    )


def _page_html(
    title: str,
    introduction: str,
    navigation: tuple[tuple[str, str], ...],
    content: str,
) -> str:
    links = "".join(
        f'<a href="#{escape(target)}">{_text(label)}</a>'
        for target, label in navigation
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_text(title)}</title><style>{_CSS}</style></head><body>"
        f"<header><h1>{_text(title)}</h1><p>{_text(introduction)}</p>"
        f"<nav>{links}</nav></header><main>{content}</main></body></html>\n"
    )


def render_conditions_html_report(
    config: dict[str, Any],
    run_id: str | None = None,
    hours: int = 24,
    location_id: str | None = None,
) -> str:
    (
        selected_locations,
        database_path,
        display_timezone,
        generated_at,
    ) = _report_inputs(config, hours, location_id)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        connection.execute("set TimeZone = 'UTC'")
        validate_report_schema(connection)
        selected_run_id, started_at, completed_at, status, _ = _select_run(
            connection,
            run_id,
        )
        first_hour, window_end = _forecast_window(
            connection,
            selected_run_id,
            started_at,
            hours,
        )
        condition_rows = []
        if first_hour is not None:
            condition_rows = connection.execute(
                """
                select * exclude (row_number)
                from (
                    select
                        location_id,
                        forecast_time,
                        shore_normal_azimuth_degrees,
                        wind_speed_10m,
                        wind_direction_10m,
                        wind_to_shore_angle_degrees,
                        wind_gusts_10m,
                        precipitation_probability,
                        precipitation,
                        wave_height,
                        wave_direction,
                        wave_to_shore_angle_degrees,
                        wave_period,
                        sea_surface_temperature,
                        tide_phase,
                        tide_previous_extremum_time,
                        tide_previous_extremum_type,
                        tide_previous_predicted_water_level,
                        tide_next_extremum_time,
                        tide_next_extremum_type,
                        tide_next_predicted_water_level,
                        tide_predicted_range,
                        row_number() over (
                            partition by location_id
                            order by forecast_time
                        ) as row_number
                    from coastal_conditions_hourly
                    where run_id = ?
                        and forecast_time >= ?
                        and forecast_time < ?
                )
                where row_number = 1
                order by location_id
                """,
                [selected_run_id, first_hour, window_end],
            ).fetchall()

        trend_rows = []
        if first_hour is not None:
            trend_rows = connection.execute(
                """
                select
                    location_id,
                    forecast_time,
                    wind_speed_10m,
                    wind_gusts_10m,
                    wave_height,
                    sea_surface_temperature,
                    wind_to_shore_angle_degrees,
                    wave_to_shore_angle_degrees,
                    tide_phase,
                    tide_previous_extremum_time,
                    tide_previous_extremum_type,
                    tide_previous_predicted_water_level,
                    tide_next_extremum_time,
                    tide_next_extremum_type,
                    tide_next_predicted_water_level
                from coastal_conditions_hourly
                where run_id = ?
                    and forecast_time >= ?
                    and forecast_time < ?
                order by location_id, forecast_time
                """,
                [selected_run_id, first_hour, window_end],
            ).fetchall()

    conditions_by_location = {row[0]: row for row in condition_rows}
    trends_by_location: dict[str, list[tuple[Any, ...]]] = {}
    for row in trend_rows:
        trends_by_location.setdefault(row[0], []).append(row)

    condition_sections = []
    trend_sections = []
    for location in selected_locations:
        location_id_value = location["id"]
        condition_sections.append(
            _condition_summary_html(
                location,
                conditions_by_location.get(location_id_value),
                display_timezone,
            )
        )
        location_trends = trends_by_location.get(location_id_value, [])
        wind_chart = _line_chart_html(
            "Wind speed and gust trend",
            location_trends,
            (("Wind speed", 2), ("Wind gust", 3)),
            "km/h",
            display_timezone,
        )
        wave_chart = _line_chart_html(
            "Wave height trend",
            location_trends,
            (("Wave height", 4),),
            "m",
            display_timezone,
        )
        sst_chart = _line_chart_html(
            "Sea surface temperature trend",
            location_trends,
            (("SST", 5),),
            "°C",
            display_timezone,
        )
        tide_chart = _tide_context_chart_html(
            location_trends,
            display_timezone,
        )
        angle_chart = _line_chart_html(
            "Wind and wave angle to shore trend",
            location_trends,
            (("Wind to shore", 6), ("Wave to shore", 7)),
            "degrees",
            display_timezone,
            fixed_minimum=-180,
            fixed_maximum=180,
            reference_value=0,
        )
        trend_sections.append(
            f'<article id="trends-{escape(location_id_value)}">'
            f'<h3>{_text(location["name"])}</h3>'
            f"{wind_chart}{wave_chart}{sst_chart}{tide_chart}{angle_chart}"
            "<p>Angle reference: 0 degrees is directly onshore; "
            "-180 degrees is directly offshore.</p></article>"
        )

    overview = (
        '<section id="overview"><h2>Selected forecast run</h2>'
        '<dl class="summary">'
        f"<div><dt>Run ID</dt><dd>{_text(selected_run_id)}</dd></div>"
        f"<div><dt>Status</dt><dd>{_text(status)}</dd></div>"
        f"<div><dt>Started</dt><dd>{_time(started_at, display_timezone)}</dd></div>"
        f"<div><dt>Completed</dt><dd>{_time(completed_at, display_timezone)}</dd></div>"
        f"<div><dt>Time since completion</dt>"
        f"<dd>{_elapsed(completed_at, generated_at)}</dd></div>"
        f"<div><dt>Generated</dt><dd>"
        f"{_time(generated_at, display_timezone)}</dd></div>"
        f"<div><dt>Forecast window</dt>"
        f"<dd>{_window_text(first_hour, window_end, display_timezone)}</dd></div>"
        f"<div><dt>Display timezone</dt><dd>{_text(display_timezone.key)}</dd></div>"
        "</dl></section>"
    )
    conditions = (
        '<section id="conditions"><h2>First forecast hour by location</h2>'
        f'{"".join(condition_sections)}</section>'
    )
    trends = (
        '<section id="condition-trends"><h2>Forecast trends</h2>'
        f'{"".join(trend_sections)}</section>'
    )
    limitations = (
        '<section id="limitations"><h2>Limitations</h2>'
        "<p>Unavailable values remain unavailable. SaltBytes stores forecasts and "
        "predictions, not historical observations or fishing recommendations.</p>"
        "</section>"
    )

    return _page_html(
        "SaltBytes coastal conditions",
        "Forecasts and predictions, not observations or fishing recommendations.",
        (
            ("overview", "Overview"),
            ("conditions", "Conditions"),
            ("condition-trends", "Forecast trends"),
            ("limitations", "Limitations"),
        ),
        overview + conditions + trends + limitations,
    )


def render_operations_html_report(
    config: dict[str, Any],
    run_id: str | None = None,
    hours: int = 24,
    location_id: str | None = None,
) -> str:
    (
        selected_locations,
        database_path,
        display_timezone,
        generated_at,
    ) = _report_inputs(config, hours, location_id)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        connection.execute("set TimeZone = 'UTC'")
        validate_report_schema(connection)
        selected_run_id, started_at, completed_at, status, rows_loaded = _select_run(
            connection,
            run_id,
        )
        first_hour, window_end = _forecast_window(
            connection,
            selected_run_id,
            started_at,
            hours,
        )
        source_rows = connection.execute(
            """
            select location_id, source, status, detail
            from source_results
            where run_id = ?
            """,
            [selected_run_id],
        ).fetchall()
        revision_section = render_revision_section(
            connection,
            selected_locations,
            first_hour,
            window_end,
            display_timezone,
        )
        monitoring_section = render_monitoring_section(
            connection,
            generated_at,
            display_timezone,
        )
        source_monitoring_section = render_source_monitoring_section(
            connection,
            selected_locations,
            display_timezone,
        )
        provenance_section = render_provenance_section(
            connection,
            selected_run_id,
            selected_locations,
            first_hour,
            window_end,
            display_timezone,
        )

    source_results: dict[str, dict[str, tuple[str, str | None]]] = {}
    for result_location_id, source, source_status, detail in source_rows:
        source_results.setdefault(result_location_id, {})[source] = (
            source_status,
            detail,
        )

    source_sections = []
    for location in selected_locations:
        location_id_value = location["id"]
        source_sections.append(
            f'<article id="source-{escape(location_id_value)}">'
            f"<h3>{_text(location['name'])}</h3>"
            f"<p>{_text(location['fishing_context'])}</p>"
            f"{_source_status_html(location_id_value, source_results)}"
            "</article>"
        )

    overview = (
        '<section id="overview"><h2>Selected pipeline run</h2>'
        '<dl class="summary">'
        f"<div><dt>Run ID</dt><dd>{_text(selected_run_id)}</dd></div>"
        f"<div><dt>Status</dt><dd>{_text(status)}</dd></div>"
        f"<div><dt>Started</dt><dd>{_time(started_at, display_timezone)}</dd></div>"
        f"<div><dt>Completed</dt><dd>{_time(completed_at, display_timezone)}</dd></div>"
        f"<div><dt>Rows loaded</dt><dd>{rows_loaded}</dd></div>"
        f"<div><dt>Time since completion</dt>"
        f"<dd>{_elapsed(completed_at, generated_at)}</dd></div>"
        f"<div><dt>Generated</dt><dd>"
        f"{_time(generated_at, display_timezone)}</dd></div>"
        f"<div><dt>Forecast window</dt>"
        f"<dd>{_window_text(first_hour, window_end, display_timezone)}</dd></div>"
        f"<div><dt>Display timezone</dt><dd>{_text(display_timezone.key)}</dd></div>"
        f"<div><dt>Database source</dt><dd>{_text(database_path.name)}</dd></div>"
        "</dl></section>"
    )
    sources = (
        '<section id="sources"><h2>Source status</h2>'
        f'{"".join(source_sections)}</section>'
    )
    limitations = (
        '<section id="limitations"><h2>Limitations</h2>'
        "<p>Operational metrics describe pipeline behavior and retained forecast "
        "evidence. They do not measure forecast accuracy or fishing outcomes.</p>"
        "</section>"
    )

    return _page_html(
        "SaltBytes pipeline operations",
        "Ingestion health, source coverage, revision history, and provenance.",
        (
            ("overview", "Overview"),
            ("revisions", "Forecast revisions"),
            ("monitoring", "Monitoring"),
            ("source-monitoring", "Source monitoring"),
            ("sources", "Source status"),
            ("provenance", "Provenance"),
            ("limitations", "Limitations"),
        ),
        (
            overview
            + revision_section
            + monitoring_section
            + source_monitoring_section
            + sources
            + provenance_section
            + limitations
        ),
    )


def render_html_report(
    config: dict[str, Any],
    run_id: str | None = None,
    hours: int = 24,
    location_id: str | None = None,
) -> str:
    return render_conditions_html_report(
        config,
        run_id=run_id,
        hours=hours,
        location_id=location_id,
    )
