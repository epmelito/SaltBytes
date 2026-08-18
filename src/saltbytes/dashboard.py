import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from saltbytes.reporting.schema import (
    ReportSchemaError,
    validate_dashboard_score_schema,
)
from saltbytes.spanish_mackerel import (
    AvailableSpanishMackerelConditionsScore,
    SpanishMackerelConditionsInput,
    calculate_spanish_mackerel_conditions_score,
)

_SOURCES = ("weather", "pressure", "wave", "sst", "tide")
_EXPORT_FILES = (
    "manifest.json",
    "locations.json",
    "conditions.json",
    "forecast-history.json",
    "pipeline-runs.json",
    "source-health.json",
    "observation-health.json",
    "provenance.json",
)


class DashboardSchemaError(ValueError):
    pass


def _json_value(value: object | None) -> object | None:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _query(
    connection: duckdb.DuckDBPyConnection,
    sql: str,
    parameters: list[object] | None = None,
) -> list[dict[str, object | None]]:
    cursor = connection.execute(sql, parameters or [])
    columns = [description[0] for description in cursor.description]
    return [
        {
            column: _json_value(value)
            for column, value in zip(columns, row, strict=True)
        }
        for row in cursor.fetchall()
    ]


def _run_record(row: tuple[Any, ...]) -> dict[str, object | None]:
    run_id, started_at, completed_at, status, rows_loaded = row
    return {
        "run_id": run_id,
        "started_at": _json_value(started_at),
        "completed_at": _json_value(completed_at),
        "status": status,
        "rows_loaded": rows_loaded,
    }


def _write_json(path: Path, payload: object) -> None:
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as output_file:
            json.dump(
                payload,
                output_file,
                allow_nan=False,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            output_file.write("\n")
        temporary_path.replace(path)
    except (OSError, ValueError) as exc:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"could not write dashboard data: {path}") from exc


def _score_projection(
    value: SpanishMackerelConditionsInput,
) -> dict[str, object]:
    result = calculate_spanish_mackerel_conditions_score(value)
    if isinstance(result, AvailableSpanishMackerelConditionsScore):
        return {
            "state": result.state,
            "methodology_version": result.methodology_version,
            "score": result.score,
            "score_band": result.score_band,
            "confidence": [
                {"identifier": item.identifier, "state": item.state}
                for item in result.confidence
            ],
            "positive_factors": list(result.positive_factors),
            "limiting_factors": list(result.limiting_factors),
            "unknown_factors": list(result.unknown_factors),
        }
    return {
        "state": result.state,
        "methodology_version": result.methodology_version,
        "unavailable_reasons": list(result.unavailable_reasons),
    }


