from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

WEATHER_API = {
    "base_url": "https://api.open-meteo.com/v1/forecast",
    "model": "ncep_nbm_conus",
    "forecast_days": 7,
    "hourly_fields": (
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "precipitation_probability",
        "precipitation",
    ),
}
WAVE_API = {
    "base_url": "https://marine-api.open-meteo.com/v1/marine",
    "model": "meteofrance_wave",
    "forecast_days": 7,
    "hourly_fields": ("wave_height", "wave_direction", "wave_period"),
}
SST_API = {
    "base_url": "https://marine-api.open-meteo.com/v1/marine",
    "model": "meteofrance_currents",
    "forecast_days": 7,
    "hourly_fields": ("sea_surface_temperature",),
}
TIDE_API = {
    "base_url": "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
    "product": "predictions",
    "interval": "hilo",
    "datum": "MLLW",
    "time_zone": "gmt",
    "units": "metric",
    "format": "json",
    "forecast_days": 7,
}

# build the open meteo request parameters for one location
def build_forecast_params(
    location: dict[str, Any],
    api_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_coordinate = location["weather"]["request_coordinate"]

    return {
        "latitude": request_coordinate["latitude"],
        "longitude": request_coordinate["longitude"],
        "models": WEATHER_API["model"],
        "forecast_days": WEATHER_API["forecast_days"],
        "hourly": ",".join(WEATHER_API["hourly_fields"]),
        "timezone": "GMT",
    }


# fetch forecast data for one configured location
def fetch_forecast(
    location: dict[str, Any],
    api_config: dict[str, Any] | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    params = build_forecast_params(location)

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(WEATHER_API["base_url"], params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("forecast api response must contain a json object")

    return payload


# build the open meteo marine request parameters for one location
def build_wave_params(
    location: dict[str, Any],
    wave_api_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_coordinate = location["wave"]["request_coordinate"]

    return {
        "latitude": request_coordinate["latitude"],
        "longitude": request_coordinate["longitude"],
        "models": WAVE_API["model"],
        "forecast_days": WAVE_API["forecast_days"],
        "hourly": ",".join(WAVE_API["hourly_fields"]),
        "timezone": "GMT",
    }


# fetch wave data for one configured location
def fetch_wave_forecast(
    location: dict[str, Any],
    wave_api_config: dict[str, Any] | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    params = build_wave_params(location)

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(
            WAVE_API["base_url"],
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
    sst_api_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_coordinate = location["sst"]["request_coordinate"]

    return {
        "latitude": request_coordinate["latitude"],
        "longitude": request_coordinate["longitude"],
        "models": SST_API["model"],
        "forecast_days": SST_API["forecast_days"],
        "hourly": ",".join(SST_API["hourly_fields"]),
        "timezone": "GMT",
    }


# fetch sea surface temperature data for one configured location
def fetch_sst_forecast(
    location: dict[str, Any],
    sst_api_config: dict[str, Any] | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    params = build_sst_params(location)

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(
            SST_API["base_url"],
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
    tide_api_config: dict[str, Any] | None = None,
    forecast_start: datetime | None = None,
) -> dict[str, Any]:
    if forecast_start is None:
        raise ValueError("forecast_start is required")
    if forecast_start.tzinfo is None or forecast_start.utcoffset() is None:
        raise ValueError("forecast_start must include timezone information")

    forecast_date = forecast_start.astimezone(timezone.utc).date()
    begin_date = forecast_date - timedelta(days=1)
    end_date = forecast_date + timedelta(
        days=TIDE_API["forecast_days"] + 1
    )

    return {
        "station": location["tide"]["station_id"],
        "begin_date": begin_date.strftime("%Y%m%d"),
        "end_date": end_date.strftime("%Y%m%d"),
        "product": TIDE_API["product"],
        "interval": TIDE_API["interval"],
        "datum": TIDE_API["datum"],
        "time_zone": TIDE_API["time_zone"],
        "units": TIDE_API["units"],
        "format": TIDE_API["format"],
    }


# fetch NOAA high and low tide predictions for one configured relationship
def fetch_tide_predictions(
    tide_api_config: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    if params is None:
        raise ValueError("tide request parameters are required")
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(
            TIDE_API["base_url"],
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "tide prediction api response must contain a json object"
        )

    return payload
