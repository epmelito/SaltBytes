from datetime import datetime, timezone
from typing import Any

import httpx
import pytest

from forecast_ops.api import (
    build_forecast_params,
    build_sst_params,
    build_tide_params,
    build_wave_params,
    fetch_forecast,
    fetch_sst_forecast,
    fetch_tide_predictions,
    fetch_wave_forecast,
)


def coastal_location() -> dict[str, Any]:
    return {
        "id": "fort_macon_ocean",
        "name": "Fort Macon State Park, ocean side",
        "fishing_context": "surf",
        "display_coordinate": {
            "latitude": 34.6949437,
            "longitude": -76.697391,
        },
        "weather": {
            "request_coordinate": {
                "latitude": 34.6933,
                "longitude": -76.7117,
            },
            "expected_returned_coordinate": {
                "latitude": 34.68586,
                "longitude": -76.717896,
            },
            "coastal_regime": "Atlantic coastal grid",
        },
        "wave": {
            "request_coordinate": {
                "latitude": 34.65,
                "longitude": -76.697,
            },
            "expected_returned_coordinate": {
                "latitude": 34.625,
                "longitude": -76.70833,
            },
        },
        "sst": {
            "request_coordinate": {
                "latitude": 34.65,
                "longitude": -76.697,
            },
            "expected_returned_coordinate": {
                "latitude": 34.625,
                "longitude": -76.70833,
            },
            "coastal_regime": "Atlantic-facing marine grid",
        },
        "tide": {
            "station_id": "8656590",
        },
    }


def atmospheric_api_config() -> dict[str, Any]:
    return {
        "base_url": "https://api.open-meteo.com/v1/forecast",
        "model": "ncep_nbm_conus",
        "forecast_days": 7,
        "hourly_fields": [
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "precipitation_probability",
            "precipitation",
        ],
    }


def wave_api_config() -> dict[str, Any]:
    return {
        "base_url": "https://marine-api.open-meteo.com/v1/marine",
        "model": "meteofrance_wave",
        "forecast_days": 7,
        "hourly_fields": [
            "wave_height",
            "wave_direction",
            "wave_period",
        ],
    }


def sst_api_config() -> dict[str, Any]:
    return {
        "base_url": "https://marine-api.open-meteo.com/v1/marine",
        "model": "meteofrance_currents",
        "forecast_days": 7,
        "hourly_fields": ["sea_surface_temperature"],
    }


