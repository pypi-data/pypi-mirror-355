from uuid import UUID

from pydantic import BaseModel

from ed_core.application.features.common.dtos.location_dto import LocationDto


class BusinessDto(BaseModel):
    id: UUID
    business_name: str
    owner_first_name: str
    owner_last_name: str
    phone_number: str
    email: str
    location: LocationDto
