from datetime import datetime, timezone
from importlib.metadata import version
from typing import Any
from zoneinfo import ZoneInfo

from astral import Observer
from astral.sun import sun

SOLAR_CALCULATION_CONTRACT = "solar_context_v1"
SOLAR_CALCULATION_LIBRARY = "astral"


def solar_calculation_provenance() -> dict[str, str]:
    return {
        "calculation_contract": SOLAR_CALCULATION_CONTRACT,
        "calculation_library": SOLAR_CALCULATION_LIBRARY,
        "calculation_library_version": version(SOLAR_CALCULATION_LIBRARY),
    }


def derive_solar_context(
    forecast_time: datetime,
    display_latitude: float | None,
    display_longitude: float | None,
    display_timezone: str | None,
) -> dict[str, Any]:
    if (
        display_latitude is None
        or display_longitude is None
        or display_timezone is None
    ):
        return _unavailable_context(forecast_time)

    timezone = ZoneInfo(display_timezone)
    local_time = forecast_time.astimezone(timezone)
    events = sun(
        Observer(latitude=display_latitude, longitude=display_longitude),
        date=local_time.date(),
        tzinfo=timezone,
    )
    morning_twilight_start = events["dawn"]
    sunrise = events["sunrise"]
    sunset = events["sunset"]
    evening_twilight_end = events["dusk"]

    return {
        "forecast_time": forecast_time,
        "morning_twilight_start": morning_twilight_start,
        "sunrise": sunrise,
        "sunset": sunset,
        "evening_twilight_end": evening_twilight_end,
        "solar_state": _solar_state(
            local_time,
            morning_twilight_start,
            sunrise,
            sunset,
            evening_twilight_end,
        ),
        "minutes_from_sunrise": _minutes_from_event(local_time, sunrise),
        "minutes_from_sunset": _minutes_from_event(local_time, sunset),
    }


def _unavailable_context(forecast_time: datetime) -> dict[str, Any]:
    return {
        "forecast_time": forecast_time,
        "morning_twilight_start": None,
        "sunrise": None,
        "sunset": None,
        "evening_twilight_end": None,
        "solar_state": None,
        "minutes_from_sunrise": None,
        "minutes_from_sunset": None,
    }


def _solar_state(
    local_time: datetime,
    morning_twilight_start: datetime,
    sunrise: datetime,
    sunset: datetime,
    evening_twilight_end: datetime,
) -> str:
    if local_time < morning_twilight_start or local_time >= evening_twilight_end:
        return "night"
    if local_time < sunrise:
        return "morning_twilight"
    if local_time < sunset:
        return "daylight"
    return "evening_twilight"


def _minutes_from_event(time: datetime, event: datetime) -> int:
    time_minute = time.astimezone(timezone.utc).replace(second=0, microsecond=0)
    event_minute = event.astimezone(timezone.utc).replace(second=0, microsecond=0)
    return int((time_minute - event_minute).total_seconds() // 60)
