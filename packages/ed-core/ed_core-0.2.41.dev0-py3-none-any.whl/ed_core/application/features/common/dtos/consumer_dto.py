from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from ed_core.application.features.common.dtos import LocationDto


class ConsumerDto(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    phone_number: str
    email: Optional[str]
    location: LocationDto
