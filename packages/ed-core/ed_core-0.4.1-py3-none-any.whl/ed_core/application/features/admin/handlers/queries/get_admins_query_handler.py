from dataclasses import dataclass

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.admin.requests.queries import GetAdminsQuery
from ed_core.application.features.common.dtos import AdminDto
from ed_core.application.services import AdminService


@request_handler(GetAdminsQuery, BaseResponse[list[AdminDto]])
@dataclass
class GetAdminsQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._admin_service = AdminService(uow)

        self._success_message = "Admins fetched successfully."

    async def handle(self, request: GetAdminsQuery) -> BaseResponse[list[AdminDto]]:
        async with self._uow.transaction():
            admins = await self._uow.admin_repository.get_all()
            admin_dtos = [await self._admin_service.to_dto(admin) for admin in admins]

        return BaseResponse[list[AdminDto]].success(self._success_message, admin_dtos)
