from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.core.entities.otp import OtpType
from ed_domain.core.entities.waypoint import WaypointType
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.features.driver.requests.commands import \
    FinishOrderPickUpCommand
from ed_core.application.services import (DeliveryJobService, DriverService,
                                          OrderService, OtpService,
                                          WaypointService)


@request_handler(FinishOrderPickUpCommand, BaseResponse[None])
class FinishOrderPickUpCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork, api: ABCApi):
        self._uow = uow
        self._api = api

        self._otp_service = OtpService(uow)
        self._order_service = OrderService(uow)
        self._waypoint_service = WaypointService(uow)
        self._driver_service = DriverService(uow)
        self._delivery_job_service = DeliveryJobService(uow)

        self._success_message = "Order picked up successfully."
        self._error_message = "Order was not picked up successfully."

    async def handle(self, request: FinishOrderPickUpCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            order = await self._order_service.get(id=request.order_id)
            assert order is not None

            driver = await self._driver_service.get(id=request.driver_id)
            assert driver is not None

            if request.driver_id != order.driver_id:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    ["Bad request. Order driver is different."],
                )

            otp = await self._uow.otp_repository.get(user_id=driver.user_id)
            if otp is None or otp.otp_type != OtpType.PICK_UP:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    ["Bad request. Otp was not sent."],
                )

            if otp.value != request.dto["otp"]:
                raise ApplicationException(
                    Exceptions.UnauthorizedException,
                    self._error_message,
                    ["Otp value is not correct."],
                )

            waypoint = await self._waypoint_service.get_order_waypoint(
                order.id, WaypointType.PICK_UP
            )
            assert waypoint is not None

            try:
                otp.delete()
                order.pick_up_order()
                waypoint.complete()
            except Exception as e:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    [f"{e}"],
                )

            await self._otp_service.save(otp)
            await self._order_service.save(order)
            await self._waypoint_service.save(waypoint)
            await self._delivery_job_service.check_if_done(request.delivery_job_id)

        return BaseResponse[None].success(self._success_message, None)
