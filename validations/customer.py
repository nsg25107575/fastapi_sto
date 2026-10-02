from pydantic import BaseModel


class CustomerCreate(BaseModel):
    """Request body for POST /customer — ip and device_hash are generated
    server-side (see routers/customer.py), so they are intentionally NOT
    part of the client-facing input schema."""
    lat: float
    lng: float
    public_data: dict


class CustomerModelAttrs(BaseModel):
    """Internal shape mirroring the full CustomerModel row, kept for
    documentation/reference — not used directly as a request schema."""
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