def _dashboard_conditions(
    connection: duckdb.DuckDBPyConnection,
    run_id: str,
    started_at: datetime,
) -> list[dict[str, object]]:
    cursor = connection.execute(
        """
        select
            conditions.run_id,
            conditions.location_id,
            conditions.forecast_time,
            conditions.shore_normal_azimuth_degrees,
            conditions.weather_snapshot_id,
            conditions.precipitation_probability,
            conditions.wind_speed_10m,
            conditions.wind_direction_10m,
            conditions.wind_to_shore_angle_degrees,
            conditions.wind_gusts_10m,
            conditions.precipitation,
            conditions.cloud_cover,
            conditions.air_temperature,
            conditions.apparent_temperature,
            conditions.pressure_snapshot_id,
            conditions.pressure_msl,
            conditions.weather_status,
            conditions.wave_snapshot_id,
            conditions.wave_height,
            conditions.wave_direction,
            conditions.wave_to_shore_angle_degrees,
            conditions.wave_period,
            conditions.wave_status,
            conditions.sst_snapshot_id,
            conditions.sea_surface_temperature,
            conditions.sst_status,
            conditions.tide_snapshot_id,
            conditions.tide_phase,
            conditions.tide_previous_extremum_time,
            conditions.tide_previous_extremum_type,
            conditions.tide_previous_predicted_water_level,
            conditions.tide_next_extremum_time,
            conditions.tide_next_extremum_type,
            conditions.tide_next_predicted_water_level,
            conditions.tide_minutes_since_previous_extremum,
            conditions.tide_minutes_until_next_extremum,
            conditions.tide_predicted_range,
            conditions.tide_status,
            conditions.sunrise,
            conditions.sunset,
            conditions.solar_state,
            conditions.minutes_from_sunrise,
            conditions.minutes_from_sunset,
            locations.fishing_context,
            solar_context.display_timezone
        from coastal_conditions_hourly as conditions
        left join run_locations as locations
            on locations.run_id = conditions.run_id
            and locations.location_id = conditions.location_id
        left join run_location_solar_context as solar_context
            on solar_context.run_id = conditions.run_id
            and solar_context.location_id = conditions.location_id
        where conditions.run_id = ? and conditions.forecast_time >= ?
        order by conditions.location_id, conditions.forecast_time
        """,
        [run_id, started_at],
    )
    columns = [description[0] for description in cursor.description]
    conditions = []
    for row in cursor.fetchall():
        values = dict(zip(columns, row, strict=True))
        score_input = SpanishMackerelConditionsInput(
            run_id=values["run_id"],
            location_id=values["location_id"],
            fishing_context=values["fishing_context"],
            forecast_time=values["forecast_time"],
            display_timezone=values["display_timezone"],
            weather_status=values["weather_status"],
            wave_status=values["wave_status"],
            sst_status=values["sst_status"],
            wind_speed_10m=values["wind_speed_10m"],
            wind_gusts_10m=values["wind_gusts_10m"],
            wave_height=values["wave_height"],
            sea_surface_temperature=values["sea_surface_temperature"],
        )
        condition = {
            column: _json_value(values[column])
            for column in columns
            if column not in {"fishing_context", "display_timezone"}
        }
        condition["spanish_mackerel_conditions"] = _score_projection(score_input)
        conditions.append(condition)
    return conditions


