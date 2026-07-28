from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

REQUIRED_MODEL = "ncep_nbm_conus"
EXPECTED_HOURLY_INSTANTS = 168


def _quality_result(
    check_name: str,
    passed: bool,
    observed_value: Any,
    expected_value: Any,
    checked_at: datetime,
) -> dict[str, str | datetime]:
    return {
        "check_name": check_name,
        "status": "pass" if passed else "fail",
        "observed_value": str(observed_value),
        "expected_value": str(expected_value),
        "checked_at": checked_at,
    }


def _parse_coordinate(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# validate one configured atmospheric result before storage
def run_payload_quality_checks(
    payload: dict[str, Any],
    expected_hourly_fields: list[str],
    model_selector: str,
    expected_returned_coordinate: dict[str, Any],
) -> list[dict[str, str | datetime]]:
    checked_at = datetime.now(timezone.utc)
    results: list[dict[str, str | datetime]] = []

    results.append(
        _quality_result(
            "configured_model_selector",
            model_selector == REQUIRED_MODEL,
            model_selector,
            REQUIRED_MODEL,
            checked_at,
        )
    )

    for coordinate_name in ("latitude", "longitude"):
        returned_coordinate = _parse_coordinate(payload.get(coordinate_name))
        expected_coordinate = _parse_coordinate(
            expected_returned_coordinate.get(coordinate_name)
        )
        coordinates_match = (
            returned_coordinate is not None
            and expected_coordinate is not None
            and returned_coordinate == expected_coordinate
        )

        results.append(
            _quality_result(
                f"returned_{coordinate_name}_matches_expected",
                coordinates_match,
                returned_coordinate,
                expected_coordinate,
                checked_at,
            )
        )

    timezone_name = payload.get("timezone")
    response_timezone: ZoneInfo | None = None

    if isinstance(timezone_name, str) and timezone_name:
        try:
            response_timezone = ZoneInfo(timezone_name)
        except (ValueError, ZoneInfoNotFoundError):
            pass

    results.append(
        _quality_result(
            "response_timezone_valid",
            response_timezone is not None,
            timezone_name,
            "recognized IANA timezone",
            checked_at,
        )
    )

    hourly = payload.get("hourly")
    hourly_exists = isinstance(hourly, dict)
    results.append(
        _quality_result(
            "hourly_mapping_exists",
            hourly_exists,
            type(hourly).__name__,
            "dict",
            checked_at,
        )
    )

    if not hourly_exists:
        return results

    forecast_times = hourly.get("time")
    time_values = forecast_times if isinstance(forecast_times, list) else []
    results.append(
        _quality_result(
            "hourly_time_count",
            len(time_values) == EXPECTED_HOURLY_INSTANTS,
            len(time_values),
            EXPECTED_HOURLY_INSTANTS,
            checked_at,
        )
    )

    parsed_times: list[datetime] = []
    times_parseable = isinstance(forecast_times, list)

    if times_parseable:
        for value in time_values:
            if not isinstance(value, str):
                times_parseable = False
                break

            try:
                parsed_times.append(datetime.fromisoformat(value))
            except ValueError:
                times_parseable = False
                break

    results.append(
        _quality_result(
            "hourly_times_parseable",
            times_parseable,
            len(parsed_times),
            len(time_values),
            checked_at,
        )
    )

    normalized_times: list[datetime] = []
    times_normalized = times_parseable and response_timezone is not None

    if times_normalized:
        try:
            for parsed_time in parsed_times:
                if parsed_time.tzinfo is None:
                    parsed_time = parsed_time.replace(
                        tzinfo=response_timezone
                    )

                normalized_times.append(
                    parsed_time.astimezone(timezone.utc)
                )
        except (OverflowError, ValueError):
            times_normalized = False
            normalized_times = []

    results.append(
        _quality_result(
            "hourly_times_normalized_to_utc",
            times_normalized,
            len(normalized_times),
            len(time_values),
            checked_at,
        )
    )

    unique_time_count = len(set(normalized_times))
    results.append(
        _quality_result(
            "hourly_utc_time_count",
            times_normalized
            and unique_time_count == EXPECTED_HOURLY_INSTANTS,
            unique_time_count,
            EXPECTED_HOURLY_INSTANTS,
            checked_at,
        )
    )

    strictly_ascending = (
        times_normalized
        and len(normalized_times) == EXPECTED_HOURLY_INSTANTS
        and all(
            earlier < later
            for earlier, later in zip(
                normalized_times,
                normalized_times[1:],
                strict=False,
            )
        )
    )
    results.append(
        _quality_result(
            "hourly_utc_times_strictly_ascending",
            strictly_ascending,
            strictly_ascending,
            True,
            checked_at,
        )
    )

    hourly_spacing = (
        strictly_ascending
        and all(
            later - earlier == timedelta(hours=1)
            for earlier, later in zip(
                normalized_times,
                normalized_times[1:],
                strict=False,
            )
        )
    )
    results.append(
        _quality_result(
            "hourly_utc_spacing",
            hourly_spacing,
            hourly_spacing,
            True,
            checked_at,
        )
    )

    for field_name in expected_hourly_fields:
        field_exists = field_name in hourly
        values = hourly.get(field_name)
        values_are_list = isinstance(values, list)
        value_count = len(values) if values_are_list else 0

        results.append(
            _quality_result(
                f"{field_name}_exists",
                field_exists,
                field_exists,
                True,
                checked_at,
            )
        )
        results.append(
            _quality_result(
                f"{field_name}_count",
                values_are_list
                and value_count == EXPECTED_HOURLY_INSTANTS,
                value_count,
                EXPECTED_HOURLY_INSTANTS,
                checked_at,
            )
        )

        values_without_nulls = (
            values_are_list
            and value_count == EXPECTED_HOURLY_INSTANTS
            and all(value is not None for value in values)
        )
        results.append(
            _quality_result(
                f"{field_name}_has_no_nulls",
                values_without_nulls,
                values_without_nulls,
                True,
                checked_at,
            )
        )

        values_are_numeric = (
            values_are_list
            and value_count == EXPECTED_HOURLY_INSTANTS
            and all(
                not isinstance(value, bool)
                and isinstance(value, int | float)
                for value in values
            )
        )
        results.append(
            _quality_result(
                f"{field_name}_values_are_numeric",
                values_are_numeric,
                values_are_numeric,
                True,
                checked_at,
            )
        )

    return results
