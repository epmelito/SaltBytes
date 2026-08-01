from datetime import datetime
from html import escape
from typing import Any
from zoneinfo import ZoneInfo

import duckdb

_SOURCES = ("weather", "wave", "sst", "tide")


def _text(value: object | None) -> str:
    return "Unavailable" if value is None else escape(str(value))


def _time(value: datetime | None, display_timezone: ZoneInfo) -> str:
    if value is None:
        return "Unavailable"
    return value.astimezone(display_timezone).strftime("%Y-%m-%d %H:%M %Z")


def _source_rate_chart(
    rates: list[tuple[str, float | None]],
) -> str:
    available_rates = [rate for _, rate in rates if rate is not None]
    if not available_rates:
        return (
            '<div class="chart"><h3>Source success rates</h3>'
            '<p>Source success rates: Unavailable.</p></div>'
        )

    width = 640
    left, right, top = 90, 36, 18
    row_height = 30
    plot_width = width - left - right
    height = top + len(rates) * row_height + 28
    bars = []

    for index, (source, rate) in enumerate(rates):
        y = top + index * row_height
        bars.append(f'<text x="4" y="{y + 15}">{_text(source)}</text>')
        if rate is None:
            bars.append(
                f'<text x="{left}" y="{y + 15}">Unavailable</text>'
            )
            continue

        bar_width = rate / 100 * plot_width
        bars.append(
            f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" '
            'height="18" fill="currentColor">'
            f'<title>{_text(source)}: {rate:.1f}%</title></rect>'
            f'<text x="{left + bar_width + 6:.1f}" y="{y + 15}">'
            f'{rate:.1f}%</text>'
        )

    return (
        '<div class="chart"><h3>Source success rates</h3>'
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Source success rates">'
        f'{"".join(bars)}'
        f'<text x="{left}" y="{height - 6}">0%</text>'
        f'<text x="{width - right}" y="{height - 6}" text-anchor="end">100%</text>'
        '</svg></div>'
    )


def render_source_monitoring_section(
    connection: duckdb.DuckDBPyConnection,
    locations: list[dict[str, Any]],
    display_timezone: ZoneInfo,
) -> str:
    recent_runs = connection.execute(
        """
        select run_id, started_at
        from pipeline_runs
        order by started_at desc, run_id desc
        limit 20
        """
    ).fetchall()
    recent_run_ids = {run_id for run_id, _ in recent_runs}
    selected_location_ids = {location["id"] for location in locations}

    source_rows = connection.execute(
        """
        with recent_runs as (
            select run_id
            from pipeline_runs
            order by started_at desc, run_id desc
            limit 20
        )
        select
            source_results.run_id,
            source_results.location_id,
            source_results.source,
            source_results.status,
            source_results.detail,
            source_results.recorded_at
        from source_results
        inner join recent_runs
            on recent_runs.run_id = source_results.run_id
        order by source_results.recorded_at desc,
            source_results.run_id desc,
            source_results.location_id,
            source_results.source
        """
    ).fetchall()

    results = {
        (run_id, location_id, source): (status, detail, recorded_at)
        for run_id, location_id, source, status, detail, recorded_at in source_rows
        if run_id in recent_run_ids
        and location_id in selected_location_ids
        and source in _SOURCES
    }

    expected_per_source = len(recent_runs) * len(locations)
    rate_rows = []
    rate_values = []
    missing_total = 0
    for source in _SOURCES:
        statuses = [
            results.get((run_id, location["id"], source))
            for run_id, _ in recent_runs
            for location in locations
        ]
        success_count = sum(
            result is not None and result[0] == "success" for result in statuses
        )
        failure_count = sum(
            result is not None and result[0] != "success" for result in statuses
        )
        missing_count = sum(result is None for result in statuses)
        missing_total += missing_count
        success_rate_value = (
            success_count / expected_per_source * 100
            if expected_per_source
            else None
        )
        success_rate = (
            f"{success_rate_value:.1f}%"
            if success_rate_value is not None
            else "Unavailable"
        )
        rate_values.append((source, success_rate_value))
        rate_rows.append(
            "<tr>"
            f"<td>{source}</td>"
            f"<td>{success_count}</td>"
            f"<td>{failure_count}</td>"
            f"<td>{missing_count}</td>"
            f"<td>{success_rate}</td>"
            "</tr>"
        )

    coverage_rows = []
    for run_id, started_at in recent_runs:
        for location in locations:
            status_cells = []
            for source in _SOURCES:
                result = results.get((run_id, location["id"], source))
                status = "not recorded" if result is None else result[0]
                status_cells.append(f"<td>{_text(status)}</td>")
            coverage_rows.append(
                f'<tr data-source-run="{_text(run_id)}" '
                f'data-location="{_text(location["id"])}">'
                f"<td>{_time(started_at, display_timezone)}</td>"
                f"<td>{_text(run_id)}</td>"
                f"<td>{_text(location['name'])}</td>"
                f"{''.join(status_cells)}</tr>"
            )

    failure_rows = []
    for run_id, location_id, source, status, detail, recorded_at in source_rows:
        if (
            run_id not in recent_run_ids
            or location_id not in selected_location_ids
            or source not in _SOURCES
            or status == "success"
        ):
            continue
        failure_rows.append(
            "<tr>"
            f"<td>{_text(run_id)}</td>"
            f"<td>{_text(location_id)}</td>"
            f"<td>{_text(source)}</td>"
            f"<td>{_text(status)}</td>"
            f"<td>{_time(recorded_at, display_timezone)}</td>"
            f"<td>{_text(detail)}</td>"
            "</tr>"
        )

    if coverage_rows:
        coverage_body = "".join(coverage_rows)
    else:
        coverage_body = '<tr><td colspan="7">No pipeline runs recorded.</td></tr>'

    if failure_rows:
        failure_body = "".join(failure_rows)
    else:
        failure_body = '<tr><td colspan="6">No recent source failures.</td></tr>'

    expected_total = expected_per_source * len(_SOURCES)
    return (
        '<section id="source-monitoring"><h2>Source monitoring</h2>'
        f"<p>Missing source results: {missing_total} of {expected_total} "
        "expected records.</p>"
        f"{_source_rate_chart(rate_values)}"
        '<div class="table-scroll"><table><thead><tr>'
        "<th>Source</th><th>Success</th><th>Failed</th><th>Missing</th>"
        "<th>Success rate</th>"
        f"</tr></thead><tbody>{''.join(rate_rows)}</tbody></table></div>"
        "<h3>Run and location coverage</h3>"
        '<div class="table-scroll"><table><thead><tr>'
        "<th>Run started</th><th>Run ID</th><th>Location</th>"
        "<th>Weather</th><th>Wave</th><th>SST</th><th>Tide</th>"
        f"</tr></thead><tbody>{coverage_body}</tbody></table></div>"
        "<h3>Recent source failures</h3>"
        '<div class="table-scroll"><table><thead><tr>'
        "<th>Run ID</th><th>Location</th><th>Source</th><th>Status</th>"
        "<th>Recorded</th><th>Detail</th>"
        f"</tr></thead><tbody>{failure_body}</tbody></table></div>"
        "</section>"
    )
