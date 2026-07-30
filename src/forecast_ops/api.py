from datetime import datetime, timedelta, timezone
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
        "timezone": "GMT",
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


# build the open meteo marine request parameters for one location
def build_wave_params(
    location: dict[str, Any],
    wave_api_config: dict[str, Any],
) -> dict[str, Any]:
    request_coordinate = location["wave"]["request_coordinate"]

    return {
        "latitude": request_coordinate["latitude"],
        "longitude": request_coordinate["longitude"],
        "models": wave_api_config["model"],
        "forecast_days": wave_api_config["forecast_days"],
        "hourly": ",".join(wave_api_config["hourly_fields"]),
        "timezone": "GMT",
    }


# fetch wave data for one configured location
def fetch_wave_forecast(
    location: dict[str, Any],
    wave_api_config: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    params = build_wave_params(location, wave_api_config)

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(
            wave_api_config["base_url"],
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "wave forecast api response must contain a json object"
        )

    return payload


# build the open meteo marine SST request parameters for one location
def build_sst_params(
    location: dict[str, Any],
    sst_api_config: dict[str, Any],
) -> dict[str, Any]:
    request_coordinate = location["sst"]["request_coordinate"]

    return {
        "latitude": request_coordinate["latitude"],
        "longitude": request_coordinate["longitude"],
        "models": sst_api_config["model"],
        "forecast_days": sst_api_config["forecast_days"],
        "hourly": ",".join(sst_api_config["hourly_fields"]),
        "timezone": "GMT",
    }


# fetch sea surface temperature data for one configured location
def fetch_sst_forecast(
    location: dict[str, Any],
    sst_api_config: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    params = build_sst_params(location, sst_api_config)

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(
            sst_api_config["base_url"],
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "sst forecast api response must contain a json object"
        )

    return payload


# build the accepted NOAA high and low prediction request
def build_tide_params(
    location: dict[str, Any],
    tide_api_config: dict[str, Any],
    forecast_start: datetime,
) -> dict[str, Any]:
    if forecast_start.tzinfo is None or forecast_start.utcoffset() is None:
        raise ValueError("forecast_start must include timezone information")

    forecast_date = forecast_start.astimezone(timezone.utc).date()
    begin_date = forecast_date - timedelta(days=1)
    end_date = forecast_date + timedelta(
        days=tide_api_config["forecast_days"] + 1
    )

    return {
        "station": location["tide"]["station_id"],
        "begin_date": begin_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
        "product": tide_api_config["product"],
        "interval": tide_api_config["interval"],
        "datum": tide_api_config["datum"],
        "time_zone": tide_api_config["time_zone"],
        "units": tide_api_config["units"],
        "format": tide_api_config["format"],
    }


# fetch NOAA high and low tide predictions for one configured relationship
def fetch_tide_predictions(
    tide_api_config: dict[str, Any],
    params: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(
            tide_api_config["base_url"],
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "tide prediction api response must contain a json object"
        )

    return payload
