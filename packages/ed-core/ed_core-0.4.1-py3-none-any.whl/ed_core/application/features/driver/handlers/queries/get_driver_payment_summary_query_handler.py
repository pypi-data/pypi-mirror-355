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
from ed_core.application.services import DriverPaymentService, OrderService


@request_handler(GetDriverPaymentSummaryQuery, BaseResponse[DriverPaymentSummaryDto])
class GetDriverPaymentSummaryQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._order_service = OrderService(uow)
        self._driver_payment_service = DriverPaymentService(uow)

        self._success_message = "Driver payment summary fetched successfully."

    async def handle(
        self, request: GetDriverPaymentSummaryQuery
    ) -> BaseResponse[DriverPaymentSummaryDto]:
        async with self._uow.transaction():
            payment_summary_dto = await self._driver_payment_service.get_total_and_outstanding_payment_sum(
                request.driver_id
            )

        return BaseResponse[DriverPaymentSummaryDto].success(
            self._success_message, payment_summary_dto
        )
