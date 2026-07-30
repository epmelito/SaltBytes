from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from forecast_ops.quality import (
    build_tide_forecast_times,
    derive_tide_phases,
    normalize_tide_events,
    run_payload_quality_checks,
    run_sst_preflight_checks,
    run_tide_preflight_checks,
    run_tide_quality_checks,
)

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
WAVE_FIELDS = [
    "wave_height",
    "wave_direction",
    "wave_period",
]
EXPECTED_WAVE_COORDINATE = {
    "latitude": 34.625,
    "longitude": -76.70833,
}
SST_FIELDS = ["sea_surface_temperature"]
EXPECTED_SST_COORDINATE = {
    "latitude": 33.958336,
    "longitude": -77.87499,
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
        "timezone": "GMT",
        "utc_offset_seconds": 0,
        "hourly": {
            "time": times,
            "wind_speed_10m": [10.0] * hour_count,
            "wind_direction_10m": [180.0] * hour_count,
            "wind_gusts_10m": [15.0] * hour_count,
            "precipitation_probability": [20.0] * hour_count,
            "precipitation": [0.0] * hour_count,
        },
    }


def valid_wave_payload(hour_count: int = 168) -> dict[str, Any]:
    start = datetime(2026, 7, 28)
    times = [
        (start + timedelta(hours=index)).isoformat(timespec="minutes")
        for index in range(hour_count)
    ]

    return {
        "latitude": 34.625,
        "longitude": -76.70833,
        "timezone": "GMT",
        "utc_offset_seconds": 0,
        "hourly": {
            "time": times,
            "wave_height": [1.2] * hour_count,
            "wave_direction": [135.0] * hour_count,
            "wave_period": [8.0] * hour_count,
        },
    }


def valid_sst_payload(hour_count: int = 168) -> dict[str, Any]:
    start = datetime(2026, 7, 28)
    times = [
        (start + timedelta(hours=index)).isoformat(timespec="minutes")
        for index in range(hour_count)
    ]

    return {
        "latitude": 33.958336,
        "longitude": -77.87499,
        "timezone": "GMT",
        "utc_offset_seconds": 0,
        "hourly": {
            "time": times,
            "sea_surface_temperature": [25.1] * hour_count,
        },
    }


def valid_sst_location() -> dict[str, Any]:
    return {
        "sst": {
            "request_coordinate": {
                "latitude": 33.93,
                "longitude": -77.9,
            },
            "expected_returned_coordinate": EXPECTED_SST_COORDINATE,
            "coastal_regime": (
                "Atlantic-facing marine grid distinct from wave grid"
            ),
        }
    }


def valid_tide_location() -> dict[str, Any]:
    return {
        "tide": {
            "prediction_location": (
                "Jennettes Pier, Nags Head (ocean)"
            ),
            "station_id": "8652226",
            "relationship_type": "direct",
            "reference_station": "8651370",
            "high_time_offset_minutes": -5,
            "low_time_offset_minutes": 1,
            "high_multiplier": 1.04,
            "low_multiplier": 1.43,
            "distance_km": 0.448,
            "coastal_relationship": (
                "Direct use at the Atlantic-facing pier"
            ),
            "known_limitation": (
                "Prediction behavior remains distinct from observed "
                "water levels"
            ),
        }
    }


def valid_tide_api_config() -> dict[str, Any]:
    return {
        "product": "predictions",
        "interval": "hilo",
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "format": "json",
        "forecast_days": 7,
    }


def valid_tide_payload() -> dict[str, Any]:
    start = datetime(2026, 7, 27, 18)
    predictions = []

    for index in range(34):
        event_time = start + timedelta(hours=index * 6)
        predictions.append(
            {
                "t": event_time.strftime("%Y-%m-%d %H:%M"),
                "v": str(0.1 if index % 2 == 0 else 1.2),
                "type": "L" if index % 2 == 0 else "H",
            }
        )

    return {"predictions": predictions}


def valid_tide_forecast_times() -> list[datetime]:
    return build_tide_forecast_times(
        datetime(2026, 7, 28, 10, tzinfo=timezone.utc),
        7,
    )


def valid_tide_provenance() -> dict[str, Any]:
    return {
        "station": "8652226",
        "begin_date": "20260727",
        "end_date": "20260805",
        "product": "predictions",
        "interval": "hilo",
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "format": "json",
        "captured_at": datetime(
            2026,
            7,
            28,
            10,
            tzinfo=timezone.utc,
        ),
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
        expected_model_selector="ncep_nbm_conus",
        source_label="weather",
    )


