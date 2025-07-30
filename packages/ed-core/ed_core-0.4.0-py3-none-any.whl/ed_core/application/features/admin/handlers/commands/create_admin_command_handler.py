from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.admin.dtos.validators import \
    CreateAdminDtoValidator
from ed_core.application.features.admin.requests.commands import \
    CreateAdminCommand
from ed_core.application.features.common.dtos.admin_dto import AdminDto
from ed_core.application.services import AdminService

LOG = get_logger()


@request_handler(CreateAdminCommand, BaseResponse[AdminDto])
class CreateAdminCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._admin_service = AdminService(uow)

        self._error_message = "Create admin failed."
        self._success_message = "Admin created successfully."

    async def handle(self, request: CreateAdminCommand) -> BaseResponse[AdminDto]:
        dto_validator = CreateAdminDtoValidator().validate(request.dto)

        if not dto_validator.is_valid:
            raise ApplicationException(
                Exceptions.ValidationException,
                self._error_message,
                dto_validator.errors,
            )

        async with self._uow.transaction():
            admin = await self._admin_service.create(request.dto)
            admin_dto = await self._admin_service.to_dto(admin)

        return BaseResponse[AdminDto].success(self._success_message, admin_dto)
