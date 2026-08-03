from datetime import datetime, timezone
from typing import Any

import httpx
import pytest

from saltbytes.api import (
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


def test_build_forecast_params_uses_weather_request_relationship() -> None:
    params = build_forecast_params(coastal_location())

    assert params == {
        "latitude": 34.6933,
        "longitude": -76.7117,
        "models": "ncep_nbm_conus",
        "forecast_days": 7,
        "hourly": (
            "wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
            "precipitation_probability,precipitation,cloud_cover"
        ),
        "timezone": "GMT",
    }


def test_build_wave_params_uses_marine_request_relationship() -> None:
    params = build_wave_params(coastal_location())

    assert params == {
        "latitude": 34.65,
        "longitude": -76.697,
        "models": "meteofrance_wave",
        "forecast_days": 7,
        "hourly": "wave_height,wave_direction,wave_period",
        "timezone": "GMT",
    }


def test_build_sst_params_uses_product_specific_relationship() -> None:
    params = build_sst_params(coastal_location())

    assert params == {
        "latitude": 34.65,
        "longitude": -76.697,
        "models": "meteofrance_currents",
        "forecast_days": 7,
        "hourly": "sea_surface_temperature",
        "timezone": "GMT",
    }


def test_build_tide_params_uses_accepted_noaa_contract_and_padding() -> None:
    params = build_tide_params(coastal_location(), datetime(2026, 7, 28, 10, tzinfo=timezone.utc))

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
            assert params == build_forecast_params(coastal_location())
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_forecast(coastal_location())

    assert result == payload


def test_fetch_forecast_rejects_non_object_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

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
            nonlocal attempts
            attempts += 1
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(
        ValueError,
        match="forecast api response must contain a json object",
    ):
        fetch_forecast(coastal_location())

    assert attempts == 1


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
        fetch_forecast(coastal_location())


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
            assert params == build_wave_params(coastal_location())
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_wave_forecast(coastal_location())

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
        fetch_wave_forecast(coastal_location())


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
        fetch_wave_forecast(coastal_location())


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
            assert params == build_sst_params(coastal_location())
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_sst_forecast(coastal_location())

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
        fetch_sst_forecast(coastal_location())


def test_fetch_tide_predictions_returns_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "predictions": [
            {"t": "2026-07-27 18:00", "v": "0.1", "type": "L"},
            {"t": "2026-07-28 00:00", "v": "1.2", "type": "H"},
        ]
    }
    params = build_tide_params(coastal_location(), datetime(2026, 7, 28, tzinfo=timezone.utc))

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
            assert url == (
                "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
            )
            assert params == build_tide_params(
                coastal_location(),
                datetime(2026, 7, 28, tzinfo=timezone.utc),
            )
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = fetch_tide_predictions(params)

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
        fetch_tide_predictions({})


def test_fetch_forecast_recovers_on_third_timeout_attempt(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    payload = {"hourly": {"time": []}}
    attempts = 0
    delays: list[float] = []
    clients: list[Any] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return payload

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            assert timeout == 2.5
            self.closed = False
            clients.append(self)

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            self.closed = True

        def get(
            self,
            url: str,
            params: dict[str, Any],
        ) -> FakeResponse:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise httpx.ConnectTimeout("TLS handshake timed out")
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    monkeypatch.setattr("saltbytes.api.time.sleep", delays.append)
    caplog.set_level("INFO", logger="saltbytes.api")

    assert fetch_forecast(coastal_location(), timeout_seconds=2.5,
    ) == payload
    assert attempts == 3
    assert delays == [1.0, 2.0]
    assert clients[0].closed is True
    assert [record.getMessage() for record in caplog.records] == [
        "open meteo request recovered source=weather "
        "location=fort_macon_ocean attempts=3 previous_error=ConnectTimeout"
    ]


def test_fetch_wave_forecast_raises_after_timeout_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    delays: list[float] = []

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(
            self,
            url: str,
            params: dict[str, Any],
        ) -> None:
            nonlocal attempts
            attempts += 1
            raise httpx.ReadTimeout("response timed out")

    monkeypatch.setattr(httpx, "Client", FakeClient)
    monkeypatch.setattr("saltbytes.api.time.sleep", delays.append)

    with pytest.raises(httpx.ReadTimeout, match="response timed out"):
        fetch_wave_forecast(coastal_location())

    assert attempts == 3
    assert delays == [1.0, 2.0]


def test_timeout_followed_by_http_error_does_not_log_recovery(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    request = httpx.Request("GET", "https://api.open-meteo.com")
    response = httpx.Response(status_code=503, request=request)
    attempts = 0
    delays: list[float] = []

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
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(self, url: str, params: dict[str, Any]) -> FakeResponse:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise httpx.ConnectTimeout("TLS handshake timed out")
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    monkeypatch.setattr("saltbytes.api.time.sleep", delays.append)
    caplog.set_level("INFO", logger="saltbytes.api")

    with pytest.raises(httpx.HTTPStatusError, match="server error"):
        fetch_forecast(coastal_location())

    assert attempts == 2
    assert delays == [1.0]
    assert caplog.records == []


def test_fetch_sst_forecast_does_not_retry_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("GET", "https://marine-api.open-meteo.com")
    response = httpx.Response(status_code=500, request=request)
    attempts = 0

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
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(
            self,
            url: str,
            params: dict[str, Any],
        ) -> FakeResponse:
            nonlocal attempts
            attempts += 1
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(httpx.HTTPStatusError, match="server error"):
        fetch_sst_forecast(coastal_location())

    assert attempts == 1


def test_open_meteo_fetches_use_caller_owned_client(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    clients: list[Any] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {"hourly": {"time": []}}

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout
            self.closed = False
            clients.append(self)

        def get(
            self,
            url: str,
            params: dict[str, Any],
        ) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    client = FakeClient(timeout=3.0)
    caplog.set_level("INFO", logger="saltbytes.api")

    fetch_forecast(coastal_location(), client=client)
    fetch_wave_forecast(coastal_location(), client=client)
    fetch_sst_forecast(coastal_location(), client=client)

    assert len(clients) == 1
    assert clients[0].timeout == 3.0
    assert clients[0].closed is False
    assert caplog.records == []


def test_fetch_forecast_does_not_retry_unrelated_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(self, url: str, params: dict[str, Any]) -> None:
            nonlocal attempts
            attempts += 1
            raise RuntimeError("unexpected failure")

    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(RuntimeError, match="unexpected failure"):
        fetch_forecast(coastal_location())

    assert attempts == 1
