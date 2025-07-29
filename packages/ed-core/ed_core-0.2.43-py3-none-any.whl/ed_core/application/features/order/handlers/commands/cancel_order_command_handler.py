from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import OrderDto
from ed_core.application.features.order.requests.commands import \
    CancelOrderCommand
from ed_core.application.services.order_service import OrderService


@request_handler(CancelOrderCommand, BaseResponse[OrderDto])
class CancelOrderCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._order_service = OrderService(uow)

    async def handle(self, request: CancelOrderCommand) -> BaseResponse[OrderDto]:
        async with self._uow.transaction():
            order = await self._uow.order_repository.get(id=request.order_id)

            if order is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    "Cancel order failed.",
                    [f"Order with id {request.order_id} not found."],
                )

            order.cancel_order()
            updated = self._uow.order_repository.update(order.id, order)

            order_dto = await self._order_service.to_dto(order)

        if not updated:
            raise ApplicationException(
                Exceptions.InternalServerException,
                "Cancel order failed.",
                [f"Internal error while cancelling order with id {request.order_id}."],
            )

        # TODO: Let optimization know about order cancelling
        return BaseResponse[OrderDto].success(
            "Order cancelled successfully.", order_dto
        )
