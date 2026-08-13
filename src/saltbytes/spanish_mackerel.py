import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TypeAlias
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

METHODOLOGY_VERSION = "spanish-mackerel-v1.1.0"

_APPROVED_LOCATION_CONTEXTS = {
    "jennettes_pier": "pier",
    "ocracoke_ramp_72": "surf",
    "fort_macon_ocean": "surf",
    "bogue_inlet_pier": "pier",
    "fort_fisher": "surf",
    "sunset_beach_pier": "pier",
}
_UNKNOWN_FACTORS = (
    "local_baitfish_presence",
    "current_spanish_mackerel_presence",
    "schools_within_casting_range",
    "nearshore_sst_accuracy_and_site_representativeness",
)


@dataclass(frozen=True)
class SpanishMackerelConditionsInput:
    run_id: str
    location_id: str
    fishing_context: str
    forecast_time: datetime | None
    display_timezone: object
    weather_status: str | None
    wave_status: str | None
    sst_status: str | None
    wind_speed_10m: object
    wind_gusts_10m: object
    wave_height: object
    sea_surface_temperature: object


@dataclass(frozen=True)
class ConfidenceDimension:
    identifier: str
    state: str


@dataclass(frozen=True)
class FactorSelection:
    identifier: str
    kind: str


@dataclass(frozen=True)
class AvailableSpanishMackerelConditionsScore:
    state: str
    methodology_version: str
    run_id: str
    location_id: str
    forecast_time: datetime
    local_forecast_date: date
    score: int
    score_band: str
    seasonal_alignment: Decimal
    thermal_alignment: Decimal
    biological_alignment: Decimal
    effective_wind_kmh: Decimal
    wind_fishability: Decimal
    wave_fishability: Decimal
    practical_fishability: Decimal
    confidence: tuple[ConfidenceDimension, ...]
    positive_factors: tuple[str, ...]
    limiting_factors: tuple[str, ...]
    unknown_factors: tuple[str, ...]
    factors: tuple[FactorSelection, ...]


@dataclass(frozen=True)
class UnavailableSpanishMackerelConditionsScore:
    state: str
    methodology_version: str
    run_id: str
    location_id: str
    forecast_time: datetime | None
    unavailable_reasons: tuple[str, ...]


SpanishMackerelConditionsScore: TypeAlias = (
    AvailableSpanishMackerelConditionsScore
    | UnavailableSpanishMackerelConditionsScore
)


