"""
`exceptions` package.

Re-exports the shared HTTPException instances from
`exceptions/exceptions.py` so existing imports across the codebase
(`from exceptions import StationNotFoundException`, etc.) keep working
unchanged after the `exceptions.py` -> `exceptions/` module refactor.
"""
from exceptions.exceptions import (
    StationNotFoundException,
    InvalidCoordinateException,
    DuplicateEmailException,
    DuplicateStationException,
    TokenExpiredException,
    OrderNotFoundException,
    InvalidOrderServiceException,
)

__all__ = [
    "StationNotFoundException",
    "InvalidCoordinateException",
    "DuplicateEmailException",
    "DuplicateStationException",
    "TokenExpiredException",
    "OrderNotFoundException",
    "InvalidOrderServiceException",
]
