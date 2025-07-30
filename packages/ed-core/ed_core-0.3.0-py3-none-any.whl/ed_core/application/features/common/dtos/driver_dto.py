from typing import Optional
from uuid import UUID

from ed_domain.core.aggregate_roots import Driver
from pydantic import BaseModel

from ed_core.application.features.common.dtos.business_dto import LocationDto
from ed_core.application.features.common.dtos.car_dto import CarDto


class DriverDto(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    profile_image: str
    phone_number: str
    email: Optional[str]
    car: CarDto
    location: LocationDto

    @classmethod
    def from_driver(cls, driver: Driver) -> "DriverDto":
        return cls(
            id=driver.id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            profile_image=driver.profile_image,
            phone_number=driver.phone_number,
            email=driver.email or None,
            car=CarDto(**driver.car.__dict__),
            location=LocationDto(**driver.location.__dict__),
        )
