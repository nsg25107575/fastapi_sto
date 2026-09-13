from pydantic import BaseModel


class CustomerCreate(BaseModel):
    lat: float
    lng: float


class CustomerResponse(BaseModel):
    id: int
    ip: str
    device_hash: str
    lat: float
    lng: float

    class Config:
        from_attributes = True
