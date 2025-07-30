from uuid import UUID

from typing import TypedDict

from ed_core.application.features.common.dtos.location_dto import LocationDto


class BusinessDto(TypedDict):
    id: UUID
    business_name: str
    owner_first_name: str
    owner_last_name: str
    phone_number: str
    email: str
    location: LocationDto
