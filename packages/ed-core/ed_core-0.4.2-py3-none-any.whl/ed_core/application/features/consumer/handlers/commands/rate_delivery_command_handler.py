from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos.order_dto import OrderDto
from ed_core.application.features.consumer.requests.commands import \
    RateDeliveryCommand
from ed_core.application.services import OrderService

LOG = get_logger()


@request_handler(RateDeliveryCommand, BaseResponse[OrderDto])
class RateDeliveryCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._order_service = OrderService(uow)

        self._error_message = "Delivery rating failed."
        self._success_message = "Delivery rated successfully."

    async def handle(self, request: RateDeliveryCommand) -> BaseResponse[OrderDto]:
        async with self._uow.transaction():
            order = await self._order_service.get_by_id(request.order_id)
            assert order is not None

            order.set_customer_rating(request.dto["rating"])

            await self._order_service.save(order)
            order_dto = await self._order_service.to_dto(order)

        return BaseResponse[OrderDto].success(self._success_message, order_dto)
