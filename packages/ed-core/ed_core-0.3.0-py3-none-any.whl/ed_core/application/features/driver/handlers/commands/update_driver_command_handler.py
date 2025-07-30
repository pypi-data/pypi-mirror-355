from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos.driver_dto import DriverDto
from ed_core.application.features.driver.dtos.validators import \
    UpdateDriverDtoValidator
from ed_core.application.features.driver.requests.commands import \
    UpdateDriverCommand
from ed_core.application.services import DriverService

LOG = get_logger()


@request_handler(UpdateDriverCommand, BaseResponse[DriverDto])
class UpdateDriverCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        self._driver_service = DriverService(uow)

        self._error_message = "Update driver failed."
        self._success_message = "Driver updated successfully."

    async def handle(self, request: UpdateDriverCommand) -> BaseResponse[DriverDto]:
        dto_validator = UpdateDriverDtoValidator().validate(request.dto)

        if not dto_validator.is_valid:
            return BaseResponse[DriverDto].error(
                self._error_message, dto_validator.errors
            )

        async with self._uow.transaction():
            updated_driver = await self._driver_service.update(
                request.driver_id, request.dto
            )

            if updated_driver is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    self._error_message,
                    [f"Driver with id: {request.driver_id} was not found."],
                )

            updated_driver_dto = await self._driver_service.to_dto(updated_driver)

        return BaseResponse[DriverDto].success(
            self._success_message,
            updated_driver_dto,
        )
