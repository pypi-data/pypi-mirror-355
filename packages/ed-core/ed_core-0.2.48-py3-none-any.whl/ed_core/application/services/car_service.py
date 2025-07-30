from datetime import UTC, datetime

from ed_domain.common.logging import get_logger
from ed_domain.core.entities import Car
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.common.dtos.car_dto import CarDto
from ed_core.application.features.driver.dtos.create_car_dto import \
    CreateCarDto
from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class CarService(ABCService[Car, CreateCarDto, None, CarDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Car", uow.car_repository)

        self._uow = uow

        LOG.info("CarService initialized with UnitOfWork.")

    async def create(self, dto: CreateCarDto) -> Car:
        car = Car(
            id=get_new_id(),
            make=dto["make"],
            model=dto["model"],
            year=dto["year"],
            color=dto["color"],
            seats=dto["seats"],
            license_plate_number=dto["license_plate"],
            registration_number=dto["registration_number"],
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        car = await self._uow.car_repository.create(car)
        LOG.info(f"Car created with ID: {car.id}")
        return car

    async def to_dto(self, entity: Car) -> CarDto:
        return CarDto(**entity.__dict__)
