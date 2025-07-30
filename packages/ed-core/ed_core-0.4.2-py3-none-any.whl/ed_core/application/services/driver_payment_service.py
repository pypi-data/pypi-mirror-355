from uuid import UUID

from ed_domain.core.entities.bill import BillStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.driver.dtos import DriverPaymentSummaryDto
from ed_core.application.services.order_service import OrderService


class DriverPaymentService:
    def __init__(self, uow: ABCAsyncUnitOfWork) -> None:
        self._uow = uow
        self._order_service = OrderService(uow)

    async def get_total_and_outstanding_payment_sum(
        self, driver_id: UUID
    ) -> DriverPaymentSummaryDto:
        orders = await self._uow.order_repository.get_all(driver_id=driver_id)
        total_revenue: float = 0
        net_revenue: float = 0
        outstanding_debt: float = 0

        driver = await self._uow.driver_repository.get(id=driver_id)
        if not driver:
            raise ValueError(f"Driver with ID {driver_id} not found.")

        for order in orders:
            bill = order.bill

            if bill.bill_status in [BillStatus.WITH_DRIVER, BillStatus.DONE]:
                total_revenue += bill.amount_in_birr
                cut_amount = bill.amount_in_birr * 0.25
                net_revenue += bill.amount_in_birr - cut_amount

                if bill.bill_status == BillStatus.WITH_DRIVER:
                    outstanding_debt += cut_amount

        await self._uow.driver_repository.save(driver)

        return {
            "orders": [await self._order_service.to_dto(order) for order in orders],
            "debt": outstanding_debt,
            "total_revenue": total_revenue,
            "net_revenue": net_revenue,
        }
