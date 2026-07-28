from typing import Any

import httpx


# build the open meteo request parameters for one location
def build_forecast_params(
    location: dict[str, Any],
    api_config: dict[str, Any],
) -> dict[str, Any]:
    request_coordinate = location["weather"]["request_coordinate"]

    return {
        "latitude": request_coordinate["latitude"],
        "longitude": request_coordinate["longitude"],
        "models": api_config["model"],
        "forecast_days": api_config["forecast_days"],
        "hourly": ",".join(api_config["hourly_fields"]),
        "timezone": "auto",
    }


# fetch forecast data for one configured location
def fetch_forecast(
    location: dict[str, Any],
    api_config: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    params = build_forecast_params(location, api_config)

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(api_config["base_url"], params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("forecast api response must contain a json object")

    return payload
