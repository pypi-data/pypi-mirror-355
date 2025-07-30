from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.dtos.validators import \
    CreateBusinessDtoValidator
from ed_core.application.features.business.requests.commands import \
    CreateBusinessCommand
from ed_core.application.features.common.dtos.business_dto import BusinessDto
from ed_core.application.services.business_service import BusinessService

LOG = get_logger()


@request_handler(CreateBusinessCommand, BaseResponse[BusinessDto])
class CreateBusinessCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        self._business_service = BusinessService(uow)

    async def handle(self, request: CreateBusinessCommand) -> BaseResponse[BusinessDto]:
        dto_validator = CreateBusinessDtoValidator().validate(request.dto)

        if not dto_validator.is_valid:
            return BaseResponse[BusinessDto].error(
                "Create business failed.", dto_validator.errors
            )

        async with self._uow.transaction():
            business = await self._business_service.create(request.dto)
            business_dto = await self._business_service.to_dto(business)

        print(business)
        return BaseResponse[BusinessDto].success(
            "Business created successfully.", business_dto
        )
