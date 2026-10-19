from fastapi import HTTPException
from starlette.status import (
    HTTP_409_CONFLICT,
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_403_FORBIDDEN,
)

from i18n.dependency_translator import t


def app_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("app.not_found", locale=locale),
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


# --- Order ------------------------------------------------------------------------
def order_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("order.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def order_customer_id_doesnt_refer_to_customer_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=t("order.customer_id_doesnt_refer_to_customer", locale=locale),
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


# --- Rating ------------------------------------------------------------------------

def rating_value_out_of_range_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=t("review.rating_out_of_range", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def rating_user_id_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("review.user_id_not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def rating_station_id_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("review.station_id_not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Review ------------------------------------------------------------------------
def review_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("review.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def review_forbidden_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail=t("review.forbidden", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def review_already_exists_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=t("review.already_exists", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Customer ------------------------------------------------------------------------
def customer_not_found_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("customer.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def customer_not_found_unauthorized_exception(
        locale: str | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail=t("customer.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def customer_cookie_missing_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail=t("customer.cookie_missing", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_auth_cookie_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail=t("auth.invalid_cookie", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Order ------------------------------------------------------------------------
def order_forbidden_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail=t("order.forbidden", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def order_not_found(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("order.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"}
    )


# --- Chat ------------------------------------------------------------------------
def chat_room_archived_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail=t("chat.room_archived", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Station ------------------------------------------------------------------------
def station_forbidden_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail=t("station.forbidden", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Station contact -------------------------------------------------------------
def station_contact_not_found_exception(
        locale: str | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail=t("station_contact.not_found", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


def admin_forbidden_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail=t("station.admin_forbidden", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Services -------------------------------------------------------------
def service_id_doesnt_belong_to_station_exception(locale: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=t("services.service_id_doesnt_belong_to_station", locale=locale),
        headers={"WWW-Authenticate": "Bearer"},
    )
