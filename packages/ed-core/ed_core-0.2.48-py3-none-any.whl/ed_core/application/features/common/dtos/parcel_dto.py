from ed_domain.core.entities.parcel import ParcelSize
from pydantic import BaseModel


class ParcelDto(BaseModel):
    size: ParcelSize
    length: float
    width: float
    height: float
    weight: float
    fragile: bool
