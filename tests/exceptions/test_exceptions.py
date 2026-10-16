import pytest
from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_401_UNAUTHORIZED

from exceptions.exceptions import (
    station_not_found_exception,
    invalid_coordinate_exception,
    duplicate_email_exception,
    duplicate_station_exception,
    token_expired_exception,
    order_not_found_exception,
    invalid_order_service_exception,
    geocoding_failed_exception,
)
from i18n.context import reset_current_locale, set_current_locale


@pytest.fixture(autouse=True)
def restore_locale():
    token = set_current_locale("en")
    yield
    reset_current_locale(token)


def test_station_not_found_exception_returns_new_instance_each_call():
    first = station_not_found_exception(locale="en")
    second = station_not_found_exception(locale="en")
    assert first is not second  # not a module-level singleton


def test_station_not_found_exception_has_correct_status_and_translated_detail():
    exc = station_not_found_exception(locale="en")
    assert isinstance(exc, HTTPException)
    assert exc.status_code == HTTP_404_NOT_FOUND
    assert exc.detail == "Station not found"


def test_station_not_found_exception_translates_for_uk_locale():
    exc = station_not_found_exception(locale="uk")
    assert exc.detail != "Station not found"  # must be a translation, not fallback text


def test_station_not_found_exception_preserves_www_authenticate_header():
    exc = station_not_found_exception(locale="en")
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_station_not_found_exception_uses_context_locale_when_not_passed(monkeypatch):
    set_current_locale("uk")
    exc = station_not_found_exception()  # without locale -> from context
    assert exc.detail != "Station not found"


def test_invalid_coordinate_exception_status_and_detail():
    exc = invalid_coordinate_exception(locale="en")
    assert exc.status_code == HTTP_400_BAD_REQUEST
    assert exc.detail == "Invalid coordinates"


def test_duplicate_email_exception_status_and_detail():
    exc = duplicate_email_exception(locale="en")
    assert exc.status_code == HTTP_409_CONFLICT
    assert exc.detail == "Email already in use"


def test_duplicate_station_exception_status_and_detail():
    exc = duplicate_station_exception(locale="en")
    assert exc.status_code == HTTP_409_CONFLICT
    assert exc.detail == "Station with this name and address already exists"


def test_token_expired_exception_status_and_detail():
    exc = token_expired_exception(locale="en")
    assert exc.status_code == HTTP_401_UNAUTHORIZED
    assert exc.detail == "The session has expired or has been invalidated."


def test_order_not_found_exception_status_and_detail():
    exc = order_not_found_exception(locale="en")
    assert exc.status_code == HTTP_404_NOT_FOUND
    assert exc.detail == "Order not found"


def test_invalid_order_service_exception_status_and_detail():
    exc = invalid_order_service_exception(locale="en")
    assert exc.status_code == HTTP_400_BAD_REQUEST
    assert exc.detail == "The specified service does not belong to the specified station"


def test_geocoding_failed_exception_status_and_detail():
    exc = geocoding_failed_exception(locale="en")
    assert exc.status_code == HTTP_400_BAD_REQUEST
    assert exc.detail == "Could not resolve coordinates for the given address"
