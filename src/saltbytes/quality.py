import math
from datetime import datetime, timedelta, timezone
from typing import Any

EXPECTED_HOURLY_INSTANTS = 168
VALID_SOURCE_LABELS = {"weather", "wave", "sst"}
EXPECTED_TIDE_REQUEST = {
    "product": "predictions",
    "interval": "hilo",
    "datum": "MLLW",
    "time_zone": "gmt",
    "units": "metric",
    "format": "json",
}


def _quality_result(
    source_label: str,
    check_name: str,
    passed: bool,
    observed_value: Any,
    expected_value: Any,
    checked_at: datetime,
) -> dict[str, str | datetime]:
    return {
        "check_name": f"{source_label}:{check_name}",
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


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, int | float)
        and math.isfinite(float(value))
    )


# build the independent seven-day hourly UTC tide phase timeline
def build_tide_forecast_times(
    forecast_start: datetime,
    forecast_days: int,
) -> list[datetime]:
    if forecast_start.tzinfo is None or forecast_start.utcoffset() is None:
        raise ValueError("forecast_start must include timezone information")

    start = forecast_start.astimezone(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    return [
        start + timedelta(hours=index)
        for index in range(forecast_days * 24)
    ]


def normalize_tide_events(
    payload: dict[str, Any],
) -> list[dict[str, str | float | datetime]]:
    predictions = payload.get("predictions")

    if not isinstance(predictions, list):
        raise ValueError("tide payload must contain a predictions list")

    events: list[dict[str, str | float | datetime]] = []

    for prediction in predictions:
        if not isinstance(prediction, dict):
            raise ValueError("each tide prediction must be a mapping")

        event_time_value = prediction.get("t")
        event_value = prediction.get("v")
        event_type_value = prediction.get("type")

        if not _is_nonempty_string(event_time_value):
            raise ValueError("each tide prediction must contain a time")

        try:
            event_time = datetime.strptime(
                event_time_value,
                "%Y-%m-%d %H:%M",
            ).replace(tzinfo=timezone.utc)
        except ValueError as error:
            raise ValueError(
                f"invalid tide prediction time: {event_time_value}"
            ) from error

        if isinstance(event_value, bool):
            raise ValueError("tide prediction value must be numeric")

        try:
            predicted_water_level = float(event_value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "tide prediction value must be numeric"
            ) from error

        if not math.isfinite(predicted_water_level):
            raise ValueError("tide prediction value must be finite")

        if event_type_value not in {"H", "L"}:
            raise ValueError("tide prediction type must be H or L")

        events.append(
            {
                "event_time": event_time,
                "event_type": (
                    "high" if event_type_value == "H" else "low"
                ),
                "predicted_water_level": predicted_water_level,
            }
        )

    return events


def derive_tide_phases(
    events: list[dict[str, str | float | datetime]],
    forecast_times: list[datetime],
) -> list[dict[str, str | datetime]]:
    phases: list[dict[str, str | datetime]] = []
    event_index = 0

    for forecast_time in forecast_times:
        while (
            event_index + 1 < len(events)
            and events[event_index + 1]["event_time"] <= forecast_time
        ):
            event_index += 1

        if event_index + 1 >= len(events):
            raise ValueError(
                f"tide valid time lacks a following extremum: {forecast_time}"
            )

        preceding_event = events[event_index]
        following_event = events[event_index + 1]
        preceding_time = preceding_event["event_time"]
        following_time = following_event["event_time"]

        if not (
            isinstance(preceding_time, datetime)
            and isinstance(following_time, datetime)
            and preceding_time <= forecast_time < following_time
        ):
            raise ValueError(
                f"tide valid time lacks a preceding extremum: {forecast_time}"
            )

        event_pair = (
            preceding_event["event_type"],
            following_event["event_type"],
        )

        if event_pair == ("low", "high"):
            phase = "rising"
        elif event_pair == ("high", "low"):
            phase = "falling"
        else:
            raise ValueError(
                f"tide events do not alternate around {forecast_time}"
            )

        phases.append(
            {
                "forecast_time": forecast_time,
                "phase": phase,
            }
        )

    return phases


# validate one NOAA tide result and its retained request provenance
def run_tide_quality_checks(
    payload: dict[str, Any],
    request_provenance: dict[str, Any],
    forecast_times: list[datetime],
) -> list[dict[str, str | datetime]]:
    checked_at = datetime.now(timezone.utc)
    results: list[dict[str, str | datetime]] = []

    station_id = request_provenance.get("station")
    results.append(
        _quality_result(
            "tide",
            "request_station_present",
            _is_nonempty_string(station_id),
            station_id,
            "nonempty string",
            checked_at,
        )
    )

    for field_name, expected_value in EXPECTED_TIDE_REQUEST.items():
        results.append(
            _quality_result(
                "tide",
                f"request_{field_name}",
                request_provenance.get(field_name) == expected_value,
                request_provenance.get(field_name),
                expected_value,
                checked_at,
            )
        )

    begin_date_value = request_provenance.get("begin_date")
    end_date_value = request_provenance.get("end_date")
    request_window_valid = False

    if (
        _is_nonempty_string(begin_date_value)
        and _is_nonempty_string(end_date_value)
        and forecast_times
        and isinstance(forecast_times[0], datetime)
        and isinstance(forecast_times[-1], datetime)
    ):
        try:
            begin_date = datetime.strptime(
                begin_date_value,
                "%Y%m%d",
            ).date()
            end_date = datetime.strptime(
                end_date_value,
                "%Y%m%d",
            ).date()
        except ValueError:
            pass
        else:
            request_window_valid = (
                begin_date < forecast_times[0].date()
                and end_date > forecast_times[-1].date()
            )

    results.append(
        _quality_result(
            "tide",
            "request_window_bounds_forecast",
            request_window_valid,
            f"{begin_date_value} through {end_date_value}",
            "dates before and after the seven-day forecast timeline",
            checked_at,
        )
    )

    captured_at = request_provenance.get("captured_at")
    captured_at_usable = (
        isinstance(captured_at, datetime)
        and captured_at.tzinfo is not None
        and captured_at.utcoffset() is not None
    )
    results.append(
        _quality_result(
            "tide",
            "request_capture_time_present",
            captured_at_usable,
            captured_at,
            "timezone-aware datetime",
            checked_at,
        )
    )

    try:
        events = normalize_tide_events(payload)
    except ValueError as error:
        events = []
        events_usable = False
        observed_events: Any = str(error)
    else:
        events_usable = bool(events)
        observed_events = len(events)

    results.append(
        _quality_result(
            "tide",
            "prediction_events_usable",
            events_usable,
            observed_events,
            "nonempty time, numeric value, and H or L event list",
            checked_at,
        )
    )

    event_times = [
        event["event_time"]
        for event in events
        if isinstance(event["event_time"], datetime)
    ]
    unique_and_ascending = (
        events_usable
        and len(set(event_times)) == len(event_times)
        and all(
            earlier < later
            for earlier, later in zip(
                event_times,
                event_times[1:],
                strict=False,
            )
        )
    )
    results.append(
        _quality_result(
            "tide",
            "prediction_events_unique_and_ascending",
            unique_and_ascending,
            unique_and_ascending,
            True,
            checked_at,
        )
    )

    alternating = (
        unique_and_ascending
        and all(
            earlier["event_type"] != later["event_type"]
            for earlier, later in zip(
                events,
                events[1:],
                strict=False,
            )
        )
    )
    results.append(
        _quality_result(
            "tide",
            "prediction_events_alternate",
            alternating,
            alternating,
            True,
            checked_at,
        )
    )

    forecast_times_are_utc = all(
        isinstance(forecast_time, datetime)
        and forecast_time.tzinfo is not None
        and forecast_time.utcoffset() == timedelta(0)
        for forecast_time in forecast_times
    )
    timeline_valid = (
        forecast_times_are_utc
        and len(forecast_times) == EXPECTED_HOURLY_INSTANTS
        and len(set(forecast_times)) == EXPECTED_HOURLY_INSTANTS
        and all(
            earlier < later
            and later - earlier == timedelta(hours=1)
            for earlier, later in zip(
                forecast_times,
                forecast_times[1:],
                strict=False,
            )
        )
    )
    results.append(
        _quality_result(
            "tide",
            "forecast_timeline_valid",
            timeline_valid,
            len(forecast_times),
            EXPECTED_HOURLY_INSTANTS,
            checked_at,
        )
    )

    phase_coverage = False

    if alternating and timeline_valid:
        try:
            phases = derive_tide_phases(events, forecast_times)
        except ValueError:
            pass
        else:
            phase_coverage = len(phases) == EXPECTED_HOURLY_INSTANTS

    results.append(
        _quality_result(
            "tide",
            "phase_bounds_complete",
            phase_coverage,
            phase_coverage,
            True,
            checked_at,
        )
    )

    return results


# validate one configured open meteo hourly result before storage
def run_payload_quality_checks(
    payload: dict[str, Any],
    expected_hourly_fields: list[str],
    expected_returned_coordinate: dict[str, Any],
    source_label: str,
    optional_hourly_fields: tuple[str, ...] = (),
) -> list[dict[str, str | datetime]]:
    if source_label not in VALID_SOURCE_LABELS:
        raise ValueError(f"unsupported quality source label: {source_label}")

    checked_at = datetime.now(timezone.utc)
    results: list[dict[str, str | datetime]] = []

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
                source_label,
                f"returned_{coordinate_name}_matches_expected",
                coordinates_match,
                returned_coordinate,
                expected_coordinate,
                checked_at,
            )
        )

    results.append(
        _quality_result(
            source_label,
            "response_timezone_is_gmt",
            payload.get("timezone") == "GMT",
            payload.get("timezone"),
            "GMT",
            checked_at,
        )
    )
    utc_offset_seconds = payload.get("utc_offset_seconds")
    results.append(
        _quality_result(
            source_label,
            "response_utc_offset_seconds_is_zero",
            isinstance(utc_offset_seconds, int | float)
            and not isinstance(utc_offset_seconds, bool)
            and utc_offset_seconds == 0,
            utc_offset_seconds,
            0,
            checked_at,
        )
    )

    hourly = payload.get("hourly")
    hourly_exists = isinstance(hourly, dict)
    results.append(
        _quality_result(
            source_label,
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
            source_label,
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
            source_label,
            "hourly_times_parseable",
            times_parseable,
            len(parsed_times),
            len(time_values),
            checked_at,
        )
    )

    times_are_utc = times_parseable and all(
        parsed_time.tzinfo is None for parsed_time in parsed_times
    )

    results.append(
        _quality_result(
            source_label,
            "hourly_times_are_utc",
            times_are_utc,
            times_are_utc,
            True,
            checked_at,
        )
    )

    unique_time_count = len(set(parsed_times))
    results.append(
        _quality_result(
            source_label,
            "hourly_utc_time_count",
            times_are_utc
            and unique_time_count == EXPECTED_HOURLY_INSTANTS,
            unique_time_count,
            EXPECTED_HOURLY_INSTANTS,
            checked_at,
        )
    )

    strictly_ascending = (
        times_are_utc
        and len(parsed_times) == EXPECTED_HOURLY_INSTANTS
        and all(
            earlier < later
            for earlier, later in zip(
                parsed_times,
                parsed_times[1:],
                strict=False,
            )
        )
    )
    results.append(
        _quality_result(
            source_label,
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
                parsed_times,
                parsed_times[1:],
                strict=False,
            )
        )
    )
    results.append(
        _quality_result(
            source_label,
            "hourly_utc_spacing",
            hourly_spacing,
            hourly_spacing,
            True,
            checked_at,
        )
    )

    field_names = list(expected_hourly_fields)
    field_names.extend(
        field_name
        for field_name in optional_hourly_fields
        if isinstance(hourly.get(field_name), list)
        and len(hourly[field_name]) == EXPECTED_HOURLY_INSTANTS
    )

    for field_name in field_names:
        field_exists = field_name in hourly
        values = hourly.get(field_name)
        values_are_list = isinstance(values, list)
        value_count = len(values) if values_are_list else 0

        results.append(
            _quality_result(
                source_label,
                f"{field_name}_exists",
                field_exists,
                field_exists,
                True,
                checked_at,
            )
        )
        results.append(
            _quality_result(
                source_label,
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
                source_label,
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
                source_label,
                f"{field_name}_values_are_numeric",
                values_are_numeric,
                values_are_numeric,
                True,
                checked_at,
            )
        )

        values_are_finite = values_are_numeric and all(
            math.isfinite(float(value))
            for value in values
        )
        results.append(
            _quality_result(
                source_label,
                f"{field_name}_values_are_finite",
                values_are_finite,
                values_are_finite,
                True,
                checked_at,
            )
        )

        if field_name in {"wind_direction_10m", "wave_direction"}:
            values_are_in_range = values_are_finite and all(
                0 <= float(value) <= 360
                for value in values
            )
            results.append(
                _quality_result(
                    source_label,
                    f"{field_name}_values_are_in_range",
                    values_are_in_range,
                    values_are_in_range,
                    True,
                    checked_at,
                )
            )
        elif field_name == "cloud_cover":
            values_are_in_range = values_are_finite and all(
                0 <= float(value) <= 100
                for value in values
            )
            results.append(
                _quality_result(
                    source_label,
                    "cloud_cover_values_are_in_range",
                    values_are_in_range,
                    values_are_in_range,
                    True,
                    checked_at,
                )
            )

    return results
