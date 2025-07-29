from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.requests.queries import \
    GetBusinessQuery
from ed_core.application.features.common.dtos import BusinessDto
from ed_core.application.services.business_service import BusinessService


@request_handler(GetBusinessQuery, BaseResponse[list[BusinessDto]])
class GetAllBusinessesQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._business_service = BusinessService(uow)

    async def handle(
        self, request: GetBusinessQuery
    ) -> BaseResponse[list[BusinessDto]]:
        async with self._uow.transaction():
            businesses = await self._business_service.get_all()
            business_dtos = [
                await self._business_service.to_dto(business) for business in businesses
            ]

        return BaseResponse[list[BusinessDto]].success(
            "Business fetched successfully.", business_dtos
        )
