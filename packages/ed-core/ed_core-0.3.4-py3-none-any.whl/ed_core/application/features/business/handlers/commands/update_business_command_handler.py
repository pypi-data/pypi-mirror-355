from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.dtos.validators import \
    UpdateBusinessDtoValidator
from ed_core.application.features.business.requests.commands import \
    UpdateBusinessCommand
from ed_core.application.features.common.dtos.business_dto import BusinessDto
from ed_core.application.services import BusinessService

LOG = get_logger()


@request_handler(UpdateBusinessCommand, BaseResponse[BusinessDto])
class UpdateBusinessCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        self._business_service = BusinessService(uow)

    async def handle(self, request: UpdateBusinessCommand) -> BaseResponse[BusinessDto]:
        dto_validator = UpdateBusinessDtoValidator().validate(request.dto)

        if not dto_validator.is_valid:
            raise ApplicationException(
                Exceptions.ValidationException,
                "Update business failed.",
                dto_validator.errors,
            )

        async with self._uow.transaction():
            business = await self._business_service.update(request.id, request.dto)
            assert business is not None

            business_dto = await self._business_service.to_dto(business)

        return BaseResponse[BusinessDto].success(
            "Business updated successfully.", business_dto
        )
