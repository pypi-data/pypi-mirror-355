from dataclasses import dataclass

from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DriverDto
from ed_core.application.features.driver.requests.queries import \
    GetDriverByUserIdQuery
from ed_core.application.services.driver_service import DriverService


@request_handler(GetDriverByUserIdQuery, BaseResponse[DriverDto])
@dataclass
class GetDriverByUserIdQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        self._driver_service = DriverService(uow)

    async def handle(self, request: GetDriverByUserIdQuery) -> BaseResponse[DriverDto]:
        async with self._uow.transaction():
            driver = await self._uow.driver_repository.get(user_id=request.user_id)

            if driver is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    "Driver not found.",
                    [f"Driver with user id {request.user_id} not found."],
                )
            driver_dto = await self._driver_service.to_dto(driver)

        return BaseResponse[DriverDto].success(
            "Driver fetched successfully.", driver_dto
        )
