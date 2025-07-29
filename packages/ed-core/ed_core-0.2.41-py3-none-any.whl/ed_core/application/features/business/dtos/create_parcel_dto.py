from typing import TypedDict

from ed_domain.core.entities.parcel import ParcelSize


class CreateParcelDto(TypedDict):
    size: ParcelSize
    length: float
    width: float
    height: float
    weight: float
    fragile: bool
