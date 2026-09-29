from pydantic import BaseModel

from validation.service import ServiceResponseSchema


class StationResponseSchema(BaseModel):
    id: int
    name: str | None = None
    address: str | None = None
    active: bool

    class Config:
        from_attributes = True


class StationCreateSchema(BaseModel):
    name: str
    address: str


class StationUpdateSchema(BaseModel):
    name: str | None = None
    address: str | None = None
    active: bool | None = None


class NearestStationResponseSchema(BaseModel):
    id: int
    name: str
    address: str
    active: bool
    distance_km: float
    services: list[ServiceResponseSchema] = []

    class Config:
        from_attributes = True
