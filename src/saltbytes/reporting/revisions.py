from datetime import datetime
from html import escape
from typing import Any
from zoneinfo import ZoneInfo

import duckdb


def _text(value: object | None) -> str:
    return "Unavailable" if value is None else escape(str(value))


def _time(value: datetime, display_timezone: ZoneInfo) -> str:
    return value.astimezone(display_timezone).strftime("%Y-%m-%d %H:%M %Z")


def _number(value: float | None, unit: str) -> str:
    if value is None:
        return "Unavailable"
    return f"{value:.1f} {unit}"


def _insufficient_history_html() -> str:
    return (
        '<section id="revisions"><h2>Forecast revisions</h2>'
        "<p>Insufficient persisted history: no selected location and valid "
        "forecast hour has values from at least two distinct runs within the "
        "selected forecast window.</p></section>"
    )


def render_revision_section(
    connection: duckdb.DuckDBPyConnection,
    locations: list[dict[str, Any]],
    window_start: datetime | None,
    window_end: datetime | None,
    display_timezone: ZoneInfo,
) -> str:
    if window_start is None or window_end is None or not locations:
        return _insufficient_history_html()

    location_ids = [location["id"] for location in locations]
    placeholders = ", ".join("?" for _ in location_ids)
    candidate = connection.execute(
        f"""
        select
            location_id,
            forecast_time,
            count(distinct run_id) as run_count
        from coastal_conditions_hourly
        where forecast_time >= ?
            and forecast_time < ?
            and location_id in ({placeholders})
        group by location_id, forecast_time
        having count(distinct run_id) >= 2
        order by run_count desc, forecast_time, location_id
        limit 1
        """,
        [window_start, window_end, *location_ids],
    ).fetchone()

    if candidate is None:
        return _insufficient_history_html()

    location_id, valid_time, run_count = candidate
    rows = connection.execute(
        """
        select
            run_id,
            run_started_at,
            wind_speed_10m,
            wave_height,
            sea_surface_temperature,
            tide_phase
        from coastal_conditions_hourly
        where location_id = ? and forecast_time = ?
        order by run_started_at, run_id
        """,
        [location_id, valid_time],
    ).fetchall()

    locations_by_id = {location["id"]: location for location in locations}
    location_name = locations_by_id[location_id]["name"]
    body_rows = []
    for run_id, started_at, wind_speed, wave_height, sst, tide_phase in rows:
        body_rows.append(
            "<tr>"
            f"<td>{_text(run_id)}</td>"
            f"<td>{_time(started_at, display_timezone)}</td>"
            f"<td>{_number(wind_speed, 'km/h')}</td>"
            f"<td>{_number(wave_height, 'm')}</td>"
            f"<td>{_number(sst, '°C')}</td>"
            f"<td>{_text(tide_phase)}</td>"
            "</tr>"
        )

    return (
        '<section id="revisions"><h2>Forecast revisions</h2>'
        f"<p><strong>Location:</strong> {_text(location_name)}</p>"
        f"<p><strong>Forecast valid time:</strong> "
        f"{_time(valid_time, display_timezone)}</p>"
        f"<p>{run_count} persisted runs contribute to this comparison. "
        "Pipeline run start time remains distinct from forecast valid time.</p>"
        '<div class="table-scroll"><table><thead><tr>'
        "<th>Run ID</th><th>Run started</th><th>Wind speed</th>"
        "<th>Wave height</th><th>SST</th><th>Tide phase</th>"
        f'</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'
        "</section>"
    )