def tide_api_config() -> dict[str, Any]:
    return {
        "base_url": (
            "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        ),
        "product": "predictions",
        "interval": "hilo",
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "format": "json",
        "forecast_days": 7,
    }


def test_build_forecast_params_uses_weather_request_relationship() -> None:
    params = build_forecast_params(
        coastal_location(),
        atmospheric_api_config(),
    )

    assert params == {
        "latitude": 34.6933,
        "longitude": -76.7117,
        "models": "ncep_nbm_conus",
        "forecast_days": 7,
        "hourly": (
            "wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
            "precipitation_probability,precipitation"
        ),
        "timezone": "GMT",
    }


def test_build_wave_params_uses_marine_request_relationship() -> None:
    params = build_wave_params(
        coastal_location(),
        wave_api_config(),
    )

    assert params == {
        "latitude": 34.65,
        "longitude": -76.697,
        "models": "meteofrance_wave",
        "forecast_days": 7,
        "hourly": "wave_height,wave_direction,wave_period",
        "timezone": "GMT",
    }


def test_build_sst_params_uses_product_specific_relationship() -> None:
    params = build_sst_params(
        coastal_location(),
        sst_api_config(),
    )

    assert params == {
        "latitude": 34.65,
        "longitude": -76.697,
        "models": "meteofrance_currents",
        "forecast_days": 7,
        "hourly": "sea_surface_temperature",
        "timezone": "GMT",
    }


def test_build_tide_params_uses_accepted_noaa_contract_and_padding() -> None:
    params = build_tide_params(
        coastal_location(),
        tide_api_config(),
        datetime(2026, 7, 28, 10, tzinfo=timezone.utc),
    )

    assert params == {
        "station": "8656590",
        "begin_date": "20260727",
        "end_date": "20260805",
        "product": "predictions",
        "interval": "hilo",
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "format": "json",
    }


def test_fetch_forecast_returns_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "latitude": 34.68586,
        "longitude": -76.717896,
        "timezone": "GMT",
        "hourly": {
            "time": ["2026-07-28T00:00"],
            "wind_speed_10m": [18.2],
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
            assert params == build_forecast_params(
                coastal_location(),
                atmospheric_api_config(),
            )
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_forecast(
        coastal_location(),
        atmospheric_api_config(),
    )

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

    with pytest.raises(
        ValueError,
        match="forecast api response must contain a json object",
    ):
        fetch_forecast(
            coastal_location(),
            atmospheric_api_config(),
        )


def test_fetch_forecast_propagates_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request(
        "GET",
        "https://api.open-meteo.com/v1/forecast",
    )
    response = httpx.Response(
        status_code=500,
        request=request,
    )

    class FakeResponse:
        def raise_for_status(self) -> None:
            raise httpx.HTTPStatusError(
                "server error",
                request=request,
                response=response,
            )

        def json(self) -> dict[str, Any]:
            return {}

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

    with pytest.raises(httpx.HTTPStatusError):
        fetch_forecast(
            coastal_location(),
            atmospheric_api_config(),
        )


def test_fetch_wave_forecast_returns_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "latitude": 34.625,
        "longitude": -76.70833,
        "timezone": "GMT",
        "hourly": {
            "time": ["2026-07-28T00:00"],
            "wave_height": [1.2],
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
            assert url == "https://marine-api.open-meteo.com/v1/marine"
            assert params == build_wave_params(
                coastal_location(),
                wave_api_config(),
            )
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_wave_forecast(
        coastal_location(),
        wave_api_config(),
    )

    assert result == payload


def test_fetch_wave_forecast_rejects_non_object_json(
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

    with pytest.raises(
        ValueError,
        match="wave forecast api response must contain a json object",
    ):
        fetch_wave_forecast(
            coastal_location(),
            wave_api_config(),
        )


def test_fetch_wave_forecast_propagates_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request(
        "GET",
        "https://marine-api.open-meteo.com/v1/marine",
    )
    response = httpx.Response(
        status_code=500,
        request=request,
    )

    class FakeResponse:
        def raise_for_status(self) -> None:
            raise httpx.HTTPStatusError(
                "server error",
                request=request,
                response=response,
            )

        def json(self) -> dict[str, Any]:
            return {}

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

    with pytest.raises(httpx.HTTPStatusError):
        fetch_wave_forecast(
            coastal_location(),
            wave_api_config(),
        )


def test_fetch_sst_forecast_returns_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "latitude": 34.625,
        "longitude": -76.70833,
        "timezone": "GMT",
        "hourly": {
            "time": ["2026-07-28T00:00"],
            "sea_surface_temperature": [25.1],
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
            assert url == "https://marine-api.open-meteo.com/v1/marine"
            assert params == build_sst_params(
                coastal_location(),
                sst_api_config(),
            )
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_sst_forecast(
        coastal_location(),
        sst_api_config(),
    )

    assert result == payload


def test_fetch_sst_forecast_rejects_non_object_json(
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

    with pytest.raises(
        ValueError,
        match="sst forecast api response must contain a json object",
    ):
        fetch_sst_forecast(
            coastal_location(),
            sst_api_config(),
        )


def test_fetch_tide_predictions_returns_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "predictions": [
            {"t": "2026-07-27 18:00", "v": "0.1", "type": "L"},
            {"t": "2026-07-28 00:00", "v": "1.2", "type": "H"},
        ]
    }
    params = build_tide_params(
        coastal_location(),
        tide_api_config(),
        datetime(2026, 7, 28, tzinfo=timezone.utc),
    )

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
            assert url == tide_api_config()["base_url"]
            assert params == build_tide_params(
                coastal_location(),
                tide_api_config(),
                datetime(2026, 7, 28, tzinfo=timezone.utc),
            )
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_tide_predictions(tide_api_config(), params)

    assert result == payload


def test_fetch_tide_predictions_rejects_non_object_json(
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

    with pytest.raises(
        ValueError,
        match="tide prediction api response must contain a json object",
    ):
        fetch_tide_predictions(tide_api_config(), {})