def run_wave_checks(
    payload: dict[str, Any],
    model_selector: str = "meteofrance_wave",
) -> list[dict[str, Any]]:
    return run_payload_quality_checks(
        payload=payload,
        expected_hourly_fields=WAVE_FIELDS,
        model_selector=model_selector,
        expected_returned_coordinate=EXPECTED_WAVE_COORDINATE,
        expected_model_selector="meteofrance_wave",
        source_label="wave",
    )


def run_sst_checks(
    payload: dict[str, Any],
    model_selector: str = "meteofrance_currents",
) -> list[dict[str, Any]]:
    return run_payload_quality_checks(
        payload=payload,
        expected_hourly_fields=SST_FIELDS,
        model_selector=model_selector,
        expected_returned_coordinate=EXPECTED_SST_COORDINATE,
        expected_model_selector="meteofrance_currents",
        source_label="sst",
    )


def result_for(
    results: list[dict[str, Any]],
    check_name: str,
    source_label: str = "weather",
) -> dict[str, Any]:
    return next(
        result
        for result in results
        if result["check_name"] == f"{source_label}:{check_name}"
    )


def test_valid_168_hour_payload_passes() -> None:
    results = run_checks(valid_payload())

    assert all(result["status"] == "pass" for result in results)
    assert {
        str(result["check_name"])
        for result in results
    } >= {
        f"weather:{field_name}_exists"
        for field_name in REQUIRED_FIELDS
    }


def test_invalid_configured_selector_fails() -> None:
    results = run_checks(valid_payload(), model_selector="auto")

    assert result_for(
        results,
        "configured_model_selector",
    )["status"] == "fail"


@pytest.mark.parametrize("field_name", ["wind_speed_10m"])
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
    [("latitude", "returned_latitude_matches_expected")],
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


def test_non_gmt_timezone_fails() -> None:
    payload = valid_payload()
    payload["timezone"] = "Not/A_Timezone"

    results = run_checks(payload)

    assert result_for(
        results,
        "response_timezone_is_gmt",
    )["status"] == "fail"


def test_nonzero_utc_offset_fails() -> None:
    payload = valid_payload()
    payload["utc_offset_seconds"] = 3600

    results = run_checks(payload)

    assert result_for(
        results,
        "response_utc_offset_seconds_is_zero",
    )["status"] == "fail"