def calculate_spanish_mackerel_conditions_score(
    value: SpanishMackerelConditionsInput,
) -> SpanishMackerelConditionsScore:
    """Calculate one internal Spanish mackerel conditions score."""
    reasons = _unavailable_reasons(value)
    if reasons:
        return UnavailableSpanishMackerelConditionsScore(
            state="unavailable",
            methodology_version=METHODOLOGY_VERSION,
            run_id=value.run_id,
            location_id=value.location_id,
            forecast_time=value.forecast_time,
            unavailable_reasons=tuple(reasons),
        )

    forecast_time = value.forecast_time
    display_timezone = value.display_timezone
    assert forecast_time is not None
    assert isinstance(display_timezone, str)

    local_forecast_date = _local_forecast_date(
        forecast_time,
        display_timezone,
    )
    if local_forecast_date is None:
        return UnavailableSpanishMackerelConditionsScore(
            state="unavailable",
            methodology_version=METHODOLOGY_VERSION,
            run_id=value.run_id,
            location_id=value.location_id,
            forecast_time=forecast_time,
            unavailable_reasons=("local_forecast_date_unavailable",),
        )
    wind_speed = _decimal(value.wind_speed_10m)
    wind_gusts = _decimal(value.wind_gusts_10m)
    wave_height = _decimal(value.wave_height)
    sea_surface_temperature = _decimal(value.sea_surface_temperature)

    seasonal_alignment = _seasonal_alignment(local_forecast_date)
    thermal_alignment = _interpolate(
        sea_surface_temperature,
        (
            (Decimal("12"), Decimal("0")),
            (Decimal("14"), Decimal("25")),
            (Decimal("16"), Decimal("50")),
            (Decimal("18"), Decimal("75")),
            (Decimal("20"), Decimal("100")),
        ),
    )
    biological_alignment = (
        Decimal("0.70") * seasonal_alignment
        + Decimal("0.30") * min(seasonal_alignment, thermal_alignment)
    )
    effective_wind_kmh = max(wind_speed, Decimal("0.60") * wind_gusts)
    wind_fishability = _interpolate(
        effective_wind_kmh,
        (
            (Decimal("15"), Decimal("100")),
            (Decimal("25"), Decimal("80")),
            (Decimal("35"), Decimal("50")),
            (Decimal("45"), Decimal("20")),
            (Decimal("55"), Decimal("0")),
        ),
    )
    wave_fishability = _interpolate(
        wave_height,
        (
            (Decimal("0.5"), Decimal("100")),
            (Decimal("1.0"), Decimal("80")),
            (Decimal("1.5"), Decimal("50")),
            (Decimal("2.0"), Decimal("20")),
            (Decimal("2.5"), Decimal("0")),
        ),
    )
    practical_fishability = min(wind_fishability, wave_fishability)
    score_unrounded = biological_alignment * (
        Decimal("0.25")
        + Decimal("0.75") * practical_fishability / Decimal("100")
    )
    score = int(
        _clamp(score_unrounded).to_integral_value(rounding=ROUND_HALF_UP)
    )

    positive_factors, limiting_factors = _factor_identifiers(
        seasonal_alignment,
        thermal_alignment,
        wind_fishability,
        wave_fishability,
    )
    factors = _factor_selections(
        seasonal_alignment,
        thermal_alignment,
        wind_fishability,
        wave_fishability,
    )
    return AvailableSpanishMackerelConditionsScore(
        state="available",
        methodology_version=METHODOLOGY_VERSION,
        run_id=value.run_id,
        location_id=value.location_id,
        forecast_time=forecast_time,
        local_forecast_date=local_forecast_date,
        score=score,
        score_band=_score_band(score),
        seasonal_alignment=seasonal_alignment,
        thermal_alignment=thermal_alignment,
        biological_alignment=biological_alignment,
        effective_wind_kmh=effective_wind_kmh,
        wind_fishability=wind_fishability,
        wave_fishability=wave_fishability,
        practical_fishability=practical_fishability,
        confidence=_confidence(value.location_id),
        positive_factors=positive_factors,
        limiting_factors=limiting_factors,
        unknown_factors=_UNKNOWN_FACTORS,
        factors=factors,
    )


def _unavailable_reasons(
    value: SpanishMackerelConditionsInput,
) -> list[str]:
    reasons = []
    if _APPROVED_LOCATION_CONTEXTS.get(value.location_id) != value.fishing_context:
        reasons.append("location_not_applicable")

    timezone = _timezone(value.display_timezone)
    if value.display_timezone is None or value.display_timezone == "":
        reasons.append("display_timezone_missing")
    elif timezone is None:
        reasons.append("display_timezone_invalid")

    if not _is_timezone_aware(value.forecast_time):
        reasons.append("forecast_time_invalid")

    for source_name, status in (
        ("weather", value.weather_status),
        ("wave", value.wave_status),
        ("sst", value.sst_status),
    ):
        if status is None:
            reasons.append(f"{source_name}_source_missing")
        elif status != "success":
            reasons.append(f"{source_name}_source_not_success")

    for field_name, field_value, minimum, maximum in (
        ("wind_speed_10m", value.wind_speed_10m, Decimal("0"), None),
        ("wind_gusts_10m", value.wind_gusts_10m, Decimal("0"), None),
        ("wave_height", value.wave_height, Decimal("0"), None),
        (
            "sea_surface_temperature",
            value.sea_surface_temperature,
            Decimal("-2"),
            Decimal("40"),
        ),
    ):
        if field_value is None:
            reasons.append(f"{field_name}_missing")
        elif not _is_finite_number(field_value):
            reasons.append(f"{field_name}_invalid")
        else:
            numeric_value = _decimal(field_value)
            if numeric_value < minimum or (
                maximum is not None and numeric_value > maximum
            ):
                reasons.append(f"{field_name}_invalid")

    return reasons


def _timezone(value: object) -> ZoneInfo | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def _local_forecast_date(
    forecast_time: datetime,
    display_timezone: str,
) -> date | None:
    try:
        return forecast_time.astimezone(ZoneInfo(display_timezone)).date()
    except (OverflowError, ValueError):
        return None


