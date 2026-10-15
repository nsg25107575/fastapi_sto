from typing import Literal

from pydantic import BaseModel, ConfigDict
from validations.service import ServiceResponseSchema


class StationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    address: str | None = None
    active: bool


class StationCreateSchema(BaseModel):
    name: str
    address: str


class StationUpdateSchema(BaseModel):
    name: str | None = None
    address: str | None = None
    active: bool | None = None


class NearestStationsSchema(BaseModel):
    lng: float
    lat: float


class NearestStationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    distance_km: float
    rating: float | None = None
    reviews_count: int = 0
    services: list[ServiceResponseSchema] = []


class StationModerationSchema(BaseModel):
    """Schema for station moderation requests."""

    moderation_status: Literal["approved", "rejected"]
    rejection_reason: str | None = None


class StationModerationResponseSchema(BaseModel):
    """Schema for station moderation responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    moderation_status: str
    rejection_reason: str | None = None
