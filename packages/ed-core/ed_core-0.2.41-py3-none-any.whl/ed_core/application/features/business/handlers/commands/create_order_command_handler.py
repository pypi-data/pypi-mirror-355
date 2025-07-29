from ed_domain.common.exceptions import (EXCEPTION_NAMES, ApplicationException,
                                         Exceptions)
from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Business, Consumer, Location, Order
from ed_domain.core.entities.notification import NotificationType
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.contracts.infrastructure.email.abc_email_templater import \
    ABCEmailTemplater
from ed_core.application.features.business.dtos.validators import \
    CreateOrderDtoValidator
from ed_core.application.features.business.requests.commands import \
    CreateOrderCommand
from ed_core.application.features.common.dtos import OrderDto
from ed_core.application.services.business_service import BusinessService
from ed_core.application.services.consumer_service import ConsumerService
from ed_core.application.services.location_service import LocationService
from ed_core.application.services.order_service import OrderService

LOG = get_logger()

BILL_AMOUNT = 10


@request_handler(CreateOrderCommand, BaseResponse[OrderDto])
class CreateOrderCommandHandler(RequestHandler):
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
        self._consumer_service = ConsumerService(uow)
        self._business_service = BusinessService(uow)
        self._location_service = LocationService(uow)

        self._error_message = "Failed to create order"

    async def handle(self, request: CreateOrderCommand) -> BaseResponse[OrderDto]:
        dto, business_id, consumer_id = (
            request.dto,
            request.business_id,
            request.dto["consumer_id"],
        )
        dto_validator = CreateOrderDtoValidator().validate(request.dto)

        if not dto_validator.is_valid:
            raise ApplicationException(
                Exceptions.ValidationException,
                self._error_message,
                dto_validator.errors,
            )

        async with self._uow.transaction():
            consumer = await self._consumer_service.get(consumer_id)
            assert consumer is not None

            consumer_location = await self._location_service.get(consumer.location_id)
            assert consumer_location is not None

            business = await self._business_service.get(business_id)
            assert business is not None

            order = await self._order_service.create_order(
                dto, business_id, BILL_AMOUNT
            )
            order_dto = await self._order_service.to_dto(order)

        await self._send_notification(order, consumer, consumer_location, business)

        return BaseResponse[OrderDto].success(
            "Order created successfully.",
            order_dto,
        )

    async def _send_notification(
        self,
        order: Order,
        consumer: Consumer,
        consumer_location: Location,
        business: Business,
    ) -> None:
        LOG.info(f"Sending notification to consumer {consumer.user_id}")
        formatted_create_datetime = order.create_datetime.strftime("%B %d, %Y")

        formatted_delivery_time = order.latest_time_of_delivery.strftime(
            "%B %d, %Y")

        email = self._email_templater.order_placed(
            order.order_number,
            consumer.first_name,
            formatted_create_datetime,
            business.business_name,
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
