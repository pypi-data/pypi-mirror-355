from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos.driver_dto import DriverDto
from ed_core.application.features.common.dtos.validators.update_location_dto_validator import \
    UpdateLocationDtoValidator
from ed_core.application.features.driver.requests.commands import \
    UpdateDriverCurrentLocationCommand
from ed_core.application.services import DriverService, LocationService

LOG = get_logger()


@request_handler(UpdateDriverCurrentLocationCommand, BaseResponse[DriverDto])
class UpdateDriverCurrentLocationCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._driver_service = DriverService(uow)
        self._location_service = LocationService(uow)

        self._error_message = "Driver current location was not updated successfully."
        self._success_message = "Driver current location updated successfully."

    async def handle(
        self, request: UpdateDriverCurrentLocationCommand
    ) -> BaseResponse[DriverDto]:
        dto_validator = UpdateLocationDtoValidator().validate(request.dto)

        if not dto_validator.is_valid:
            raise ApplicationException(
                Exceptions.BadRequestException,
                self._error_message,
                dto_validator.errors,
            )

        async with self._uow.transaction():
            driver = await self._driver_service.get(request.driver_id)
            assert driver is not None

            await self._location_service.update(driver.location_id, request.dto)

            driver_dto = await self._driver_service.to_dto(driver)

        return BaseResponse[DriverDto].success(self._success_message, driver_dto)
