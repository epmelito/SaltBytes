import math
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def _sst_coordinate_is_usable(value: Any) -> bool:
    if not isinstance(value, dict):
        return False

    latitude = value.get("latitude")
    longitude = value.get("longitude")

    return (
        not isinstance(latitude, bool)
        and isinstance(latitude, int | float)
        and -90 <= latitude <= 90
        and not isinstance(longitude, bool)
        and isinstance(longitude, int | float)
        and -180 <= longitude <= 180
    )


# validate location-specific SST prerequisites before fetching the source
def run_sst_preflight_checks(
    location: dict[str, Any],
) -> list[dict[str, str | datetime]]:
    checked_at = datetime.now(timezone.utc)
    sst_config = location.get("sst")
    relationship_present = isinstance(sst_config, dict)
    relationship = sst_config if relationship_present else {}
    request_coordinate = relationship.get("request_coordinate")
    expected_returned_coordinate = relationship.get(
        "expected_returned_coordinate"
    )
    coastal_regime = relationship.get("coastal_regime")
    coastal_regime_present = (
        isinstance(coastal_regime, str) and bool(coastal_regime.strip())
    )

    return [
        _quality_result(
            "sst",
            "relationship_present",
            relationship_present,
            type(sst_config).__name__,
            "dict",
            checked_at,
        ),
        _quality_result(
            "sst",
            "request_coordinate_usable",
            _sst_coordinate_is_usable(request_coordinate),
            request_coordinate,
            "numeric latitude and longitude in range",
            checked_at,
        ),
        _quality_result(
            "sst",
            "expected_returned_coordinate_usable",
            _sst_coordinate_is_usable(expected_returned_coordinate),
            expected_returned_coordinate,
            "numeric latitude and longitude in range",
            checked_at,
        ),
        _quality_result(
            "sst",
            "coastal_regime_present",
            coastal_regime_present,
            coastal_regime,
            "nonempty string",
            checked_at,
        ),
    ]


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


# validate location-specific tide prerequisites before fetching the source
def run_tide_preflight_checks(
    location: dict[str, Any],
    tide_api_config: dict[str, Any],
) -> list[dict[str, str | datetime]]:
    checked_at = datetime.now(timezone.utc)
    tide_config = location.get("tide")
    relationship_present = isinstance(tide_config, dict)
    relationship = tide_config if relationship_present else {}
    relationship_type = relationship.get("relationship_type")
    reference_station = relationship.get("reference_station")
    subordinate_values = (
        relationship.get("high_time_offset_minutes"),
        relationship.get("low_time_offset_minutes"),
        relationship.get("high_multiplier"),
        relationship.get("low_multiplier"),
    )
    nullable_metadata_present = all(
        field_name in relationship
        for field_name in (
            "reference_station",
            "high_time_offset_minutes",
            "low_time_offset_minutes",
            "high_multiplier",
            "low_multiplier",
        )
    )
    subordinate_metadata_usable = nullable_metadata_present and (
        (
            reference_station is None
            and all(value is None for value in subordinate_values)
        )
        or (
            _is_nonempty_string(reference_station)
            and all(
                _is_finite_number(value)
                for value in subordinate_values
            )
        )
    )
    required_metadata_present = all(
        field_name in relationship
        for field_name in (
            "prediction_location",
            "relationship_type",
            "distance_km",
            "coastal_relationship",
            "known_limitation",
        )
    )
    relationship_metadata_usable = (
        required_metadata_present
        and _is_nonempty_string(relationship.get("prediction_location"))
        and relationship_type in {"direct", "transfer"}
        and _is_finite_number(relationship.get("distance_km"))
        and float(relationship["distance_km"]) >= 0
        and _is_nonempty_string(
            relationship.get("coastal_relationship")
        )
        and _is_nonempty_string(relationship.get("known_limitation"))
        and subordinate_metadata_usable
    )
    results = [
        _quality_result(
            "tide",
            "relationship_present",
            relationship_present,
            type(tide_config).__name__,
            "dict",
            checked_at,
        ),
        _quality_result(
            "tide",
            "station_id_present",
            _is_nonempty_string(relationship.get("station_id")),
            relationship.get("station_id"),
            "nonempty string",
            checked_at,
        ),
        _quality_result(
            "tide",
            "relationship_metadata_usable",
            relationship_metadata_usable,
            relationship,
            "accepted direct or transfer relationship metadata",
            checked_at,
        ),
    ]

    for field_name, expected_value in EXPECTED_TIDE_REQUEST.items():
        results.append(
            _quality_result(
                "tide",
                f"configured_{field_name}",
                tide_api_config.get(field_name) == expected_value,
                tide_api_config.get(field_name),
                expected_value,
                checked_at,
            )
        )

    results.append(
        _quality_result(
            "tide",
            "configured_forecast_days",
            tide_api_config.get("forecast_days") == 7,
            tide_api_config.get("forecast_days"),
            7,
            checked_at,
        )
    )

    return results


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
    model_selector: str,
    expected_returned_coordinate: dict[str, Any],
    expected_model_selector: str = "ncep_nbm_conus",
    source_label: str = "weather",
) -> list[dict[str, str | datetime]]:
    if source_label not in VALID_SOURCE_LABELS:
        raise ValueError(f"unsupported quality source label: {source_label}")

    checked_at = datetime.now(timezone.utc)
    results: list[dict[str, str | datetime]] = []

    results.append(
        _quality_result(
            source_label,
            "configured_model_selector",
            model_selector == expected_model_selector,
            model_selector,
            expected_model_selector,
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
                source_label,
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
            source_label,
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
            source_label,
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
            source_label,
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
                normalized_times,
                normalized_times[1:],
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

    for field_name in expected_hourly_fields:
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

    return results
