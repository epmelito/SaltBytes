from datetime import datetime, timezone
from decimal import Decimal

import pytest

from saltbytes.spanish_mackerel import (
    METHODOLOGY_VERSION,
    AvailableSpanishMackerelConditionsScore,
    SpanishMackerelConditionsInput,
    UnavailableSpanishMackerelConditionsScore,
    calculate_spanish_mackerel_conditions_score,
)


def score_input(**changes: object) -> SpanishMackerelConditionsInput:
    values: dict[str, object] = {
        "run_id": "run-1",
        "location_id": "jennettes_pier",
        "fishing_context": "pier",
        "forecast_time": datetime(2026, 7, 15, 12, tzinfo=timezone.utc),
        "display_timezone": "America/New_York",
        "weather_status": "success",
        "wave_status": "success",
        "sst_status": "success",
        "wind_speed_10m": 10.0,
        "wind_gusts_10m": 15.0,
        "wave_height": 0.5,
        "sea_surface_temperature": 20.0,
    }
    values.update(changes)
    return SpanishMackerelConditionsInput(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    (
        "local_date",
        "sst",
        "wind",
        "gust",
        "waves",
        "biological",
        "practical",
        "score",
        "score_band",
    ),
    [
        ("2026-01-15", 20, 10, 15, 0.5, "0", "100", 0, "very_limited_alignment"),
        ("2026-04-01", 20, 10, 15, 0.5, "40", "100", 40, "mixed_conditions"),
        ("2026-04-01", 14, 10, 15, 0.5, "35.5", "100", 36, "limited_alignment"),
        ("2026-07-15", 20, 10, 15, 0.5, "100", "100", 100, "strong_alignment"),
        ("2026-07-15", 20, 20, 30, 1.2, "100", "68", 76, "favorable_alignment"),
        ("2026-07-15", 20, 55, 60, 2.5, "100", "0", 25, "limited_alignment"),
        ("2026-10-31", 20, 10, 15, 0.5, "60", "100", 60, "favorable_alignment"),
        ("2026-10-31", 14, 10, 15, 0.5, "49.5", "100", 50, "mixed_conditions"),
    ],
)
def test_calculation_matches_approved_validation_scenarios(
    local_date: str,
    sst: float,
    wind: float,
    gust: float,
    waves: float,
    biological: str,
    practical: str,
    score: int,
    score_band: str,
) -> None:
    forecast_time = datetime.fromisoformat(
        f"{local_date}T16:00:00+00"
    )

    result = calculate_spanish_mackerel_conditions_score(
        score_input(
            forecast_time=forecast_time,
            sea_surface_temperature=sst,
            wind_speed_10m=wind,
            wind_gusts_10m=gust,
            wave_height=waves,
        )
    )

    assert isinstance(result, AvailableSpanishMackerelConditionsScore)
    assert result.methodology_version == METHODOLOGY_VERSION
    assert result.biological_alignment == Decimal(biological)
    assert result.practical_fishability == Decimal(practical)
    assert result.score == score
    assert result.score_band == score_band


def test_calculation_uses_persisted_timezone_for_local_date() -> None:
    result = calculate_spanish_mackerel_conditions_score(
        score_input(
            forecast_time=datetime(2026, 4, 1, 2, tzinfo=timezone.utc),
        )
    )

    assert isinstance(result, AvailableSpanishMackerelConditionsScore)
    assert result.local_forecast_date.isoformat() == "2026-03-31"
    assert Decimal("0") < result.seasonal_alignment < Decimal("40")


def test_value_error_timezone_key_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid_timezone(_: str) -> None:
        raise ValueError("malformed timezone key")

    monkeypatch.setattr(
        "saltbytes.spanish_mackerel.ZoneInfo",
        invalid_timezone,
    )

    result = calculate_spanish_mackerel_conditions_score(score_input())

    assert isinstance(result, UnavailableSpanishMackerelConditionsScore)
    assert result.unavailable_reasons == ("display_timezone_invalid",)


def test_local_date_overflow_is_unavailable() -> None:
    class OverflowingDatetime(datetime):
        def astimezone(self, tz: object | None = None) -> datetime:
            raise OverflowError("local date cannot be derived")

    result = calculate_spanish_mackerel_conditions_score(
        score_input(
            forecast_time=OverflowingDatetime(
                2026,
                7,
                15,
                12,
                tzinfo=timezone.utc,
            )
        )
    )

    assert isinstance(result, UnavailableSpanishMackerelConditionsScore)
    assert result.unavailable_reasons == ("local_forecast_date_unavailable",)


