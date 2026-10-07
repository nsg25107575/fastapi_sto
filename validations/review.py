from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateSchema(BaseModel):
    order_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    station_id: int
    customer_id: int
    rating: float
    comment: str | None
