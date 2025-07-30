from datetime import datetime
from typing import Optional, TypedDict
from uuid import UUID

from ed_domain.core.aggregate_roots.order import OrderStatus

from ed_core.application.features.common.dtos import BusinessDto, ConsumerDto
from ed_core.application.features.common.dtos.bill_dto import BillDto
from ed_core.application.features.common.dtos.parcel_dto import ParcelDto


class OrderDto(TypedDict):
    id: UUID
    business: BusinessDto
    consumer: ConsumerDto
    latest_time_of_delivery: datetime
    parcel: ParcelDto
    order_status: OrderStatus
    bill: BillDto
    customer_rating: Optional[int]
