from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Location
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.common.dtos.create_location_dto import \
    CreateLocationDto
from ed_core.application.features.common.dtos.location_dto import LocationDto
from ed_core.application.features.common.dtos.update_location_dto import \
    UpdateLocationDto
from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

CITY = "Addis Ababa"
COUNTRY = "Ethiopia"
LOG = get_logger()


class LocationService(
    ABCService[Location, CreateLocationDto, UpdateLocationDto, LocationDto]
):
    def __init__(self, uow: ABCAsyncUnitOfWork) -> None:
        super().__init__("Location", uow.location_repository)

        self._uow = uow

        LOG.info("LocationService initialized with UnitOfWork.")

    async def create(self, dto: CreateLocationDto) -> Location:
        location = Location(
            id=get_new_id(),
            address=dto["address"],
            latitude=dto["latitude"],
            longitude=dto["longitude"],
            postal_code=dto["postal_code"],
            city=CITY,
            country=COUNTRY,
            last_used=datetime.now(UTC),
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        location = await self._uow.location_repository.create(location)
        LOG.info(f"Location created with ID: {location.id}")
        return location

    async def update(self, id: UUID, dto: UpdateLocationDto) -> Optional[Location]:
        location = await self._uow.location_repository.get(id=id)
        if not location:
            LOG.error(f"Cannot update: No location found for ID: {id}")
            return None

        # Apply updates from the DTO
        if "address" in dto:
            location.address = dto["address"]
        if "latitude" in dto:
            location.latitude = dto["latitude"]
        if "longitude" in dto:
            location.longitude = dto["longitude"]
        if "postal_code" in dto:
            location.postal_code = dto["postal_code"]

        location.update_datetime = datetime.now(UTC)
        await self._uow.location_repository.save(location)
        LOG.info(f"Location with ID: {id} updated.")
        return location

    async def to_dto(self, entity: Location) -> LocationDto:
        return LocationDto(**entity.__dict__)
