from pydantic import BaseModel


class CustomerCreate(BaseModel):
    ip: str
    device_hash: str
    lat: float
    lng: float
    public_data: dict

    class Config:
        from_attributes = True


class CustomerResponse(BaseModel):
    ip: str
    device_hash: str
    public_data: dict

    class Config:
        from_attributes = True
