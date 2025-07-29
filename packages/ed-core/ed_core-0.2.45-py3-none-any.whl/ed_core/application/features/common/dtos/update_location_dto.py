from typing import TypedDict


class UpdateLocationDto(TypedDict):
    address: str
    latitude: float
    longitude: float
    postal_code: str
