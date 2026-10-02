from pydantic import BaseModel, ConfigDict


class ServiceResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    price: float
