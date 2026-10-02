from fastapi import HTTPException
from starlette.status import HTTP_409_CONFLICT, HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

StationNotFoundException = HTTPException(
    status_code=HTTP_404_NOT_FOUND,
    detail="Station not found",
    headers={"WWW-Authenticate": "Bearer"},
)

InvalidCoordinateException = HTTPException(
    status_code=HTTP_400_BAD_REQUEST,
    detail="Invalid coordinates",
    headers={"WWW-Authenticate": "Bearer"},
)

DuplicateEmailException = HTTPException(
    status_code=HTTP_409_CONFLICT,
    detail="Email already in use",
    headers={"WWW-Authenticate": "Bearer"},
)

DuplicateStationException = HTTPException(
    status_code=HTTP_409_CONFLICT,
    detail="Station with this name and address already exists",
    headers={"WWW-Authenticate": "Bearer"},
)

TokenExpiredException = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="The session has expired or has been invalidated.",
    headers={"WWW-Authenticate": "Bearer"},
)
