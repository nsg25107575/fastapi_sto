from fastapi import HTTPException
from starlette.status import (
    HTTP_409_CONFLICT,
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from i18n.dependency_translator import t


def application_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("application.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def station_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("station.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def service_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("service.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_coordinate_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=t("station.invalid_coordinates", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def duplicate_email_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_409_CONFLICT,
        detail=t("auth.email_already_in_use", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def duplicate_station_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_409_CONFLICT,
        detail=t("station.duplicate", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def token_expired_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail=t("auth.session_expired", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def order_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("order.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_order_service_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=t("order.invalid_service", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def geocoding_failed_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=t("geocoding.failed", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )
