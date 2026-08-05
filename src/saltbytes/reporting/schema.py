import duckdb


class ReportSchemaError(ValueError):
    pass


_REQUIRED_REPORT_SCHEMA = {
    "pipeline_runs": (
        "run_id",
        "started_at",
        "completed_at",
        "status",
        "rows_loaded",
        "error_message",
    ),
    "forecast_snapshots": (
        "snapshot_id",
        "run_id",
    ),
    "source_results": (
        "run_id",
        "location_id",
        "source",
        "status",
        "detail",
        "recorded_at",
    ),
    "run_locations": (
        "run_id",
        "location_id",
        "fishing_context",
        "shore_normal_azimuth_degrees",
        "pier_seaward_azimuth_degrees",
        "orientation_method",
        "orientation_source",
        "orientation_reviewed_at",
        "orientation_limitation",
    ),
    "coastal_conditions_hourly": (
        "run_id",
        "run_started_at",
        "location_id",
        "forecast_time",
        "shore_normal_azimuth_degrees",
        "weather_snapshot_id",
        "precipitation_probability",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_to_shore_angle_degrees",
        "wind_gusts_10m",
        "precipitation",
        "wave_snapshot_id",
        "wave_height",
        "wave_direction",
        "wave_to_shore_angle_degrees",
        "wave_period",
        "sst_snapshot_id",
        "sea_surface_temperature",
        "tide_snapshot_id",
        "tide_phase",
        "tide_previous_extremum_time",
        "tide_previous_extremum_type",
        "tide_previous_predicted_water_level",
        "tide_next_extremum_time",
        "tide_next_extremum_type",
        "tide_next_predicted_water_level",
        "tide_predicted_range",
    ),
}

_REQUIRED_DASHBOARD_SCORE_SCHEMA = {
    "run_location_solar_context": (
        "run_id",
        "location_id",
        "display_timezone",
    ),
    "coastal_conditions_hourly": (
        "weather_status",
        "wave_status",
        "sst_status",
    ),
}


def validate_report_schema(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    rows = connection.execute(
        """
        select table_name, column_name
        from information_schema.columns
        where table_schema = 'main'
        """
    ).fetchall()

    columns_by_relation: dict[str, set[str]] = {}

    for relation, column in rows:
        columns_by_relation.setdefault(
            relation,
            set(),
        ).add(column)

    missing = []

    for relation, required_columns in (
        _REQUIRED_REPORT_SCHEMA.items()
    ):
        available_columns = columns_by_relation.get(
            relation
        )

        if available_columns is None:
            missing.append(relation)
            continue

        missing.extend(
            f"{relation}.{column}"
            for column in required_columns
            if column not in available_columns
        )

    if missing:
        raise ReportSchemaError(
            "HTML reporting requires a current "
            "SaltBytes database schema.\n"
            f"Missing: {', '.join(missing)}\n"
            "Run ingestion with the current code or "
            "restore a current database before retrying."
        )


def validate_dashboard_score_schema(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """Validate the extra persisted fields needed by dashboard score export."""
    validate_report_schema(connection)
    rows = connection.execute(
        """
        select table_name, column_name
        from information_schema.columns
        where table_schema = 'main'
        """
    ).fetchall()
    columns_by_relation: dict[str, set[str]] = {}
    for relation, column in rows:
        columns_by_relation.setdefault(relation, set()).add(column)

    missing = []
    for relation, required_columns in _REQUIRED_DASHBOARD_SCORE_SCHEMA.items():
        available = columns_by_relation.get(relation)
        if available is None:
            missing.append(relation)
            continue
        missing.extend(
            f"{relation}.{column}"
            for column in required_columns
            if column not in available
        )

    if missing:
        raise ReportSchemaError(
            "Dashboard score export requires a current SaltBytes database schema.\n"
            f"Missing: {', '.join(missing)}\n"
            "Run ingestion with the current code or restore a current database before retrying."
        )
