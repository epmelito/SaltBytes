"""Imperial display conversions for user-facing reports.

Canonical forecast values remain metric through ingestion, storage, and
assessment calculations. These helpers are only for rendering reports.
"""

from decimal import ROUND_HALF_UP, Decimal


def format_display_number(value: float, precision: int = 1) -> str:
    """Format a converted float using JavaScript ``Number.toFixed`` rounding."""
    if value == 0:
        value = 0.0
    quantum = Decimal(1).scaleb(-precision)
    rounded = Decimal.from_float(value).quantize(quantum, rounding=ROUND_HALF_UP)
    return f"{rounded:.{precision}f}"


def celsius_to_fahrenheit(value: float | None) -> float | None:
    return None if value is None else value * 9 / 5 + 32


def kilometers_per_hour_to_miles_per_hour(value: float | None) -> float | None:
    return None if value is None else value / 1.609344


def meters_to_feet(value: float | None) -> float | None:
    return None if value is None else value * 3.2808398950131


def millimeters_to_inches(value: float | None) -> float | None:
    return None if value is None else value / 25.4
