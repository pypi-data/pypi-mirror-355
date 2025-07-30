from typing import Optional

from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.core.aggregate_roots import DeliveryJob, Driver, Order
from ed_domain.core.entities.waypoint import Waypoint
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import TrackOrderDto
from ed_core.application.features.order.requests.queries import TrackOrderQuery
from ed_core.application.services.delivery_job_service import \
    DeliveryJobService
from ed_core.application.services.driver_service import DriverService
from ed_core.application.services.order_service import OrderService
from ed_core.application.services.waypoint_service import WaypointService


@request_handler(TrackOrderQuery, BaseResponse[TrackOrderDto])
class TrackOrderQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._order_service = OrderService(uow)
        self._driver_service = DriverService(uow)
        self._delivery_job_service = DeliveryJobService(uow)
        self._waypoint_service = WaypointService(uow)

        self._error_message = "Cannot track order."
        self._success_message = "Order tracked successfully."

    async def handle(self, request: TrackOrderQuery) -> BaseResponse[TrackOrderDto]:
        async with self._uow.transaction():
            order = await self._uow.order_repository.get(id=request.order_id)
            if order is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    "Order  found.",
                    [f"Order with id {request.order_id} not found."],
                )

            driver = None
            if order.driver_id is not None:
                driver = await self._driver_service.get(order.driver_id)
                assert driver is not None

            dto = await self._create_dto(order, driver)
            return BaseResponse[TrackOrderDto].success(self._success_message, dto)

    async def _create_dto(
        self,
        order: Order,
        driver: Optional[Driver] = None,
    ) -> TrackOrderDto:
        return TrackOrderDto(
            order=await self._order_service.to_dto(order),
            driver=await self._driver_service.to_dto(driver) if driver else None,
        )