def _is_timezone_aware(value: datetime | None) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, TypeError, ValueError):
        return False


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _seasonal_alignment(local_forecast_date: date) -> Decimal:
    if (
        local_forecast_date < date(local_forecast_date.year, 3, 1)
        or local_forecast_date > date(local_forecast_date.year, 11, 30)
    ):
        return Decimal("0")
    return _interpolate(
        Decimal(local_forecast_date.toordinal()),
        tuple(
            (
                Decimal(date(local_forecast_date.year, month, day).toordinal()),
                Decimal(score),
            )
            for month, day, score in (
                (3, 1, 0),
                (4, 1, 40),
                (5, 1, 90),
                (5, 15, 100),
                (9, 30, 100),
                (10, 31, 60),
                (11, 30, 0),
            )
        ),
    )


def _interpolate(
    value: Decimal,
    anchors: tuple[tuple[Decimal, Decimal], ...],
) -> Decimal:
    if value <= anchors[0][0]:
        return anchors[0][1]
    if value >= anchors[-1][0]:
        return anchors[-1][1]

    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:], strict=True):
        if x0 <= value <= x1:
            return y0 + ((value - x0) / (x1 - x0)) * (y1 - y0)

    raise AssertionError("anchors must cover the input value")


def _clamp(value: Decimal) -> Decimal:
    return min(max(value, Decimal("0")), Decimal("100"))


def _score_band(score: int) -> str:
    if score <= 19:
        return "very_limited_alignment"
    if score <= 39:
        return "limited_alignment"
    if score <= 59:
        return "mixed_conditions"
    if score <= 79:
        return "favorable_alignment"
    return "strong_alignment"


def _confidence(location_id: str) -> tuple[ConfidenceDimension, ...]:
    location_state = (
        "moderate" if location_id == "ocracoke_ramp_72" else "high"
    )
    return (
        ConfidenceDimension("species_identity_confidence", "high"),
        ConfidenceDimension(
            "location_applicability_confidence",
            location_state,
        ),
        ConfidenceDimension("environmental_source_confidence", "moderate"),
        ConfidenceDimension("seasonal_evidence_confidence", "high"),
        ConfidenceDimension("habitat_data_confidence", "moderate"),
        ConfidenceDimension("biological_observation_confidence", "low"),
        ConfidenceDimension("fishability_data_confidence", "moderate"),
        ConfidenceDimension("overall_interpretation_confidence", "moderate"),
    )


def _factor_identifiers(
    seasonal_alignment: Decimal,
    thermal_alignment: Decimal,
    wind_fishability: Decimal,
    wave_fishability: Decimal,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    positive = []
    limiting = []
    if seasonal_alignment >= Decimal("80"):
        positive.append("seasonal_alignment")
    else:
        limiting.append("seasonal_alignment")
    if (
        seasonal_alignment > Decimal("0")
        and thermal_alignment >= seasonal_alignment
    ):
        positive.append("thermal_context")
    elif thermal_alignment < seasonal_alignment:
        limiting.append("thermal_context")
    if wind_fishability >= Decimal("80"):
        positive.append("wind_fishability")
    else:
        limiting.append("wind_fishability")
    if wave_fishability >= Decimal("80"):
        positive.append("wave_fishability")
    else:
        limiting.append("wave_fishability")
    return tuple(positive), tuple(limiting)


def _factor_selections(
    seasonal_alignment: Decimal,
    thermal_alignment: Decimal,
    wind_fishability: Decimal,
    wave_fishability: Decimal,
) -> tuple[FactorSelection, ...]:
    factors = []
    factors.append(
        FactorSelection(
            "seasonal_alignment",
            "positive" if seasonal_alignment >= Decimal("80") else "limiting",
        )
    )
    if (
        seasonal_alignment > Decimal("0")
        and thermal_alignment >= seasonal_alignment
    ):
        factors.append(FactorSelection("thermal_context", "positive"))
    elif thermal_alignment < seasonal_alignment:
        factors.append(FactorSelection("thermal_context", "limiting"))
    factors.append(
        FactorSelection(
            "wind_fishability",
            "positive" if wind_fishability >= Decimal("80") else "limiting",
        )
    )
    factors.append(
        FactorSelection(
            "wave_fishability",
            "positive" if wave_fishability >= Decimal("80") else "limiting",
        )
    )
    factors.extend(FactorSelection(identifier, "unknown") for identifier in _UNKNOWN_FACTORS)
    return tuple(factors)
