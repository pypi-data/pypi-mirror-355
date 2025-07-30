from datetime import datetime
from uuid import UUID

from ed_domain.core.entities.bill import BillStatus
from typing import TypedDict


class BillDto(TypedDict):
    id: UUID
    amount_in_birr: float
    bill_status: BillStatus
    due_date: datetime
