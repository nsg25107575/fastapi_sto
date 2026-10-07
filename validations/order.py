from pydantic import BaseModel, ConfigDict

from models.order import OrderStatus


class OrderCreateSchema(BaseModel):
    """Request body for POST /orders -- a customer orders a specific
    service at a specific station. `customer_id` is the id returned by
    POST /customer (see routers/customer.py); the client is expected to
    have already called GET /stations/nearest to pick a station and
    service."""
    customer_id: int
    station_id: int
    station_service_id: int


class OrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    station_service_id: int
    status: OrderStatus


class OrderStatusUpdateSchema(BaseModel):
    status: OrderStatus
