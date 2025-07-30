from dataclasses import dataclass

from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.admin.requests.queries import \
    GetAdminByUserIdQuery
from ed_core.application.features.common.dtos import AdminDto
from ed_core.application.services.admin_service import AdminService


@request_handler(GetAdminByUserIdQuery, BaseResponse[AdminDto])
@dataclass
class GetAdminByUserIdQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._admin_service = AdminService(uow)

        self._error_message = "Admin couldn't be fetched."
        self._success_message = "Admin fetched successfully."

    async def handle(self, request: GetAdminByUserIdQuery) -> BaseResponse[AdminDto]:
        async with self._uow.transaction():
            admin = await self._uow.admin_repository.get(user_id=request.user_id)

            if admin is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    self._error_message,
                    [f"Admin with user id {request.user_id} not found."],
                )

            admin_dto = await self._admin_service.to_dto(admin)

        return BaseResponse[AdminDto].success(self._success_message, admin_dto)
