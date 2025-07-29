from dataclasses import dataclass

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DriverDto
from ed_core.application.features.driver.requests.queries.get_driver_query import \
    GetDriverQuery
from ed_core.application.services import DriverService


@request_handler(GetDriverQuery, BaseResponse[DriverDto])
@dataclass
class GetDriverQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        self._driver_service = DriverService(uow)

    async def handle(self, request: GetDriverQuery) -> BaseResponse[DriverDto]:
        async with self._uow.transaction():
            driver = await self._uow.driver_repository.get(id=request.driver_id)

            if driver is None:
                return BaseResponse[DriverDto].error(
                    "Driver couldn't be fetched.",
                    [f"Driver with id {request.driver_id} does not exist."],
                )

            driver_dto = await self._driver_service.to_dto(driver)

        return BaseResponse[DriverDto].success(
            "Driver fetched successfully.", driver_dto
        )
