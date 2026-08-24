from collections.abc import Callable

import pytest

from saltbytes.reporting.presentation import (
    celsius_to_fahrenheit,
    format_display_number,
    kilometers_per_hour_to_miles_per_hour,
    meters_to_feet,
    millimeters_to_inches,
)


@pytest.mark.parametrize(
    ("convert", "metric", "expected"),
    [
        (celsius_to_fahrenheit, 24.6, 76.28),
        (kilometers_per_hour_to_miles_per_hour, 18.5, 11.495367056),
        (meters_to_feet, 1.2, 3.937007874),
        (millimeters_to_inches, 1.5, 0.059055118),
    ],
)
def test_presentation_conversions_preserve_canonical_measurements(
    convert: Callable[[float | None], float | None],
    metric: float,
    expected: float,
) -> None:
    assert convert(metric) == pytest.approx(expected)


def test_presentation_conversions_keep_unavailable_values_unavailable() -> None:
    assert celsius_to_fahrenheit(None) is None
    assert kilometers_per_hour_to_miles_per_hour(None) is None
    assert meters_to_feet(None) is None
    assert millimeters_to_inches(None) is None


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        (72.5, 0, "73"),
        (1.005, 2, "1.00"),
        (-0.0, 2, "0.00"),
    ],
)
def test_display_rounding_matches_javascript_to_fixed(
    value: float, precision: int, expected: str
) -> None:
    assert format_display_number(value, precision) == expected
