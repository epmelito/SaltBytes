from datetime import datetime
from html import escape
from typing import Any
from zoneinfo import ZoneInfo

import duckdb

_SOURCES = ("weather", "wave", "sst", "tide")


def _text(value: object | None) -> str:
    return "Unavailable" if value is None else escape(str(value))


def _number(value: float | None, unit: str = "") -> str:
    if value is None:
        return "Unavailable"

    suffix = f" {unit}" if unit else ""
    return f"{value:.0f}{suffix}"


def render_provenance_section(
    connection: duckdb.DuckDBPyConnection,
    run_id: str,
    selected_locations: list[dict[str, Any]],
    first_hour: datetime | None,
    window_end: datetime | None,
    display_timezone: ZoneInfo,
) -> str:
    location_ids = [location["id"] for location in selected_locations]
    placeholders = ", ".join("?" for _ in location_ids)
    orientation_rows = connection.execute(
        f"""
        select
            location_id,
            fishing_context,
            shore_normal_azimuth_degrees,
            pier_seaward_azimuth_degrees,
            orientation_method,
            orientation_source,
            orientation_reviewed_at,
            orientation_limitation
        from run_locations
        where run_id = ? and location_id in ({placeholders})
        order by location_id
        """,
        [run_id, *location_ids],
    ).fetchall()
    orientations = {row[0]: row[1:] for row in orientation_rows}

    snapshot_rows = []
    if first_hour is not None and window_end is not None:
        snapshot_rows = connection.execute(
            f"""
            select * exclude (row_number)
            from (
                select
                    location_id,
                    forecast_time,
                    weather_snapshot_id,
                    wave_snapshot_id,
                    sst_snapshot_id,
                    tide_snapshot_id,
                    row_number() over (
                        partition by location_id
                        order by forecast_time
                    ) as row_number
                from coastal_conditions_hourly
                where run_id = ?
                    and forecast_time >= ?
                    and forecast_time < ?
                    and location_id in ({placeholders})
            )
            where row_number = 1
            order by location_id
            """,
            [run_id, first_hour, window_end, *location_ids],
        ).fetchall()
    snapshots = {row[0]: row[1:] for row in snapshot_rows}

    articles = []
    for location in selected_locations:
        location_id = location["id"]
        orientation = orientations.get(location_id, (None,) * 7)
        (
            fishing_context,
            shore_normal,
            pier_alignment,
            method,
            source,
            reviewed_at,
            limitation,
        ) = orientation
        snapshot = snapshots.get(location_id, (None,) * 5)
        forecast_time, *snapshot_ids = snapshot
        snapshot_fields = "".join(
            f"<div><dt>{label.title()} snapshot</dt>"
            f"<dd><code>{_text(snapshot_id)}</code></dd></div>"
            for label, snapshot_id in zip(
                _SOURCES,
                snapshot_ids,
                strict=True,
            )
        )
        forecast_time_text = (
            forecast_time.astimezone(display_timezone).strftime(
                "%Y-%m-%d %H:%M %Z"
            )
            if forecast_time is not None
            else "Unavailable"
        )
        articles.append(
            f'<article id="provenance-{escape(location_id)}">'
            f'<h3>{_text(location["name"])}</h3><dl class="summary">'
            f"<div><dt>Persisted fishing context</dt>"
            f"<dd>{_text(fishing_context)}</dd></div>"
            f"<div><dt>Persisted shore normal</dt>"
            f"<dd>{_number(shore_normal, 'degrees')}</dd></div>"
            f"<div><dt>Persisted pier alignment</dt>"
            f"<dd>{_number(pier_alignment, 'degrees')}</dd></div>"
            f"<div><dt>Orientation method</dt><dd>{_text(method)}</dd></div>"
            f"<div><dt>Orientation source</dt><dd>{_text(source)}</dd></div>"
            f"<div><dt>Orientation reviewed</dt>"
            f"<dd>{_text(reviewed_at)}</dd></div>"
            f"<div><dt>Orientation limitation</dt>"
            f"<dd>{_text(limitation)}</dd></div>"
            f"<div><dt>Snapshot valid time</dt>"
            f"<dd>{forecast_time_text}</dd></div>"
            f"{snapshot_fields}</dl></article>"
        )

    return (
        '<section id="provenance"><h2>Provenance</h2>'
        "<p>Orientation metadata is preserved with the selected run. Snapshot "
        "identifiers below produced the first displayed forecast hour. Raw file "
        "paths are intentionally omitted.</p>"
        f'{"".join(articles)}</section>'
    )
