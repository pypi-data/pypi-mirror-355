from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.core.entities.waypoint import WaypointStatus, WaypointType
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.features.driver.requests.commands import \
    FinishOrderDeliveryCommand
from ed_core.application.services import (OrderService, OtpService,
                                          WaypointService)


@request_handler(FinishOrderDeliveryCommand, BaseResponse[None])
class FinishOrderDeliveryCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork, api: ABCApi):
        self._uow = uow
        self._api = api

        self._otp_service = OtpService(uow)
        self._order_service = OrderService(uow)
        self._waypoint_service = WaypointService(uow)

        self._success_message = "Order delivered successfully."
        self._error_message = "Order was not delivered successfully."

    async def handle(self, request: FinishOrderDeliveryCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            order = await self._order_service.get(request.order_id)
            assert order is not None

            if request.driver_id != order.driver_id:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    ["Bad request. Order driver is different."],
                )

            waypoint = await self._waypoint_service.get_order_waypoint(
                order.id, WaypointType.DROP_OFF
            )
            assert waypoint is not None

            # Update db
            order.complete_order()
            waypoint.update_status(WaypointStatus.DONE)

            # Update db
            await self._order_service.save(order)
            await self._waypoint_service.save(waypoint)

        return BaseResponse[None].success(self._success_message, None)
