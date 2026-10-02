"""Unit tests for the geocoding helper -- resolves a free-text address
into (lat, lng) via the configured provider (OpenStreetMap Nominatim by
default). Network calls are mocked; no real HTTP requests are made.
"""
import httpx
import pytest

from services.geocoding import GeocodingError, geocode_address


class _FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=httpx.Request("GET", "https://example.test"), response=self
            )


def test_geocode_address_success(monkeypatch):
    def fake_get(url, params, headers, timeout):
        return _FakeResponse(200, [{"lat": "50.4501000", "lon": "30.5234000"}])

    monkeypatch.setattr("services.geocoding.httpx.get", fake_get)

    lat, lng = geocode_address("1 Khreshchatyk St, Kyiv")

    assert lat == pytest.approx(50.4501)
    assert lng == pytest.approx(30.5234)


def test_geocode_address_no_results_raises(monkeypatch):
    def fake_get(url, params, headers, timeout):
        return _FakeResponse(200, [])

    monkeypatch.setattr("services.geocoding.httpx.get", fake_get)

    with pytest.raises(GeocodingError):
        geocode_address("a place that does not exist anywhere")


def test_geocode_address_http_error_raises(monkeypatch):
    def fake_get(url, params, headers, timeout):
        return _FakeResponse(503, [])

    monkeypatch.setattr("services.geocoding.httpx.get", fake_get)

    with pytest.raises(GeocodingError):
        geocode_address("1 Main St")


def test_geocode_address_network_error_raises(monkeypatch):
    def fake_get(url, params, headers, timeout):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr("services.geocoding.httpx.get", fake_get)

    with pytest.raises(GeocodingError):
        geocode_address("1 Main St")


def test_geocode_address_rejects_blank_address():
    with pytest.raises(ValueError):
        geocode_address("")

    with pytest.raises(ValueError):
        geocode_address("   ")
