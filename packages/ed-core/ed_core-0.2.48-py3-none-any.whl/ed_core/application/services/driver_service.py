from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Driver
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.common.dtos.driver_dto import DriverDto
from ed_core.application.features.driver.dtos.create_driver_dto import \
    CreateDriverDto
from ed_core.application.features.driver.dtos.update_driver_dto import \
    UpdateDriverDto
from ed_core.application.services.abc_service import ABCService
from ed_core.application.services.car_service import CarService
from ed_core.application.services.location_service import LocationService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class DriverService(ABCService[Driver, CreateDriverDto, UpdateDriverDto, DriverDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Driver", uow.driver_repository)

        self._uow = uow
        self._location_service = LocationService(uow)
        self._car_service = CarService(uow)

        LOG.info("DriverService initialized with UnitOfWork.")

    async def create(self, dto: CreateDriverDto) -> Driver:
        location = await self._location_service.create(dto["location"])
        car = await self._car_service.create(dto["car"])

        driver = Driver(
            id=get_new_id(),
            user_id=dto["user_id"],
            first_name=dto["first_name"],
            last_name=dto["last_name"],
            profile_image=dto["profile_image"],
            phone_number=dto["phone_number"],
            email=dto["email"],
            location_id=location.id,
            car=car,
            available=False,
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        driver = await self._uow.driver_repository.create(driver)
        LOG.info(f"Driver created with ID: {driver.id}")
        return driver

    async def update(self, id: UUID, dto: UpdateDriverDto) -> Optional[Driver]:
        driver = await self._uow.driver_repository.get(id=id)
        if driver is None:
            LOG.error(f"Cannot update: No driver found for ID: {id}")
            return None

        if "profile_image" in dto:
            driver.profile_image = dto["profile_image"]
        if "phone_number" in dto:
            driver.phone_number = dto["phone_number"]
        if "email" in dto:
            driver.email = dto["email"]

        if "location" in dto:
            await self._location_service.update(driver.location_id, dto["location"])

        driver.update_datetime = datetime.now(UTC)
        await self._uow.driver_repository.save(driver)
        LOG.info(f"Driver with ID: {id} updated.")
        return driver

    async def to_dto(self, entity: Driver) -> DriverDto:
        location = await self._location_service.get(entity.location_id)
        assert location is not None

        location_dto = await self._location_service.to_dto(location)
        car_dto = await self._car_service.to_dto(entity.car)

        return DriverDto(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            profile_image=entity.profile_image,
            phone_number=entity.phone_number,
            email=entity.email or None,
            car=car_dto,
            location=location_dto,
        )
