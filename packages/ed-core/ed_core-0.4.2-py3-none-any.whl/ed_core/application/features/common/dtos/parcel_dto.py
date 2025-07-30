from ed_domain.core.entities.parcel import ParcelSize
from typing import TypedDict


class ParcelDto(TypedDict):
    size: ParcelSize
    length: float
    width: float
    height: float
    weight: float
    fragile: bool
