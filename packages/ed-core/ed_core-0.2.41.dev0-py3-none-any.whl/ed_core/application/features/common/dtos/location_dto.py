from pydantic import BaseModel


class LocationDto(BaseModel):
    address: str
    latitude: float
    longitude: float
    postal_code: str
    city: str
