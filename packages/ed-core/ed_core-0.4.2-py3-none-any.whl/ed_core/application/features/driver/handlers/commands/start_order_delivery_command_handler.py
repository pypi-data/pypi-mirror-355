from ed_domain.common.exceptions import EXCEPTION_NAMES, ApplicationException
from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Consumer, Driver, Location, Order
from ed_domain.core.entities.notification import NotificationType
from ed_domain.core.entities.otp import OtpType
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from ed_domain.utils.otp.abc_otp_generator import ABCOtpGenerator
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.contracts.infrastructure.email.abc_email_templater import \
    ABCEmailTemplater
from ed_core.application.features.driver.requests.commands import \
    StartOrderDeliveryCommand
from ed_core.application.services import (ConsumerService, DriverService,
                                          LocationService, OrderService,
                                          OtpService)
from ed_core.application.services.otp_service import CreateOtpDto

LOG = get_logger()


@request_handler(StartOrderDeliveryCommand, BaseResponse[None])
class StartOrderDeliveryCommandHandler(RequestHandler):
    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
        api: ABCApi,
        otp: ABCOtpGenerator,
        email_templater: ABCEmailTemplater,
    ):
        self._uow = uow
        self._api = api
        self._otp = otp
        self._email_templater = email_templater

        self._driver_service = DriverService(uow)
        self._consumer_service = ConsumerService(uow)
        self._otp_service = OtpService(uow)
        self._order_service = OrderService(uow)
        self._location_service = LocationService(uow)

        self._success_message = "Order delivery initiated successfully."
        self._error_message = "Order delivery was not initiated successfully."

    async def handle(self, request: StartOrderDeliveryCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            order = await self._order_service.get(id=request.order_id)
            assert order is not None

            driver = await self._driver_service.get(id=request.driver_id)
            assert driver is not None

            consumer = await self._consumer_service.get(id=order.consumer_id)
            assert consumer is not None

            consumer_location = await self._location_service.get(
                id=consumer.location_id
            )
            assert consumer_location is not None

            otp = await self._otp_service.create(
                CreateOtpDto(
                    user_id=driver.user_id,
                    value=self._otp.generate(),
                    otp_type=OtpType.DROP_OFF,
                )
            )

        await self._send_email_to_consumer(
            otp.value, consumer, order, driver, consumer_location
        )

        return BaseResponse[None].success(self._success_message, None)

    async def _send_email_to_consumer(
        self,
        otp: str,
        consumer: Consumer,
        order: Order,
        driver: Driver,
        consumer_location: Location,
    ) -> None:
        email = self._email_templater.delivery_consumer_otp(
            otp,
            order.order_number,
            consumer.first_name,
            consumer_location.address,
            f"{driver.first_name} {driver.last_name}",
            driver.phone_number,
        )
        notification_response = await self._api.notification_api.send_notification(
            {
                "user_id": consumer.user_id,
                "notification_type": NotificationType.EMAIL,
                "message": email,
            }
        )

        if not notification_response["is_success"]:
            raise ApplicationException(
                EXCEPTION_NAMES[notification_response["http_status_code"]],
                self._error_message,
                notification_response["errors"],
            )
        LOG.info("Got response from notification api sent successfully.")
