from forecast_ops.quality import run_payload_quality_checks


def test_run_payload_quality_checks_passes_valid_payload() -> None:
    payload = {
        "hourly": {
            "time": [
                "2026-07-28T12:00",
                "2026-07-28T13:00",
            ],
            "temperature_2m": [18.2, 19.1],
            "precipitation_probability": [10, 20],
            "wind_speed_10m": [8.4, 9.1],
        }
    }

    results = run_payload_quality_checks(
        payload=payload,
        expected_hourly_fields=[
            "temperature_2m",
            "precipitation_probability",
            "wind_speed_10m",
        ],
    )

    assert all(result["status"] == "pass" for result in results)


def test_run_payload_quality_checks_detects_mismatched_metric_count() -> None:
    payload = {
        "hourly": {
            "time": [
                "2026-07-28T12:00",
                "2026-07-28T13:00",
            ],
            "temperature_2m": [18.2],
        }
    }

    results = run_payload_quality_checks(
        payload=payload,
        expected_hourly_fields=["temperature_2m"],
    )

    temperature_result = next(
        result
        for result in results
        if result["check_name"] == "temperature_2m_count_matches_time"
    )

    assert temperature_result["status"] == "fail"
    assert temperature_result["observed_value"] == "1"
    assert temperature_result["expected_value"] == "2"


def test_run_payload_quality_checks_stops_when_hourly_mapping_is_missing() -> None:
    results = run_payload_quality_checks(
        payload={},
        expected_hourly_fields=["temperature_2m"],
    )

    assert results == [
        {
            "check_name": "hourly_mapping_exists",
            "status": "fail",
            "observed_value": "NoneType",
            "expected_value": "dict",
            "checked_at": results[0]["checked_at"],
        }
    ]