def _dashboard_payloads(
    connection: duckdb.DuckDBPyConnection,
    config: dict[str, Any],
    generated_at: datetime,
) -> dict[str, object]:
    latest_attempt = connection.execute(
        """
        select run_id, started_at, completed_at, status, rows_loaded
        from pipeline_runs
        order by started_at desc, run_id desc
        limit 1
        """
    ).fetchone()
    latest_success = connection.execute(
        """
        select run_id, started_at, completed_at, status, rows_loaded
        from pipeline_runs
        where status = 'success' and completed_at is not null
        order by started_at desc, run_id desc
        limit 1
        """
    ).fetchone()
    if latest_success is None:
        raise ValueError("no completed successful pipeline run found")

    run_id, started_at, completed_at, _, _ = latest_success
    window_start, window_end = connection.execute(
        """
        select min(forecast_time), max(forecast_time)
        from coastal_conditions_hourly
        where run_id = ? and forecast_time >= ?
        """,
        [run_id, started_at],
    ).fetchone()
    conditions = _dashboard_conditions(connection, run_id, started_at)
    history = []
    if window_start is not None and window_end is not None:
        history = _query(
            connection,
            """
            with recent_runs as (
                select run_id
                from pipeline_runs
                order by started_at desc, run_id desc
                limit 20
            )
            select
                conditions.run_id,
                conditions.run_started_at,
                conditions.location_id,
                conditions.forecast_time,
                conditions.wind_speed_10m,
                conditions.wind_direction_10m,
                conditions.wind_to_shore_angle_degrees,
                conditions.wind_gusts_10m,
                conditions.wave_height,
                conditions.wave_direction,
                conditions.wave_to_shore_angle_degrees,
                conditions.wave_period,
                conditions.sea_surface_temperature,
                conditions.tide_phase,
                conditions.tide_predicted_range
            from coastal_conditions_hourly as conditions
            inner join recent_runs
                on recent_runs.run_id = conditions.run_id
            where conditions.forecast_time between ? and ?
            order by
                conditions.location_id,
                conditions.forecast_time,
                conditions.run_started_at,
                conditions.run_id
            """,
            [window_start, window_end],
        )

    pipeline_runs = _query(
        connection,
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
            case
                when recent_runs.completed_at is null then null
                else greatest(
                    date_diff(
                        'second',
                        recent_runs.started_at,
                        recent_runs.completed_at
                    ),
                    0
                )
            end as duration_seconds,
            recent_runs.rows_loaded,
            count(forecast_snapshots.snapshot_id) as snapshot_count,
            recent_runs.status = 'failed' and recent_runs.rows_loaded > 0
                as partial_data
        from recent_runs
        left join forecast_snapshots
            on forecast_snapshots.run_id = recent_runs.run_id
        group by all
        order by recent_runs.started_at desc, recent_runs.run_id desc
        """,
    )
    source_summary = _query(
        connection,
        """
        with recent_runs as (
            select run_id, started_at
            from pipeline_runs
            order by started_at desc, run_id desc
            limit 20
        ),
        pressure_introduction as (
            select min(runs.started_at) as started_at
            from source_results as results
            inner join pipeline_runs as runs on runs.run_id = results.run_id
            where results.source = 'pressure'
        ),
        expected as (
            select
                recent_runs.run_id,
                run_locations.location_id,
                sources.source
            from recent_runs
            inner join run_locations
                on run_locations.run_id = recent_runs.run_id
            cross join (
                values ('weather'), ('pressure'), ('wave'), ('sst'), ('tide')
            ) as sources(source)
            cross join pressure_introduction
            where sources.source != 'pressure'
                or recent_runs.started_at >= pressure_introduction.started_at
        )
        select
            expected.source,
            sum(case when results.status = 'success' then 1 else 0 end)::integer
                as success_count,
            sum(
                case
                    when results.status is not null
                        and results.status != 'success'
                    then 1
                    else 0
                end
            )::integer as failure_count,
            sum(case when results.status is null then 1 else 0 end)::integer
                as missing_count,
            round(
                sum(case when results.status = 'success' then 1 else 0 end)
                    * 100.0 / count(*),
                1
            ) as success_rate_percent
        from expected
        left join source_results as results
            on results.run_id = expected.run_id
            and results.location_id = expected.location_id
            and results.source = expected.source
        group by expected.source
        order by expected.source
        """,
    )
    source_coverage = _query(
        connection,
        """
        with recent_runs as (
            select run_id, started_at
            from pipeline_runs
            order by started_at desc, run_id desc
            limit 20
        ),
        pressure_introduction as (
            select min(runs.started_at) as started_at
            from source_results as results
            inner join pipeline_runs as runs on runs.run_id = results.run_id
            where results.source = 'pressure'
        ),
        expected as (
            select
                recent_runs.run_id,
                recent_runs.started_at as run_started_at,
                run_locations.location_id,
                sources.source
            from recent_runs
            inner join run_locations
                on run_locations.run_id = recent_runs.run_id
            cross join (
                values ('weather'), ('pressure'), ('wave'), ('sst'), ('tide')
            ) as sources(source)
            cross join pressure_introduction
            where sources.source != 'pressure'
                or recent_runs.started_at >= pressure_introduction.started_at
        )
        select
            expected.run_id,
            expected.run_started_at,
            expected.location_id,
            expected.source,
            coalesce(results.status, 'not_recorded') as status
        from expected
        left join source_results as results
            on results.run_id = expected.run_id
            and results.location_id = expected.location_id
            and results.source = expected.source
        order by
            expected.run_started_at desc,
            expected.run_id desc,
            expected.location_id,
            expected.source
        """,
    )
    source_failures = _query(
        connection,
        """
        with recent_runs as (
            select run_id
            from pipeline_runs
            order by started_at desc, run_id desc
            limit 20
        )
        select
            results.run_id,
            results.location_id,
            results.source,
            results.status,
            results.recorded_at
        from source_results as results
        inner join recent_runs
            on recent_runs.run_id = results.run_id
        where results.status != 'success'
        order by results.recorded_at desc, results.run_id desc
        """,
    )
    observation_attempt = _query(
        connection,
        """select source, attempted_at, status, new_review_patterns,
        previously_seen_review_patterns, outstanding_review_patterns
        from fishing_observation_ingestion_attempts
        order by attempted_at desc, attempt_id desc limit 1""",
    )
    observation_attempts = _query(
        connection,
        """select source, attempted_at, status, new_review_patterns,
        previously_seen_review_patterns, outstanding_review_patterns
        from fishing_observation_ingestion_attempts
        qualify row_number() over (
            partition by source order by attempted_at desc, attempt_id desc
        ) = 1
        order by source""",
    )
    observation_patterns = _query(
        connection,
        """select pattern.pattern_id, pattern.source, pattern.raw_segment, pattern.reason,
        count(candidate.candidate_id)::integer as occurrence_count,
        min(candidate.report_id) as report_id,
        arg_min(report.report_time_text, candidate.report_id) as report_time_text
        from fishing_observation_review_patterns as pattern
        inner join fishing_observation_review_candidate_patterns as linked
            using (pattern_id)
        inner join fishing_observation_review_candidates as candidate
            using (candidate_id)
        inner join fishing_observation_reports as report using (report_id)
        where pattern.disposition is null
        group by pattern.pattern_id, pattern.source, pattern.raw_segment, pattern.reason
        order by pattern.pattern_id
        limit 20""",
    )
    provenance = _query(
        connection,
        """
        with selected_run as (
            select started_at
            from pipeline_runs
            where run_id = ?
        ),
        pressure_introduction as (
            select min(runs.started_at) as started_at
            from source_results as results
            inner join pipeline_runs as runs on runs.run_id = results.run_id
            where results.source = 'pressure'
        ),
        expected_sources as (
            select *
            from (values
                ('weather', 1),
                ('pressure', 2),
                ('wave', 3),
                ('sst', 4),
                ('tide', 5)
            ) as sources(source, source_order)
            cross join selected_run
            cross join pressure_introduction
            where sources.source != 'pressure'
                or selected_run.started_at >= pressure_introduction.started_at
        ),
        snapshot_references as (
            select distinct location_id, 'weather' as source,
                weather_snapshot_id as snapshot_id
            from coastal_conditions_hourly
            where run_id = ? and weather_snapshot_id is not null
            union all
            select distinct location_id, 'wave', wave_snapshot_id
            from coastal_conditions_hourly
            where run_id = ? and wave_snapshot_id is not null
            union all
            select distinct location_id, 'pressure', pressure_snapshot_id
            from coastal_conditions_hourly
            where run_id = ? and pressure_snapshot_id is not null
            union all
            select distinct location_id, 'sst', sst_snapshot_id
            from coastal_conditions_hourly
            where run_id = ? and sst_snapshot_id is not null
            union all
            select distinct location_id, 'tide', tide_snapshot_id
            from coastal_conditions_hourly
            where run_id = ? and tide_snapshot_id is not null
        )
        select
            run_locations.location_id,
            run_locations.fishing_context,
            run_locations.shore_normal_azimuth_degrees,
            run_locations.pier_seaward_azimuth_degrees,
            run_locations.orientation_method,
            run_locations.orientation_source,
            run_locations.orientation_reviewed_at,
            run_locations.orientation_limitation,
            expected_sources.source,
            snapshot_refs.snapshot_id,
            snapshots.captured_at,
            snapshots.model_selector,
            snapshots.request_latitude,
            snapshots.request_longitude,
            snapshots.returned_latitude,
            snapshots.returned_longitude,
            tides.station_id,
            tides.prediction_location,
            tides.relationship_type,
            tides.reference_station,
            tides.product,
            tides.interval,
            tides.datum,
            tides.time_zone,
            tides.units,
            tides.response_format,
            tides.request_begin_date,
            tides.request_end_date,
            tides.subordinate_station_type,
            tides.high_time_offset_minutes,
            tides.low_time_offset_minutes,
            tides.high_multiplier,
            tides.low_multiplier,
            tides.height_offset_high_tide,
            tides.height_offset_low_tide,
            tides.height_adjusted_type,
            tides.distance_km,
            tides.coastal_relationship,
            tides.known_limitation
        from run_locations
        cross join expected_sources
        left join snapshot_references as snapshot_refs
            on snapshot_refs.location_id = run_locations.location_id
            and snapshot_refs.source = expected_sources.source
        left join forecast_snapshots as snapshots
            on snapshots.snapshot_id = snapshot_refs.snapshot_id
        left join tide_snapshots as tides
            on tides.snapshot_id = snapshot_refs.snapshot_id
        where run_locations.run_id = ?
        order by
            run_locations.location_id,
            expected_sources.source_order,
            snapshot_refs.snapshot_id
        """,
        [run_id, run_id, run_id, run_id, run_id, run_id, run_id],
    )

    freshness_minutes = max(
        int((generated_at - completed_at).total_seconds() // 60),
        0,
    )
    manifest = {
        "schema_version": 4,
        "generated_at": _json_value(generated_at),
        "display_timezone": config["display_timezone"],
        "latest_attempt": (
            _run_record(latest_attempt) if latest_attempt is not None else None
        ),
        "latest_success": _run_record(latest_success),
        "latest_success_freshness_minutes": freshness_minutes,
        "forecast_window": {
            "start": _json_value(window_start),
            "end": _json_value(window_end),
        },
        "location_count": len(config["locations"]),
        "source_count": len(_SOURCES),
    }
    locations = [
        {
            "location_id": location["id"],
            "name": location["name"],
            "fishing_context": location["fishing_context"],
        }
        for location in config["locations"]
    ]
    return {
        "manifest.json": manifest,
        "locations.json": locations,
        "conditions.json": conditions,
        "forecast-history.json": history,
        "pipeline-runs.json": pipeline_runs,
        "source-health.json": {
            "summary": source_summary,
            "coverage": source_coverage,
            "failures": source_failures,
        },
        "observation-health.json": {
            "latest_attempt": observation_attempt[0] if observation_attempt else None,
            "latest_attempts": observation_attempts,
            "outstanding_patterns": observation_patterns,
        },
        "provenance.json": provenance,
    }


def export_dashboard_data(
    config: dict[str, Any],
    output_directory: Path | str,
    generated_at: datetime | None = None,
) -> None:
    database_path = Path(config["storage"]["database_path"])
    if not database_path.is_file():
        raise ValueError(f"database does not exist: {database_path}")

    generated_at = generated_at or datetime.now(timezone.utc)
    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("generated_at must include timezone information")

    try:
        with duckdb.connect(str(database_path), read_only=True) as connection:
            connection.execute("set TimeZone = 'UTC'")
            validate_dashboard_score_schema(connection)
            payloads = _dashboard_payloads(connection, config, generated_at)
    except ReportSchemaError as exc:
        raise DashboardSchemaError(
            "dashboard export requires a current SaltBytes database schema"
        ) from exc
    except duckdb.Error as exc:
        raise DashboardSchemaError(
            "dashboard export could not read the current SaltBytes database schema"
        ) from exc

    if tuple(payloads) != _EXPORT_FILES:
        raise RuntimeError("dashboard export file contract is inconsistent")

    output_path = Path(output_directory)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(
            f"could not create dashboard output directory: {output_path}"
        ) from exc
    if not output_path.is_dir():
        raise ValueError(f"dashboard output path must be a directory: {output_path}")

    for filename, payload in payloads.items():
        _write_json(output_path / filename, payload)
