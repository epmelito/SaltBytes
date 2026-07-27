from typing import Any

import httpx
import pytest

from forecast_ops.api import build_forecast_params, fetch_forecast


def test_build_forecast_params() -> None:
    location = {
        "id": "prague",
        "name": "Prague",
        "latitude": 50.0755,
        "longitude": 14.4378,
    }
    api_config = {
        "base_url": "https://api.open-meteo.com/v1/forecast",
        "forecast_days": 2,
        "hourly_fields": [
            "temperature_2m",
            "precipitation_probability",
            "wind_speed_10m",
        ],
    }

    params = build_forecast_params(location, api_config)

    assert params == {
        "latitude": 50.0755,
        "longitude": 14.4378,
        "forecast_days": 2,
        "hourly": "temperature_2m,precipitation_probability,wind_speed_10m",
        "timezone": "auto",
    }


def test_fetch_forecast_returns_json_object(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "latitude": 50.08,
        "longitude": 14.44,
        "hourly": {
            "time": ["2026-07-28T00:00"],
            "temperature_2m": [18.2],
        },
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return payload

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(
            self,
            url: str,
            params: dict[str, Any],
        ) -> FakeResponse:
            assert url == "https://api.open-meteo.com/v1/forecast"
            assert params["latitude"] == 50.0755
            assert params["longitude"] == 14.4378
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    location = {
        "latitude": 50.0755,
        "longitude": 14.4378,
    }
    api_config = {
        "base_url": "https://api.open-meteo.com/v1/forecast",
        "forecast_days": 2,
        "hourly_fields": ["temperature_2m"],
    }

    result = fetch_forecast(location, api_config)

    assert result == payload


def test_fetch_forecast_rejects_non_object_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> list[str]:
            return ["unexpected"]

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(
            self,
            url: str,
            params: dict[str, Any],
        ) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    location = {
        "latitude": 50.0755,
        "longitude": 14.4378,
    }
    api_config = {
        "base_url": "https://api.open-meteo.com/v1/forecast",
        "forecast_days": 2,
        "hourly_fields": ["temperature_2m"],
    }

    with pytest.raises(
        ValueError,
        match="forecast api response must contain a json object",
    ):
        fetch_forecast(location, api_config)