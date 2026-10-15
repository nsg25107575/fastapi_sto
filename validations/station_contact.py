from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StationContactCreateSchema(BaseModel):
    station_id: int = Field(gt=0)
    type: str = Field(min_length=1, max_length=50)
    value: str = Field(min_length=1, max_length=255)


class StationContactUpdateSchema(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=50)
    value: str | None = Field(default=None, min_length=1, max_length=255)


class StationContactResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    type: str
    value: str
    created_at: datetime
    updated_at: datetime
