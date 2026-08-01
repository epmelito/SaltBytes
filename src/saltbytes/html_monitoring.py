from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

import duckdb


def _text(value: object | None) -> str:
    return "Unavailable" if value is None else escape(str(value))


def _time(value: datetime | None, display_timezone: ZoneInfo) -> str:
    if value is None:
        return "Unavailable"
    return value.astimezone(display_timezone).strftime("%Y-%m-%d %H:%M %Z")


def _duration(started_at: datetime, completed_at: datetime | None) -> str:
    if completed_at is None:
        return "Unavailable"
    seconds = max(int((completed_at - started_at).total_seconds()), 0)
    return f"{seconds} s"


def _elapsed(completed_at: datetime | None, generated_at: datetime) -> str:
    if completed_at is None:
        return "Unavailable"

    minutes = max(int((generated_at - completed_at).total_seconds() // 60), 0)
    days, remaining_minutes = divmod(minutes, 24 * 60)
    hours, remaining_minutes = divmod(remaining_minutes, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{remaining_minutes}m")
    return " ".join(parts)


def _status_timeline(
    recent_runs: list[tuple[object, ...]],
    display_timezone: ZoneInfo,
) -> str:
    if not recent_runs:
        return (
            '<div class="chart"><h3>Recent run status timeline</h3>'
            '<p>Recent run status timeline: Unavailable.</p></div>'
        )

    ordered_runs = list(reversed(recent_runs))
    width, height = 640, 130
    left, right, marker_y = 50, 20, 48
    plot_width = width - left - right
    denominator = max(len(ordered_runs) - 1, 1)
    markers = []

    for index, run in enumerate(ordered_runs):
        run_id, started_at, _, status, _, _ = run
        x = (
            left + plot_width / 2
            if len(ordered_runs) == 1
            else left + index / denominator * plot_width
        )
        symbol = {"success": "S", "failed": "F"}.get(status, "?")
        title = (
            f"{_text(run_id)} | "
            f"{_time(started_at, display_timezone)} | {_text(status)}"
        )
        markers.append(
            f'<g data-status-marker="{_text(status)}"><title>{title}</title>'
            f'<rect x="{x - 9:.1f}" y="{marker_y - 9}" width="18" '
            'height="18" fill="white" stroke="currentColor"/>'
            f'<text x="{x:.1f}" y="{marker_y + 4}" '
            f'text-anchor="middle">{symbol}</text></g>'
        )

    return (
        '<div class="chart"><h3>Recent run status timeline</h3>'
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Recent run status timeline">'
        f'<line class="axis" x1="{left}" y1="{marker_y}" '
        f'x2="{width - right}" y2="{marker_y}"/>'
        f'{"".join(markers)}'
        f'<text x="{left}" y="88">'
        f'{_time(ordered_runs[0][1], display_timezone)}</text>'
        f'<text x="{width - right}" y="88" text-anchor="end">'
        f'{_time(ordered_runs[-1][1], display_timezone)}</text>'
        '<text x="50" y="116">S success · F failed · ? other</text>'
        '</svg></div>'
    )


def _run_bar_chart(
    title: str,
    unit: str,
    recent_runs: list[tuple[object, ...]],
    values: list[float | None],
    display_timezone: ZoneInfo,
) -> str:
    ordered = list(reversed(list(zip(recent_runs, values, strict=True))))
    available_values = [value for _, value in ordered if value is not None]
    if not available_values:
        return (
            f'<div class="chart"><h3>{_text(title)}</h3>'
            f'<p>{_text(title)}: Unavailable.</p></div>'
        )

    width, height = 640, 190
    left, right, top, bottom = 52, 16, 20, 42
    plot_width = width - left - right
    plot_height = height - top - bottom
    maximum = max(max(available_values), 1.0)
    slot_width = plot_width / max(len(ordered), 1)
    bar_width = max(min(slot_width * 0.65, 24), 2)
    bars = []

    for index, (run, value) in enumerate(ordered):
        run_id, started_at, _, _, _, _ = run
        center_x = left + (index + 0.5) * slot_width
        if value is None:
            bars.append(
                f'<text x="{center_x:.1f}" y="{top + plot_height - 4:.1f}" '
                'text-anchor="middle">?</text>'
            )
            continue

        bar_height = max(value / maximum * plot_height, 1.0)
        y = top + plot_height - bar_height
        title_text = (
            f"{_text(run_id)} | {_time(started_at, display_timezone)} | "
            f"{value:.1f} {_text(unit)}"
        )
        bars.append(
            f'<rect x="{center_x - bar_width / 2:.1f}" y="{y:.1f}" '
            f'width="{bar_width:.1f}" height="{bar_height:.1f}" '
            f'fill="currentColor"><title>{title_text}</title></rect>'
        )

    return (
        f'<div class="chart"><h3>{_text(title)}</h3>'
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{_text(title)}">'
        f'<line class="axis" x1="{left}" y1="{top + plot_height}" '
        f'x2="{width - right}" y2="{top + plot_height}"/>'
        f'<text x="4" y="{top + 4}">{maximum:.1f} {_text(unit)}</text>'
        f'<text x="32" y="{top + plot_height + 4}">0</text>'
        f'{"".join(bars)}'
        f'<text x="{left}" y="{height - 10}">'
        f'{_time(ordered[0][0][1], display_timezone)}</text>'
        f'<text x="{width - right}" y="{height - 10}" text-anchor="end">'
        f'{_time(ordered[-1][0][1], display_timezone)}</text>'
        '</svg></div>'
    )


def render_monitoring_section(
    connection: duckdb.DuckDBPyConnection,
    generated_at: datetime,
    display_timezone: ZoneInfo,
) -> str:
    recent_runs = connection.execute(
        """
        with recent_runs as (
            select
                run_id,
                started_at,
                completed_at,
                status,
                rows_loaded
            from pipeline_runs
            order by started_at desc, run_id desc
            limit 20
        )
        select
            recent_runs.run_id,
            recent_runs.started_at,
            recent_runs.completed_at,
            recent_runs.status,
            recent_runs.rows_loaded,
            count(forecast_snapshots.snapshot_id) as snapshot_count
        from recent_runs
        left join forecast_snapshots
            on forecast_snapshots.run_id = recent_runs.run_id
        group by
            recent_runs.run_id,
            recent_runs.started_at,
            recent_runs.completed_at,
            recent_runs.status,
            recent_runs.rows_loaded
        order by recent_runs.started_at desc, recent_runs.run_id desc
        """
    ).fetchall()

    latest_success = connection.execute(
        """
        select run_id, completed_at
        from pipeline_runs
        where status = 'success' and completed_at is not null
        order by completed_at desc, run_id desc
        limit 1
        """
    ).fetchone()
    ordered_statuses = connection.execute(
        """
        select status
        from pipeline_runs
        order by started_at desc, run_id desc
        """
    ).fetchall()

    consecutive_failures = 0
    for (status,) in ordered_statuses:
        if status != "failed":
            break
        consecutive_failures += 1

    success_count = sum(run[3] == "success" for run in recent_runs)
    failure_count = sum(run[3] == "failed" for run in recent_runs)
    duration_values = [
        (
            max((run[2] - run[1]).total_seconds(), 0.0)
            if run[2] is not None
            else None
        )
        for run in recent_runs
    ]
    rows_loaded_values = [float(run[4]) for run in recent_runs]
    monitoring_charts = (
        _status_timeline(recent_runs, display_timezone)
        + _run_bar_chart(
            "Recent run duration",
            "seconds",
            recent_runs,
            duration_values,
            display_timezone,
        )
        + _run_bar_chart(
            "Rows loaded by run",
            "rows",
            recent_runs,
            rows_loaded_values,
            display_timezone,
        )
    )

    if latest_success is None:
        latest_success_text = "Unavailable"
        latest_success_elapsed = "Unavailable"
    else:
        latest_success_text = (
            f"{_text(latest_success[0])} at "
            f"{_time(latest_success[1], display_timezone)}"
        )
        latest_success_elapsed = _elapsed(latest_success[1], generated_at)

    rows = []
    for (
        run_id,
        started_at,
        completed_at,
        status,
        rows_loaded,
        snapshot_count,
    ) in recent_runs:
        data_note = (
            "partial data" if status == "failed" and rows_loaded > 0 else ""
        )
        rows.append(
            f'<tr data-run-id="{_text(run_id)}">'
            f"<td>{_text(run_id)}</td>"
            f"<td>{_time(started_at, display_timezone)}</td>"
            f"<td>{_time(completed_at, display_timezone)}</td>"
            f"<td>{_text(status)}</td>"
            f"<td>{_duration(started_at, completed_at)}</td>"
            f"<td>{rows_loaded}</td>"
            f"<td>{snapshot_count}</td>"
            f"<td>{data_note}</td>"
            "</tr>"
        )

    if rows:
        table_body = "".join(rows)
    else:
        table_body = '<tr><td colspan="8">No pipeline runs recorded.</td></tr>'

    return (
        '<section id="monitoring"><h2>Ingestion monitoring</h2>'
        '<dl class="summary">'
        f"<div><dt>Latest successful run</dt><dd>{latest_success_text}</dd></div>"
        f"<div><dt>Elapsed since latest success</dt>"
        f"<dd>{latest_success_elapsed}</dd></div>"
        f"<div><dt>Consecutive failed runs</dt>"
        f"<dd>{consecutive_failures}</dd></div>"
        f"<div><dt>Recent successful runs</dt><dd>{success_count}</dd></div>"
        f"<div><dt>Recent failed runs</dt><dd>{failure_count}</dd></div>"
        f"<div><dt>Displayed runs</dt><dd>{len(recent_runs)}</dd></div>"
        "</dl>"
        f"{monitoring_charts}"
        '<div class="table-scroll"><table><thead><tr>'
        "<th>Run ID</th><th>Started</th><th>Completed</th><th>Status</th>"
        "<th>Duration</th><th>Rows loaded</th><th>Snapshots</th>"
        "<th>Data note</th>"
        f"</tr></thead><tbody>{table_body}</tbody></table></div>"
        "</section>"
    )
