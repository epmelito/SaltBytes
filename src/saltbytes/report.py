from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import duckdb

_SOURCES = ("weather", "wave", "sst", "tide")


def _format_time(value: datetime, display_timezone: ZoneInfo) -> str:
    return value.astimezone(display_timezone).strftime("%Y-%m-%d %H:%M %Z")


def _format_value(value: float | None, precision: int = 1) -> str:
    if value is None:
        return "-"

    return f"{value:.{precision}f}"


def _source_summary(
    source_results: dict[str, tuple[str, str | None]],
) -> str:
    summaries = []

    for source in _SOURCES:
        status, detail = source_results.get(source, ("not attempted", None))
        summary = f"{source}: {status}"
        if detail:
            summary = f"{summary} ({detail})"
        summaries.append(summary)

    return " | ".join(summaries)


def _select_run(
    connection: duckdb.DuckDBPyConnection,
    run_id: str | None,
) -> tuple[str, datetime, datetime | None, str, int]:
    if run_id is None:
        run = connection.execute(
            """
            select run_id, started_at, completed_at, status, rows_loaded
            from pipeline_runs
            order by started_at desc, run_id desc
            limit 1
            """
        ).fetchone()
    else:
        run = connection.execute(
            """
            select run_id, started_at, completed_at, status, rows_loaded
            from pipeline_runs
            where run_id = ?
            """,
            [run_id],
        ).fetchone()

    if run is None:
        identifier = run_id or "latest"
        raise ValueError(f"no pipeline run found for: {identifier}")

    return run


def render_conditions_report(
    config: dict[str, Any],
    run_id: str | None = None,
    hours: int = 24,
    location_id: str | None = None,
) -> str:
    if hours <= 0:
        raise ValueError("hours must be greater than zero")

    locations = config["locations"]
    locations_by_id = {location["id"]: location for location in locations}
    if location_id is not None and location_id not in locations_by_id:
        raise ValueError(f"unknown location: {location_id}")

    selected_locations = (
        [locations_by_id[location_id]] if location_id else locations
    )
    display_timezone = ZoneInfo(config["display_timezone"])
    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        selected_run_id, started_at, completed_at, status, _rows_loaded = _select_run(
            connection,
            run_id,
        )
        first_hour = connection.execute(
            """
            select min(forecast_time)
            from coastal_conditions_hourly
            where run_id = ? and forecast_time >= ?
            """,
            [selected_run_id, started_at],
        ).fetchone()[0]
        window_end = first_hour + timedelta(hours=hours) if first_hour else None

        report_rows = connection.execute(
            """
            select
                location_id,
                forecast_time,
                wind_speed_10m,
                wind_direction_10m,
                wind_gusts_10m,
                precipitation_probability,
                precipitation,
                wave_height,
                wave_direction,
                wave_period,
                sea_surface_temperature,
                tide_phase
            from coastal_conditions_hourly
            where run_id = ?
                and forecast_time >= ?
                and forecast_time < ?
            order by location_id, forecast_time
            """,
            [selected_run_id, first_hour, window_end],
        ).fetchall() if first_hour else []

    rows_by_location: dict[str, list[tuple[Any, ...]]] = {}
    for row in report_rows:
        rows_by_location.setdefault(row[0], []).append(row)

    completed_text = (
        _format_time(completed_at, display_timezone)
        if completed_at is not None
        else "not completed"
    )
    lines = [
        f"Run: {selected_run_id}",
        f"Status: {status}",
        f"Started: {_format_time(started_at, display_timezone)}",
        f"Completed: {completed_text}",
        f"Display timezone: {display_timezone.key}",
    ]
    if first_hour is None:
        lines.append("Forecast window: no integrated hours at or after run start")
    else:
        lines.append(
            "Forecast window: "
            f"{_format_time(first_hour, display_timezone)} through "
            f"{_format_time(window_end - timedelta(hours=1), display_timezone)}"
        )

    header = (
        "Time | Wind km/h | Dir deg | Gust km/h | Precip % | Rain mm | "
        "Wave m | Wave dir deg | Period s | SST C | Tide"
    )
    for location in selected_locations:
        current_location_id = location["id"]
        lines.extend(
            [
                "",
                f"{location['name']} ({location['fishing_context']})",
            ]
        )
        location_rows = rows_by_location.get(current_location_id, [])
        if not location_rows:
            lines.append("No integrated forecast hours in the selected window.")
            continue

        lines.append(header)
        for row in location_rows:
            (
                _,
                forecast_time,
                wind_speed,
                wind_direction,
                wind_gust,
                precipitation_probability,
                precipitation,
                wave_height,
                wave_direction,
                wave_period,
                sea_surface_temperature,
                tide_phase,
            ) = row
            lines.append(
                " | ".join(
                    (
                        _format_time(forecast_time, display_timezone),
                        _format_value(wind_speed),
                        _format_value(wind_direction, 0),
                        _format_value(wind_gust),
                        _format_value(precipitation_probability, 0),
                        _format_value(precipitation),
                        _format_value(wave_height),
                        _format_value(wave_direction, 0),
                        _format_value(wave_period),
                        _format_value(sea_surface_temperature),
                        tide_phase or "-",
                    )
                )
            )

    return "\n".join(lines)


