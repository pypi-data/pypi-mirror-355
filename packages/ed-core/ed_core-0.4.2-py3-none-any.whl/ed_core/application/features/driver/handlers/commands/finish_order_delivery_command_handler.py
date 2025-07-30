from ed_domain.common.exceptions import (EXCEPTION_NAMES, ApplicationException,
                                         Exceptions)
from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Consumer, Driver, Location, Order
from ed_domain.core.entities.notification import NotificationType
from ed_domain.core.entities.otp import OtpType
from ed_domain.core.entities.waypoint import WaypointStatus, WaypointType
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.contracts.infrastructure.email.abc_email_templater import \
    ABCEmailTemplater
from ed_core.application.features.driver.requests.commands import \
    FinishOrderDeliveryCommand
from ed_core.application.services import (ConsumerService, DriverService,
                                          LocationService, OrderService,
                                          OtpService, WaypointService)

LOG = get_logger()


@request_handler(FinishOrderDeliveryCommand, BaseResponse[None])
class FinishOrderDeliveryCommandHandler(RequestHandler):
    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
        api: ABCApi,
        email_templater: ABCEmailTemplater,
    ):
        self._uow = uow
        self._api = api
        self._email_templater = email_templater

        self._order_service = OrderService(uow)
        self._waypoint_service = WaypointService(uow)
        self._location_service = LocationService(uow)
        self._driver_service = DriverService(uow)
        self._consumer_service = ConsumerService(uow)
        self._otp_service = OtpService(uow)

        self._success_message = "Order delivered successfully."
        self._error_message = "Order was not delivered successfully."

    async def handle(self, request: FinishOrderDeliveryCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            order = await self._order_service.get(id=request.order_id)
            assert order is not None and order.driver_id is not None

            driver = await self._driver_service.get(id=order.driver_id)
            assert driver is not None

            consumer = await self._consumer_service.get(id=order.consumer_id)
            assert consumer is not None

            consumer_location = await self._location_service.get(
                id=consumer.location_id
            )
            assert consumer_location is not None

            if request.driver_id != order.driver_id:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    ["Bad request. Order driver is different."],
                )

            otp = await self._uow.otp_repository.get(user_id=driver.user_id)
            print("LOG: got otp", otp)
            if otp is None or otp.otp_type != OtpType.DROP_OFF:
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

            print("Order:", order)

            # Update db
            try:
                otp.delete()
                order.complete_order()
                waypoint.update_status(WaypointStatus.DONE)
            except Exception as e:
                raise ApplicationException(
                    Exceptions.BadRequestException, self._error_message, [
                        f"{e}"]
                )

            # Update db
            await self._otp_service.save(otp)
            await self._order_service.save(order)
            await self._waypoint_service.save(waypoint)

            # Send notification
            await self._send_rating_in_app_notificaiton_to_consumer(consumer, order)
            await self._send_email_to_consumer(
                consumer, order, driver, consumer_location
            )

        return BaseResponse[None].success(self._success_message, None)

    async def _send_rating_in_app_notificaiton_to_consumer(
        self, consumer: Consumer, order: Order
    ) -> None:
        notification_response = await self._api.notification_api.send_notification(
            {
                "user_id": consumer.user_id,
                "notification_type": NotificationType.IN_APP,
                "message": f"RATE_DELIVERY: {order.id}",
            }
        )

        if not notification_response["is_success"]:
            raise ApplicationException(
                EXCEPTION_NAMES[notification_response["http_status_code"]],
                self._error_message,
                notification_response["errors"],
            )
        LOG.info("Got response from notification api sent successfully.")

    async def _send_email_to_consumer(
        self,
        consumer: Consumer,
        order: Order,
        driver: Driver,
        consumer_location: Location,
    ) -> None:
        assert order.actual_delivery_time is not None
        formatted_delivery_time = order.actual_delivery_time.strftime(
            "%B %d, %Y")

        email = self._email_templater.delivery_completed(
            order.order_number,
            consumer.first_name,
            f"{driver.first_name} {driver.last_name}",
            consumer_location.address,
            formatted_delivery_time,
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
