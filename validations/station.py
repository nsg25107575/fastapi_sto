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
    services: list[ServiceResponseSchema] = []
