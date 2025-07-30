from ed_domain.common.exceptions import EXCEPTION_NAMES, ApplicationException
from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Business, Driver, Location, Order
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
    StartOrderPickUpCommand
from ed_core.application.services import (BusinessService, DriverService,
                                          LocationService, OrderService,
                                          OtpService)
from ed_core.application.services.otp_service import CreateOtpDto

LOG = get_logger()


@request_handler(StartOrderPickUpCommand, BaseResponse[None])
class StartOrderPickUpCommandHandler(RequestHandler):
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
        self._business_service = BusinessService(uow)
        self._order_service = OrderService(uow)
        self._otp_service = OtpService(uow)
        self._location_service = LocationService(uow)

        self._success_message = "Order picked up initiated successfully."
        self._error_message = "Order pick up was not  successfully."

    async def handle(self, request: StartOrderPickUpCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            order = await self._order_service.get(id=request.order_id)
            assert order is not None

            driver = await self._driver_service.get(id=request.driver_id)
            assert driver is not None

            business = await self._business_service.get(id=order.business_id)
            assert business is not None

            business_location = await self._location_service.get(
                id=business.location_id
            )
            assert business_location is not None

            otp = await self._otp_service.create(
                CreateOtpDto(
                    user_id=driver.user_id,
                    value=self._otp.generate(),
                    otp_type=OtpType.PICK_UP,
                )
            )

            await self._send_email_to_business(
                str(order.bill.amount_in_birr),
                otp.value,
                business,
                order,
                driver,
                business_location,
            )

        return BaseResponse[None].success(self._success_message, None)

    async def _send_email_to_business(
        self,
        bill_amount: str,
        otp: str,
        business: Business,
        order: Order,
        driver: Driver,
        business_location: Location,
    ) -> None:
        email = self._email_templater.delivery_business_otp(
            otp,
            order.order_number,
            business.business_name,
            bill_amount,
            business_location.address,
            f"{driver.first_name} {driver.last_name}",
            driver.phone_number,
        )

        notification_response = await self._api.notification_api.send_notification(
            {
                "user_id": business.user_id,
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
