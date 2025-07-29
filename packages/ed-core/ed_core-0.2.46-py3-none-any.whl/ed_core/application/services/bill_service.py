from datetime import UTC, datetime
from typing import TypedDict

from ed_domain.common.logging import get_logger
from ed_domain.core.entities import Bill
from ed_domain.core.entities.bill import BillStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from pydantic import BaseModel

from ed_core.application.features.common.dtos.bill_dto import BillDto
from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class CreateBillDto(TypedDict):
    amount_in_birr: float


BILL_AMOUNT = 10


class BillService(ABCService[Bill, CreateBillDto, None, BillDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Bill", uow.bill_repository)

        self._uow = uow

        LOG.info("BillService initialized with UnitOfWork.")

    async def create(self, dto: CreateBillDto) -> Bill:
        bill = Bill(
            id=get_new_id(),
            amount_in_birr=dto["amount_in_birr"],
            bill_status=BillStatus.PENDING,
            due_date=datetime.now(UTC),
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        bill = await self._uow.bill_repository.create(bill)
        LOG.info(f"Bill created with ID: {bill.id}")
        return bill

    async def to_dto(self, entity: Bill) -> BillDto:
        return BillDto(**entity.__dict__)