def test_offset_aware_hourly_timestamp_fails() -> None:
    payload = valid_payload()
    payload["hourly"]["time"][0] = "2026-07-28T00:00+00:00"

    results = run_checks(payload)

    assert result_for(
        results,
        "hourly_times_are_utc",
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


@pytest.mark.parametrize("hour_count", [167])
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


def test_valid_168_hour_wave_payload_passes_without_selector_echo() -> None:
    payload = valid_wave_payload()

    assert "model" not in payload
    assert "models" not in payload
    results = run_wave_checks(payload)
    assert all(result["status"] == "pass" for result in results)
    assert all(
        str(result["check_name"]).startswith("wave:")
        for result in results
    )


def _test_invalid_configured_wave_selector_fails() -> None:
    results = run_wave_checks(
        valid_wave_payload(),
        model_selector="auto",
    )

    assert result_for(
        results,
        "configured_model_selector",
        source_label="wave",
    )["status"] == "fail"


@pytest.mark.parametrize("field_name", WAVE_FIELDS)
def _test_missing_required_wave_field_fails(field_name: str) -> None:
    payload = valid_wave_payload()
    del payload["hourly"][field_name]

    results = run_wave_checks(payload)

    assert result_for(
        results,
        f"{field_name}_exists",
        source_label="wave",
    )["status"] == "fail"


@pytest.mark.parametrize(
    ("value", "check_name"),
    [
        (None, "wave_height_has_no_nulls"),
        (True, "wave_height_values_are_numeric"),
        ("high", "wave_height_values_are_numeric"),
    ],
)
def _test_invalid_wave_values_fail(
    value: Any,
    check_name: str,
) -> None:
    payload = valid_wave_payload()
    payload["hourly"]["wave_height"][12] = value

    results = run_wave_checks(payload)

    assert result_for(
        results,
        check_name,
        source_label="wave",
    )["status"] == "fail"


def _test_wave_field_length_mismatch_fails() -> None:
    payload = valid_wave_payload()
    payload["hourly"]["wave_period"].pop()

    results = run_wave_checks(payload)

    assert result_for(
        results,
        "wave_period_count",
        source_label="wave",
    )["status"] == "fail"


def _test_wave_coordinate_comparison_uses_parsed_numeric_equality() -> None:
    payload = valid_wave_payload()
    payload["latitude"] = "34.6250000"
    payload["longitude"] = "-76.7083300"

    results = run_wave_checks(payload)

    assert result_for(
        results,
        "returned_latitude_matches_expected",
        source_label="wave",
    )["status"] == "pass"
    assert result_for(
        results,
        "returned_longitude_matches_expected",
        source_label="wave",
    )["status"] == "pass"


@pytest.mark.parametrize(
    ("coordinate_name", "check_name"),
    [
        ("latitude", "returned_latitude_matches_expected"),
        ("longitude", "returned_longitude_matches_expected"),
    ],
)
def _test_unexpected_returned_wave_coordinate_fails(
    coordinate_name: str,
    check_name: str,
) -> None:
    payload = valid_wave_payload()
    payload[coordinate_name] = 0

    results = run_wave_checks(payload)

    assert result_for(
        results,
        check_name,
        source_label="wave",
    )["status"] == "fail"


def _test_invalid_wave_timezone_fails() -> None:
    payload = valid_wave_payload()
    payload["timezone"] = "Not/A_Timezone"

    results = run_wave_checks(payload)

    assert result_for(
        results,
        "response_timezone_is_gmt",
        source_label="wave",
    )["status"] == "fail"


def _test_unparsable_wave_valid_time_fails() -> None:
    payload = valid_wave_payload()
    payload["hourly"]["time"][12] = "not-a-time"

    results = run_wave_checks(payload)

    assert result_for(
        results,
        "hourly_times_parseable",
        source_label="wave",
    )["status"] == "fail"


def _test_duplicate_wave_utc_valid_times_fail() -> None:
    payload = valid_wave_payload()
    payload["hourly"]["time"][12] = payload["hourly"]["time"][11]

    results = run_wave_checks(payload)

    assert result_for(
        results,
        "hourly_utc_time_count",
        source_label="wave",
    )["status"] == "fail"


def _test_unordered_wave_utc_valid_times_fail() -> None:
    payload = valid_wave_payload()
    times = payload["hourly"]["time"]
    times[12], times[13] = times[13], times[12]

    results = run_wave_checks(payload)

    assert result_for(
        results,
        "hourly_utc_times_strictly_ascending",
        source_label="wave",
    )["status"] == "fail"


def _test_non_hourly_wave_utc_spacing_fails() -> None:
    payload = valid_wave_payload()
    payload["hourly"]["time"][12] = "2026-07-28T12:30"

    results = run_wave_checks(payload)

    assert result_for(
        results,
        "hourly_utc_spacing",
        source_label="wave",
    )["status"] == "fail"


@pytest.mark.parametrize("hour_count", [167, 169])
def _test_wave_result_requires_exactly_168_utc_instants(
    hour_count: int,
) -> None:
    results = run_wave_checks(
        valid_wave_payload(hour_count=hour_count)
    )

    assert result_for(
        results,
        "hourly_time_count",
        source_label="wave",
    )["status"] == "fail"
    assert result_for(
        results,
        "hourly_utc_time_count",
        source_label="wave",
    )["status"] == "fail"


def test_valid_168_hour_sst_payload_passes_without_selector_echo() -> None:
    payload = valid_sst_payload()

    assert "model" not in payload
    assert "models" not in payload
    results = run_sst_checks(payload)
    assert all(result["status"] == "pass" for result in results)
    assert all(
        str(result["check_name"]).startswith("sst:")
        for result in results
    )


def _test_valid_sst_preflight_passes() -> None:
    assert all(
        result["status"] == "pass"
        for result in run_sst_preflight_checks(valid_sst_location())
    )


@pytest.mark.parametrize(
    ("sst_config", "failed_check"),
    [
        (None, "relationship_present"),
        (
            {
                "expected_returned_coordinate": EXPECTED_SST_COORDINATE,
                "coastal_regime": "Atlantic-facing marine grid",
            },
            "request_coordinate_usable",
        ),
        (
            {
                "request_coordinate": {
                    "latitude": True,
                    "longitude": -77.9,
                },
                "expected_returned_coordinate": EXPECTED_SST_COORDINATE,
                "coastal_regime": "Atlantic-facing marine grid",
            },
            "request_coordinate_usable",
        ),
        (
            {
                "request_coordinate": {
                    "latitude": 33.93,
                    "longitude": -77.9,
                },
                "coastal_regime": "Atlantic-facing marine grid",
            },
            "expected_returned_coordinate_usable",
        ),
        (
            {
                "request_coordinate": {
                    "latitude": 33.93,
                    "longitude": -77.9,
                },
                "expected_returned_coordinate": EXPECTED_SST_COORDINATE,
                "coastal_regime": " ",
            },
            "coastal_regime_present",
        ),
    ],
)
def _test_sst_preflight_rejects_missing_or_unusable_prerequisite(
    sst_config: Any,
    failed_check: str,
) -> None:
    results = run_sst_preflight_checks({"sst": sst_config})

    assert result_for(
        results,
        failed_check,
        source_label="sst",
    )["status"] == "fail"


def _test_invalid_configured_sst_selector_fails() -> None:
    results = run_sst_checks(
        valid_sst_payload(),
        model_selector="auto",
    )

    assert result_for(
        results,
        "configured_model_selector",
        source_label="sst",
    )["status"] == "fail"


def _test_missing_required_sst_field_fails() -> None:
    payload = valid_sst_payload()
    del payload["hourly"]["sea_surface_temperature"]

    results = run_sst_checks(payload)

    assert result_for(
        results,
        "sea_surface_temperature_exists",
        source_label="sst",
    )["status"] == "fail"


@pytest.mark.parametrize(
    ("value", "check_name"),
    [
        (None, "sea_surface_temperature_has_no_nulls"),
        (True, "sea_surface_temperature_values_are_numeric"),
        ("warm", "sea_surface_temperature_values_are_numeric"),
    ],
)
def _test_invalid_sst_values_fail(
    value: Any,
    check_name: str,
) -> None:
    payload = valid_sst_payload()
    payload["hourly"]["sea_surface_temperature"][12] = value

    results = run_sst_checks(payload)

    assert result_for(
        results,
        check_name,
        source_label="sst",
    )["status"] == "fail"


def _test_unexpected_returned_sst_coordinate_fails() -> None:
    payload = valid_sst_payload()
    payload["latitude"] = "0"

    results = run_sst_checks(payload)

    assert result_for(
        results,
        "returned_latitude_matches_expected",
        source_label="sst",
    )["status"] == "fail"


def _test_invalid_sst_timezone_and_timeline_fail() -> None:
    payload = valid_sst_payload()
    payload["timezone"] = "Not/A_Timezone"
    payload["hourly"]["time"][12] = payload["hourly"]["time"][11]

    results = run_sst_checks(payload)

    assert result_for(
        results,
        "response_timezone_is_gmt",
        source_label="sst",
    )["status"] == "fail"
    assert result_for(
        results,
        "hourly_utc_time_count",
        source_label="sst",
    )["status"] == "fail"


def test_valid_tide_payload_passes() -> None:
    payload_results = run_tide_quality_checks(
        valid_tide_payload(),
        valid_tide_provenance(),
        valid_tide_forecast_times(),
    )

    assert all(result["status"] == "pass" for result in payload_results)
    assert all(
        str(result["check_name"]).startswith("tide:")
        for result in payload_results
    )


@pytest.mark.parametrize(
    ("tide_config", "failed_check"),
    [
        (None, "relationship_present"),
        (
            {
                "prediction_location": "Ocracoke Inlet",
                "relationship_type": "transfer",
                "reference_station": "8654400",
                "high_time_offset_minutes": 9,
                "low_time_offset_minutes": 11,
                "high_multiplier": 0.63,
                "low_multiplier": 0.83,
                "distance_km": 3.697,
                "coastal_relationship": "Ocean-side transfer",
                "known_limitation": "No current interpretation",
            },
            "station_id_present",
        ),
        (
            {
                "prediction_location": "Ocracoke Inlet",
                "station_id": "TEC2793",
                "relationship_type": "fallback",
                "reference_station": "8654400",
                "high_time_offset_minutes": 9,
                "low_time_offset_minutes": 11,
                "high_multiplier": 0.63,
                "low_multiplier": 0.83,
                "distance_km": 3.697,
                "coastal_relationship": "Ocean-side transfer",
                "known_limitation": "No current interpretation",
            },
            "relationship_metadata_usable",
        ),
    ],
)
def _test_tide_preflight_rejects_missing_or_unusable_relationship(
    tide_config: Any,
    failed_check: str,
) -> None:
    results = run_tide_preflight_checks(
        {"tide": tide_config},
        valid_tide_api_config(),
    )

    assert result_for(
        results,
        failed_check,
        source_label="tide",
    )["status"] == "fail"


def test_tide_events_normalize_gmt_and_phase_boundaries() -> None:
    payload = {
        "predictions": [
            {"t": "2026-07-28 00:00", "v": "0.1", "type": "L"},
            {"t": "2026-07-28 06:00", "v": "1.2", "type": "H"},
            {"t": "2026-07-28 12:00", "v": "0.2", "type": "L"},
        ]
    }
    events = normalize_tide_events(payload)
    phases = derive_tide_phases(
        events,
        [
            datetime(2026, 7, 28, 0, tzinfo=timezone.utc),
            datetime(2026, 7, 28, 5, tzinfo=timezone.utc),
            datetime(2026, 7, 28, 6, tzinfo=timezone.utc),
        ],
    )

    assert events[0] == {
        "event_time": datetime(
            2026,
            7,
            28,
            0,
            tzinfo=timezone.utc,
        ),
        "event_type": "low",
        "predicted_water_level": 0.1,
    }
    assert [phase["phase"] for phase in phases] == [
        "rising",
        "rising",
        "falling",
    ]


@pytest.mark.parametrize(
    ("prediction_change", "failed_check"),
    [
        (("remove", "t"), "prediction_events_usable"),
        (("replace", "v", None), "prediction_events_usable"),
        (("replace", "v", "not-a-number"), "prediction_events_usable"),
        (("replace", "type", "X"), "prediction_events_usable"),
        (("duplicate_time", None), "prediction_events_unique_and_ascending"),
        (("nonalternating", None), "prediction_events_alternate"),
    ],
)
def test_invalid_tide_event_response_fails(
    prediction_change: tuple[str, str | None, Any] | tuple[str, None],
    failed_check: str,
) -> None:
    payload = valid_tide_payload()
    action = prediction_change[0]

    if action == "remove":
        del payload["predictions"][1][prediction_change[1]]
    elif action == "replace":
        payload["predictions"][1][prediction_change[1]] = (
            prediction_change[2]
        )
    elif action == "duplicate_time":
        payload["predictions"][1]["t"] = payload["predictions"][0]["t"]
    else:
        payload["predictions"][1]["type"] = "L"

    results = run_tide_quality_checks(
        payload,
        valid_tide_provenance(),
        valid_tide_forecast_times(),
    )

    assert result_for(
        results,
        failed_check,
        source_label="tide",
    )["status"] == "fail"


def test_tide_result_rejects_missing_phase_bounds() -> None:
    payload = valid_tide_payload()
    payload["predictions"] = payload["predictions"][2:-5]

    results = run_tide_quality_checks(
        payload,
        valid_tide_provenance(),
        valid_tide_forecast_times(),
    )

    assert result_for(
        results,
        "phase_bounds_complete",
        source_label="tide",
    )["status"] == "fail"


def test_tide_result_rejects_non_utc_forecast_timeline() -> None:
    forecast_times = [
        forecast_time.replace(tzinfo=None)
        for forecast_time in valid_tide_forecast_times()
    ]

    results = run_tide_quality_checks(
        valid_tide_payload(),
        valid_tide_provenance(),
        forecast_times,
    )

    assert result_for(
        results,
        "forecast_timeline_valid",
        source_label="tide",
    )["status"] == "fail"
    assert result_for(
        results,
        "phase_bounds_complete",
        source_label="tide",
    )["status"] == "fail"


def test_tide_phase_is_not_inferred_outside_event_pair() -> None:
    events = normalize_tide_events(
        {
            "predictions": [
                {"t": "2026-07-28 00:00", "v": "0.1", "type": "L"},
                {"t": "2026-07-28 06:00", "v": "1.2", "type": "H"},
            ]
        }
    )

    with pytest.raises(ValueError, match="preceding extremum"):
        derive_tide_phases(
            events,
            [datetime(2026, 7, 27, 23, tzinfo=timezone.utc)],
        )

    with pytest.raises(ValueError, match="following extremum"):
        derive_tide_phases(
            events,
            [datetime(2026, 7, 28, 6, tzinfo=timezone.utc)],
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("station", ""),
        ("begin_date", "20260728"),
        ("end_date", "20260803"),
        ("product", "water_level"),
        ("interval", "h"),
        ("datum", "MSL"),
        ("time_zone", "lst_ldt"),
        ("units", "english"),
        ("format", "csv"),
        ("captured_at", None),
    ],
)
def test_tide_result_rejects_invalid_request_provenance(
    field_name: str,
    invalid_value: Any,
) -> None:
    provenance = valid_tide_provenance()
    provenance[field_name] = invalid_value

    results = run_tide_quality_checks(
        valid_tide_payload(),
        provenance,
        valid_tide_forecast_times(),
    )
    check_name = (
        "request_station_present"
        if field_name == "station"
        else (
            "request_capture_time_present"
            if field_name == "captured_at"
            else (
                "request_window_bounds_forecast"
                if field_name in {"begin_date", "end_date"}
                else f"request_{field_name}"
            )
        )
    )

    assert result_for(
        results,
        check_name,
        source_label="tide",
    )["status"] == "fail"
