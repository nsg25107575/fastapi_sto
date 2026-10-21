from pydantic import BaseModel, ConfigDict


class ServiceCreateSchema(BaseModel):
    station_id: int
    name: str
    price: float | None = None


class ServiceUpdateSchema(BaseModel):
    name: str | None = None
    price: float | None = None


class ServiceResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    price: float
