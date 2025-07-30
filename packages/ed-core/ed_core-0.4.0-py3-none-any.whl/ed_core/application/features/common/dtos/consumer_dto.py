from typing import Optional, TypedDict
from uuid import UUID

from ed_core.application.features.common.dtos import LocationDto


class ConsumerDto(TypedDict):
    id: UUID
    first_name: str
    last_name: str
    phone_number: str
    email: Optional[str]
    location: LocationDto
    profile_image_url: str
