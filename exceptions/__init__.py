"""
`exceptions` package.

Re-exports the shared HTTPException instances from
`exceptions/exceptions.py` so existing imports across the codebase
(`from exceptions import StationNotFoundException`, etc.) keep working
unchanged after the `exceptions.py` -> `exceptions/` module refactor.
"""
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

__all__ = [
    "station_not_found_exception",
    "invalid_coordinate_exception",
    "duplicate_email_exception",
    "duplicate_station_exception",
    "token_expired_exception",
    "order_not_found_exception",
    "invalid_order_service_exception",
    "geocoding_failed_exception",
]
