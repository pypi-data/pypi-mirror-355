from dataclasses import dataclass

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DriverDto
from ed_core.application.features.driver.requests.queries.get_all_drivers_query import \
    GetAllDriversQuery
from ed_core.application.services import DriverService


@request_handler(GetAllDriversQuery, BaseResponse[list[DriverDto]])
@dataclass
class GetAllDriversQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._driver_service = DriverService(uow)

    async def handle(
        self, request: GetAllDriversQuery
    ) -> BaseResponse[list[DriverDto]]:
        async with self._uow.transaction():
            drivers = await self._uow.driver_repository.get_all()
            driver_dtos = [
                await self._driver_service.to_dto(driver) for driver in drivers
            ]

        return BaseResponse[list[DriverDto]].success(
            "Drivers fetched successfully.", driver_dtos
        )
