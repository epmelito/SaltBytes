from datetime import datetime, timedelta
from typing import Any

import pytest

from forecast_ops.quality import run_payload_quality_checks

REQUIRED_FIELDS = [
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation_probability",
    "precipitation",
]
EXPECTED_COORDINATE = {
    "latitude": 35.89557,
    "longitude": -75.5936,
}


def valid_payload(hour_count: int = 168) -> dict[str, Any]:
    start = datetime(2026, 7, 28)
    times = [
        (start + timedelta(hours=index)).isoformat(timespec="minutes")
        for index in range(hour_count)
    ]

    return {
        "latitude": 35.89557,
        "longitude": -75.5936,
        "timezone": "America/New_York",
        "hourly": {
            "time": times,
            "wind_speed_10m": [10.0] * hour_count,
            "wind_direction_10m": [180.0] * hour_count,
            "wind_gusts_10m": [15.0] * hour_count,
            "precipitation_probability": [20.0] * hour_count,
            "precipitation": [0.0] * hour_count,
        },
    }


def run_checks(
    payload: dict[str, Any],
    model_selector: str = "ncep_nbm_conus",
) -> list[dict[str, Any]]:
    return run_payload_quality_checks(
        payload=payload,
        expected_hourly_fields=REQUIRED_FIELDS,
        model_selector=model_selector,
        expected_returned_coordinate=EXPECTED_COORDINATE,
    )


def result_for(
    results: list[dict[str, Any]],
    check_name: str,
) -> dict[str, Any]:
    return next(
        result
        for result in results
        if result["check_name"] == check_name
    )


def test_valid_168_hour_payload_passes() -> None:
    results = run_checks(valid_payload())

    assert all(result["status"] == "pass" for result in results)


def test_invalid_configured_selector_fails() -> None:
    results = run_checks(valid_payload(), model_selector="auto")

    assert result_for(
        results,
        "configured_model_selector",
    )["status"] == "fail"


@pytest.mark.parametrize("field_name", REQUIRED_FIELDS)
def test_missing_required_field_fails(field_name: str) -> None:
    payload = valid_payload()
    del payload["hourly"][field_name]

    results = run_checks(payload)

    assert result_for(
        results,
        f"{field_name}_exists",
    )["status"] == "fail"


def test_null_required_value_fails() -> None:
    payload = valid_payload()
    payload["hourly"]["precipitation"][12] = None

    results = run_checks(payload)

    assert result_for(
        results,
        "precipitation_has_no_nulls",
    )["status"] == "fail"


def test_nonnumeric_required_value_fails() -> None:
    payload = valid_payload()
    payload["hourly"]["wind_speed_10m"][12] = "fast"

    results = run_checks(payload)

    assert result_for(
        results,
        "wind_speed_10m_values_are_numeric",
    )["status"] == "fail"


@pytest.mark.parametrize(
    ("coordinate_name", "check_name"),
    [
        ("latitude", "returned_latitude_matches_expected"),
        ("longitude", "returned_longitude_matches_expected"),
    ],
)
def test_unexpected_returned_coordinate_fails(
    coordinate_name: str,
    check_name: str,
) -> None:
    payload = valid_payload()
    payload[coordinate_name] = 0

    results = run_checks(payload)

    assert result_for(results, check_name)["status"] == "fail"


def test_coordinate_comparison_uses_parsed_numeric_equality() -> None:
    payload = valid_payload()
    payload["latitude"] = "35.8955700"
    payload["longitude"] = "-75.5936000"

    results = run_checks(payload)

    assert result_for(
        results,
        "returned_latitude_matches_expected",
    )["status"] == "pass"
    assert result_for(
        results,
        "returned_longitude_matches_expected",
    )["status"] == "pass"


def test_boolean_returned_coordinate_fails() -> None:
    payload = valid_payload()
    payload["latitude"] = True

    results = run_checks(payload)

    assert result_for(
        results,
        "returned_latitude_matches_expected",
    )["status"] == "fail"


def test_nonnumeric_returned_coordinate_fails() -> None:
    payload = valid_payload()
    payload["longitude"] = "west"

    results = run_checks(payload)

    assert result_for(
        results,
        "returned_longitude_matches_expected",
    )["status"] == "fail"


def test_required_field_length_mismatch_fails() -> None:
    payload = valid_payload()
    payload["hourly"]["wind_gusts_10m"].pop()

    results = run_checks(payload)

    assert result_for(
        results,
        "wind_gusts_10m_count",
    )["status"] == "fail"


def test_invalid_timezone_fails() -> None:
    payload = valid_payload()
    payload["timezone"] = "Not/A_Timezone"

    results = run_checks(payload)

    assert result_for(
        results,
        "response_timezone_valid",
    )["status"] == "fail"
    assert result_for(
        results,
        "hourly_times_normalized_to_utc",
    )["status"] == "fail"


def test_unparsable_valid_time_fails() -> None:
    payload = valid_payload()
    payload["hourly"]["time"][12] = "not-a-time"

    results = run_checks(payload)

    assert result_for(
        results,
        "hourly_times_parseable",
    )["status"] == "fail"


def test_duplicate_utc_valid_times_fail() -> None:
    payload = valid_payload()
    payload["hourly"]["time"][12] = payload["hourly"]["time"][11]

    results = run_checks(payload)

    assert result_for(
        results,
        "hourly_utc_time_count",
    )["status"] == "fail"


def test_unordered_utc_valid_times_fail() -> None:
    payload = valid_payload()
    times = payload["hourly"]["time"]
    times[12], times[13] = times[13], times[12]

    results = run_checks(payload)

    assert result_for(
        results,
        "hourly_utc_times_strictly_ascending",
    )["status"] == "fail"


def test_non_hourly_utc_spacing_fails() -> None:
    payload = valid_payload()
    payload["hourly"]["time"][12] = "2026-07-28T12:30"

    results = run_checks(payload)

    assert result_for(
        results,
        "hourly_utc_spacing",
    )["status"] == "fail"


@pytest.mark.parametrize("hour_count", [167, 169])
def test_result_requires_exactly_168_utc_instants(
    hour_count: int,
) -> None:
    results = run_checks(valid_payload(hour_count=hour_count))

    assert result_for(
        results,
        "hourly_time_count",
    )["status"] == "fail"
    assert result_for(
        results,
        "hourly_utc_time_count",
    )["status"] == "fail"


def test_missing_hourly_mapping_fails() -> None:
    payload = valid_payload()
    del payload["hourly"]

    results = run_checks(payload)

    assert result_for(
        results,
        "hourly_mapping_exists",
    )["status"] == "fail"
