from pydantic import BaseModel


class ServiceResponseSchema(BaseModel):
    name: str
    price: float

    class Config:
        from_attributes = True
