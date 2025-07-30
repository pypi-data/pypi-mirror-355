from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.core.entities.bill import BillStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.admin.requests.commands import \
    SettleDriverPaymentCommand
from ed_core.application.features.driver.dtos import DriverPaymentSummaryDto
from ed_core.application.services import (AdminService, BillService,
                                          DriverPaymentService, OrderService)

LOG = get_logger()


@request_handler(SettleDriverPaymentCommand, BaseResponse[DriverPaymentSummaryDto])
class SettleDriverPaymentCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._admin_service = AdminService(uow)
        self._bill_service = BillService(uow)
        self._order_service = OrderService(uow)
        self._driver_payment_service = DriverPaymentService(uow)

        self._error_message = "Settling driver payment failed."
        self._success_message = "Driver payment settled successfully."

    async def handle(
        self, request: SettleDriverPaymentCommand
    ) -> BaseResponse[DriverPaymentSummaryDto]:
        async with self._uow.transaction():
            admin = await self._admin_service.get(id=request.admin_id)
            assert admin is not None

            if not admin.can_receive_money_from_drivers:
                raise ApplicationException(
                    Exceptions.UnauthorizedException,
                    self._error_message,
                    [
                        f"Admin with id {request.admin_id} does not have authorization to accept payment from drivers."
                    ],
                )

            orders = await self._order_service.get_all(driver_id=request.driver_id)

            for order in orders:
                order.bill.update_status(BillStatus.DONE)
                await self._bill_service.save(order.bill)

            payment_summary_dto = await self._driver_payment_service.get_total_and_outstanding_payment_sum(
                request.driver_id
            )

        return BaseResponse[DriverPaymentSummaryDto].success(
            self._success_message, payment_summary_dto
        )
