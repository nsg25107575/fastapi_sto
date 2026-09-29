from pydantic import BaseModel


class ServiceResponseSchema(BaseModel):
    name: str
    price: float | None = None

    class Config:
        from_attributes = True
