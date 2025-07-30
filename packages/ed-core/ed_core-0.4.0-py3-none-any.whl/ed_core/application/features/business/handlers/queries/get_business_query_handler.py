from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.requests.queries import \
    GetBusinessQuery
from ed_core.application.features.common.dtos import BusinessDto
from ed_core.application.services import BusinessService


@request_handler(GetBusinessQuery, BaseResponse[BusinessDto])
class GetBusinessQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        self._business_service = BusinessService(uow)

    async def handle(self, request: GetBusinessQuery) -> BaseResponse[BusinessDto]:
        async with self._uow.transaction():
            business = await self._uow.business_repository.get(id=request.business_id)

            if business is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    "Business not found.",
                    [f"Business with id {request.business_id} not found."],
                )

            business_dto = await self._business_service.to_dto(business)

        return BaseResponse[BusinessDto].success(
            "Business fetched successfully.", business_dto
        )