def render_operations_report(
    config: dict[str, Any],
    run_id: str | None = None,
    hours: int = 24,
    location_id: str | None = None,
) -> str:
    if hours <= 0:
        raise ValueError("hours must be greater than zero")

    locations = config["locations"]
    locations_by_id = {location["id"]: location for location in locations}
    if location_id is not None and location_id not in locations_by_id:
        raise ValueError(f"unknown location: {location_id}")

    selected_locations = (
        [locations_by_id[location_id]] if location_id else locations
    )
    display_timezone = ZoneInfo(config["display_timezone"])
    database_path = Path(config["storage"]["database_path"])

    with duckdb.connect(str(database_path), read_only=True) as connection:
        selected_run_id, started_at, completed_at, status, rows_loaded = _select_run(
            connection,
            run_id,
        )
        first_hour = connection.execute(
            """
            select min(forecast_time)
            from coastal_conditions_hourly
            where run_id = ? and forecast_time >= ?
            """,
            [selected_run_id, started_at],
        ).fetchone()[0]
        window_end = first_hour + timedelta(hours=hours) if first_hour else None
        source_rows = connection.execute(
            """
            select location_id, source, status, detail
            from source_results
            where run_id = ?
            """,
            [selected_run_id],
        ).fetchall()

    source_results: dict[str, dict[str, tuple[str, str | None]]] = {}
    for result_location_id, source, source_status, detail in source_rows:
        source_results.setdefault(result_location_id, {})[source] = (
            source_status,
            detail,
        )

    completed_text = (
        _format_time(completed_at, display_timezone)
        if completed_at is not None
        else "not completed"
    )
    lines = [
        f"Run: {selected_run_id}",
        f"Status: {status}",
        f"Started: {_format_time(started_at, display_timezone)}",
        f"Completed: {completed_text}",
        f"Rows loaded: {rows_loaded}",
        f"Display timezone: {display_timezone.key}",
    ]
    if first_hour is None:
        lines.append("Forecast window: no integrated hours at or after run start")
    else:
        lines.append(
            "Forecast window: "
            f"{_format_time(first_hour, display_timezone)} through "
            f"{_format_time(window_end - timedelta(hours=1), display_timezone)}"
        )

    for location in selected_locations:
        current_location_id = location["id"]
        lines.extend(
            [
                "",
                f"{location['name']} ({location['fishing_context']})",
                f"Sources: {_source_summary(source_results.get(current_location_id, {}))}",
            ]
        )

    return "\n".join(lines)
