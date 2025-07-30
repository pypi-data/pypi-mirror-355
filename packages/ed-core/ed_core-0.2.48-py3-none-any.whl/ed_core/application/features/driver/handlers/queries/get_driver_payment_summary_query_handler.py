from ed_domain.core.aggregate_roots import Order
from ed_domain.core.entities.bill import BillStatus
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.driver.dtos import DriverPaymentSummaryDto
from ed_core.application.features.driver.requests.queries import \
    GetDriverPaymentSummaryQuery
from ed_core.application.services import OrderService


@request_handler(GetDriverPaymentSummaryQuery, BaseResponse[DriverPaymentSummaryDto])
class GetDriverPaymentSummaryQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._order_service = OrderService(uow)

    async def handle(
        self, request: GetDriverPaymentSummaryQuery
    ) -> BaseResponse[DriverPaymentSummaryDto]:
        async with self._uow.transaction():
            orders = await self._uow.order_repository.get_all(
                driver_id=request.driver_id
            )
            total, debt = await self._get_total_and_outstanding_payment_sum(orders)

            order_dtos = [await self._order_service.to_dto(order) for order in orders]

        return BaseResponse[DriverPaymentSummaryDto].success(
            "Driver payment summary fetched successfully.",
            DriverPaymentSummaryDto(
                total_revenue=total,
                debt=debt,
                net_revenue=total - debt,
                orders=order_dtos,
            ),
        )

    async def _get_total_and_outstanding_payment_sum(
        self, orders: list[Order]
    ) -> tuple[float, float]:
        total_sum: float = 0
        outstanding_sum: float = 0

        for order in orders:
            bill = order.bill

            total_sum += bill.amount_in_birr
            if bill.bill_status == BillStatus.WITH_DRIVER:
                outstanding_sum += bill.amount_in_birr

        return total_sum, outstanding_sum
