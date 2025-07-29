from ed_domain.core.entities.otp import OtpType
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from ed_domain.utils.otp.abc_otp_generator import ABCOtpGenerator
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.features.common.helpers import send_notification
from ed_core.application.features.driver.requests.commands import \
    StartOrderPickUpCommand
from ed_core.application.services import (BusinessService, DriverService,
                                          OrderService, OtpService)
from ed_core.application.services.otp_service import CreateOtpDto


@request_handler(StartOrderPickUpCommand, BaseResponse[None])
class StartOrderPickUpCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork, api: ABCApi, otp: ABCOtpGenerator):
        self._uow = uow
        self._api = api
        self._otp = otp

        self._driver_service = DriverService(uow)
        self._business_service = BusinessService(uow)
        self._order_service = OrderService(uow)
        self._otp_service = OtpService(uow)

        self._success_message = "Order picked up initiated successfully."
        self._error_message = "Order pick up was not  successfully."

    async def handle(self, request: StartOrderPickUpCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            order = await self._order_service.get(request.order_id)
            assert order is not None

            driver = await self._driver_service.get(request.driver_id)
            assert driver is not None

            business = await self._business_service.get(order.business_id)
            assert business is not None

            otp = await self._otp_service.create(
                CreateOtpDto(
                    user_id=driver.user_id,
                    value=self._otp.generate(),
                    otp_type=OtpType.PICK_UP,
                )
            )

        await send_notification(
            business.user_id,
            f"Your OTP for the pick up of order: {order.id} is {otp}.",
            self._api.notification_api,
            self._error_message,
        )

        return BaseResponse[None].success(self._success_message, None)
