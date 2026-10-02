from pydantic import BaseModel, ConfigDict


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
    model_config = ConfigDict(from_attributes=True)

    ip: str
    device_hash: str
    lat: float
    lng: float
    public_data: dict


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Needed by the client to place an order (POST /orders) referencing
    # this customer afterward -- without it, the "find nearest station ->
    # order a service" flow has no way to carry the customer's identity
    # from this call into the next one.
    id: int
    ip: str
    device_hash: str
    public_data: dict