def test_oversized_integer_numeric_input_is_unavailable() -> None:
    result = calculate_spanish_mackerel_conditions_score(
        score_input(wind_speed_10m=10**10000)
    )

    assert isinstance(result, UnavailableSpanishMackerelConditionsScore)
    assert result.unavailable_reasons == ("wind_speed_10m_invalid",)


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"location_id": "unknown", "fishing_context": "surf"}, "location_not_applicable"),
        ({"fishing_context": "surf"}, "location_not_applicable"),
        ({"display_timezone": None}, "display_timezone_missing"),
        ({"display_timezone": 1}, "display_timezone_invalid"),
        ({"display_timezone": "Invalid/Timezone"}, "display_timezone_invalid"),
        ({"forecast_time": datetime(2026, 7, 15, 12)}, "forecast_time_invalid"),
        ({"weather_status": None}, "weather_source_missing"),
        ({"weather_status": "fetch_failed"}, "weather_source_not_success"),
        ({"wave_status": None}, "wave_source_missing"),
        ({"wave_status": "validation_failed"}, "wave_source_not_success"),
        ({"sst_status": None}, "sst_source_missing"),
        ({"sst_status": "persistence_failed"}, "sst_source_not_success"),
        ({"wind_speed_10m": None}, "wind_speed_10m_missing"),
        ({"wind_gusts_10m": float("nan")}, "wind_gusts_10m_invalid"),
        ({"wave_height": -0.1}, "wave_height_invalid"),
        ({"sea_surface_temperature": -2.1}, "sea_surface_temperature_invalid"),
        ({"sea_surface_temperature": 40.1}, "sea_surface_temperature_invalid"),
        ({"wind_speed_10m": True}, "wind_speed_10m_invalid"),
    ],
)
def test_unavailable_conditions_do_not_produce_a_reduced_score(
    changes: dict[str, object],
    reason: str,
) -> None:
    result = calculate_spanish_mackerel_conditions_score(
        score_input(**changes)
    )

    assert isinstance(result, UnavailableSpanishMackerelConditionsScore)
    assert result.state == "unavailable"
    assert result.methodology_version == METHODOLOGY_VERSION
    assert reason in result.unavailable_reasons
    assert not hasattr(result, "score")


def test_available_result_has_stable_explanations_and_confidence() -> None:
    result = calculate_spanish_mackerel_conditions_score(
        score_input(
            forecast_time=datetime(2026, 4, 1, 16, tzinfo=timezone.utc),
            sea_surface_temperature=14.0,
        )
    )

    assert isinstance(result, AvailableSpanishMackerelConditionsScore)
    assert result.positive_factors == ("wind_fishability", "wave_fishability")
    assert result.limiting_factors == (
        "seasonal_alignment",
        "thermal_context",
    )
    assert result.unknown_factors == (
        "local_baitfish_presence",
        "current_spanish_mackerel_presence",
        "schools_within_casting_range",
        "nearshore_sst_accuracy_and_site_representativeness",
    )
    assert [(factor.identifier, factor.kind) for factor in result.factors] == [
        ("seasonal_alignment", "limiting"),
        ("thermal_context", "limiting"),
        ("wind_fishability", "positive"),
        ("wave_fishability", "positive"),
        ("local_baitfish_presence", "unknown"),
        ("current_spanish_mackerel_presence", "unknown"),
        ("schools_within_casting_range", "unknown"),
        ("nearshore_sst_accuracy_and_site_representativeness", "unknown"),
    ]
    assert result.confidence[-1].identifier == "overall_interpretation_confidence"
    assert result.confidence[-1].state == "moderate"


def test_ocracoke_retains_its_moderate_location_confidence() -> None:
    result = calculate_spanish_mackerel_conditions_score(
        score_input(
            location_id="ocracoke_ramp_72",
            fishing_context="surf",
        )
    )

    assert isinstance(result, AvailableSpanishMackerelConditionsScore)
    assert result.confidence[1].state == "moderate"


@pytest.mark.parametrize(
    ("location_id", "fishing_context"),
    [
        ("jennettes_pier", "pier"),
        ("ocracoke_ramp_72", "surf"),
        ("fort_macon_ocean", "surf"),
        ("bogue_inlet_pier", "pier"),
        ("fort_fisher", "surf"),
    ],
)
def test_all_approved_location_context_pairs_are_eligible(
    location_id: str,
    fishing_context: str,
) -> None:
    result = calculate_spanish_mackerel_conditions_score(
        score_input(
            location_id=location_id,
            fishing_context=fishing_context,
        )
    )

    assert isinstance(result, AvailableSpanishMackerelConditionsScore)


def test_repeated_calculation_is_deterministic() -> None:
    value = score_input(wind_speed_10m=20.0, wind_gusts_10m=30.0, wave_height=1.2)

    assert calculate_spanish_mackerel_conditions_score(value) == (
        calculate_spanish_mackerel_conditions_score(value)
    )
