import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

_OPEN_METEO_RETRY_BACKOFF_SECONDS = (1.0, 2.0)

logger = logging.getLogger(__name__)

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
        "cloud_cover",
    ),
}
WEATHER_REQUIRED_HOURLY_FIELDS = (
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation_probability",
    "precipitation",
)
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


def _get_open_meteo_response(
    client: httpx.Client,
    url: str,
    params: dict[str, Any],
) -> tuple[httpx.Response, int, str | None]:
    previous_error: str | None = None

    for attempt in range(3):
        try:
            response = client.get(url, params=params)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as error:
            if attempt == 2:
                raise
            previous_error = type(error).__name__
            time.sleep(_OPEN_METEO_RETRY_BACKOFF_SECONDS[attempt])
        else:
            return response, attempt + 1, previous_error

    raise AssertionError("Open-Meteo request retry loop ended unexpectedly")


def _fetch_open_meteo_payload(
    url: str,
    params: dict[str, Any],
    timeout_seconds: float,
    client: httpx.Client | None,
    source: str,
    location_id: str,
) -> Any:
    if client is None:
        with httpx.Client(timeout=timeout_seconds) as request_client:
            response, attempts, previous_error = _get_open_meteo_response(
                request_client,
                url,
                params,
            )
    else:
        response, attempts, previous_error = _get_open_meteo_response(
            client,
            url,
            params,
        )

    response.raise_for_status()
    if previous_error is not None:
        logger.info(
            "open meteo request recovered source=%s location=%s "
            "attempts=%s previous_error=%s",
            source,
            location_id,
            attempts,
            previous_error,
        )
    return response.json()

# build the open meteo request parameters for one location
def build_forecast_params(
    location: dict[str, Any],
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
    timeout_seconds: float = 10.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    params = build_forecast_params(location)

    payload = _fetch_open_meteo_payload(
        WEATHER_API["base_url"],
        params,
        timeout_seconds,
        client,
        "weather",
        location["id"],
    )

    if not isinstance(payload, dict):
        raise ValueError("forecast api response must contain a json object")

    return payload


# build the open meteo marine request parameters for one location
def build_wave_params(
    location: dict[str, Any],
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
    timeout_seconds: float = 10.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    params = build_wave_params(location)

    payload = _fetch_open_meteo_payload(
        WAVE_API["base_url"],
        params,
        timeout_seconds,
        client,
        "wave",
        location["id"],
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "wave forecast api response must contain a json object"
        )

    return payload


# build the open meteo marine SST request parameters for one location
def build_sst_params(
    location: dict[str, Any],
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
    timeout_seconds: float = 10.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    params = build_sst_params(location)

    payload = _fetch_open_meteo_payload(
        SST_API["base_url"],
        params,
        timeout_seconds,
        client,
        "sst",
        location["id"],
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "sst forecast api response must contain a json object"
        )

    return payload


# build the accepted NOAA high and low prediction request
def build_tide_params(
    location: dict[str, Any],
    forecast_start: datetime,
) -> dict[str, Any]:
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
    params: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
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
