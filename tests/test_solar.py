from datetime import datetime
from zoneinfo import ZoneInfo

from saltbytes.solar import _minutes_from_event, _solar_state, derive_solar_context


def test_solar_state_boundaries_are_deterministic() -> None:
    timezone = ZoneInfo("America/New_York")
    morning_twilight_start = datetime(2026, 7, 29, 5, 30, tzinfo=timezone)
    sunrise = datetime(2026, 7, 29, 6, 0, tzinfo=timezone)
    sunset = datetime(2026, 7, 29, 20, 0, tzinfo=timezone)
    evening_twilight_end = datetime(2026, 7, 29, 20, 30, tzinfo=timezone)

    assert _solar_state(
        morning_twilight_start,
        morning_twilight_start,
        sunrise,
        sunset,
        evening_twilight_end,
    ) == "morning_twilight"
    assert _solar_state(
        sunrise,
        morning_twilight_start,
        sunrise,
        sunset,
        evening_twilight_end,
    ) == "daylight"
    assert _solar_state(
        sunset,
        morning_twilight_start,
        sunrise,
        sunset,
        evening_twilight_end,
    ) == "evening_twilight"
    assert _solar_state(
        evening_twilight_end,
        morning_twilight_start,
        sunrise,
        sunset,
        evening_twilight_end,
    ) == "night"


def test_relative_solar_minutes_are_signed_by_event_minute() -> None:
    timezone = ZoneInfo("America/New_York")
    event = datetime(2026, 7, 29, 6, 15, 45, tzinfo=timezone)

    assert _minutes_from_event(datetime(2026, 7, 29, 6, 14, tzinfo=timezone), event) == -1
    assert _minutes_from_event(datetime(2026, 7, 29, 6, 15, tzinfo=timezone), event) == 0
    assert _minutes_from_event(datetime(2026, 7, 29, 6, 16, tzinfo=timezone), event) == 1


def test_relative_solar_minutes_use_absolute_elapsed_time_at_spring_forward() -> None:
    timezone = ZoneInfo("America/New_York")
    event = datetime(2026, 3, 8, 1, 30, tzinfo=timezone)
    after_transition = datetime(2026, 3, 8, 3, 30, tzinfo=timezone)

    assert _minutes_from_event(after_transition, event) == 60


def test_relative_solar_minutes_use_absolute_elapsed_time_at_fall_back() -> None:
    timezone = ZoneInfo("America/New_York")
    event = datetime(2026, 11, 1, 1, 30, tzinfo=timezone, fold=0)
    after_transition = datetime(2026, 11, 1, 1, 30, tzinfo=timezone, fold=1)

    assert _minutes_from_event(after_transition, event) == 60


def test_solar_context_uses_local_date_across_daylight_saving_boundary() -> None:
    context = derive_solar_context(
        datetime(2026, 3, 8, 7, tzinfo=ZoneInfo("UTC")),
        35.9096355,
        -75.5966537,
        "America/New_York",
    )

    local_sunrise = context["sunrise"].astimezone(
        ZoneInfo("America/New_York")
    )
    assert local_sunrise.date().isoformat() == "2026-03-08"
    assert context["solar_state"] is not None


def test_solar_context_is_unavailable_without_persisted_display_context() -> None:
    context = derive_solar_context(
        datetime(2026, 7, 29, 12, tzinfo=ZoneInfo("UTC")),
        None,
        None,
        None,
    )

    assert context["solar_state"] is None
    assert context["minutes_from_sunrise"] is None
