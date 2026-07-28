from datetime import datetime, timezone
from typing import Any


# validate the expected hourly arrays in one forecast payload
def run_payload_quality_checks(
    payload: dict[str, Any],
    expected_hourly_fields: list[str],
) -> list[dict[str, str | datetime]]:
    checked_at = datetime.now(timezone.utc)
    results: list[dict[str, str | datetime]] = []

    hourly = payload.get("hourly")

    hourly_status = "pass" if isinstance(hourly, dict) else "fail"

    results.append(
        {
            "check_name": "hourly_mapping_exists",
            "status": hourly_status,
            "observed_value": type(hourly).__name__,
            "expected_value": "dict",
            "checked_at": checked_at,
        }
    )

    if not isinstance(hourly, dict):
        return results

    forecast_times = hourly.get("time")
    time_count = len(forecast_times) if isinstance(forecast_times, list) else 0

    results.append(
        {
            "check_name": "hourly_time_not_empty",
            "status": "pass" if time_count > 0 else "fail",
            "observed_value": str(time_count),
            "expected_value": "> 0",
            "checked_at": checked_at,
        }
    )

    for field_name in expected_hourly_fields:
        values = hourly.get(field_name)
        value_count = len(values) if isinstance(values, list) else 0

        results.append(
            {
                "check_name": f"{field_name}_count_matches_time",
                "status": "pass" if value_count == time_count else "fail",
                "observed_value": str(value_count),
                "expected_value": str(time_count),
                "checked_at": checked_at,
            }
        )

    return results