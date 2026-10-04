from typing import TypeVar, Generic

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Pagination parameters for API requests.
    Connects to any endpoint `response_model=PaginatedResponse[AnyResponseSchema]``
    """
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    A paginated response model.
    """
    items: list[T]
    total: int
    limit: int
    offset: int
