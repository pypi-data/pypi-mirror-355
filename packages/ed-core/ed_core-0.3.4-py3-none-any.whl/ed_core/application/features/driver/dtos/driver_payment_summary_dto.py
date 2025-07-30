from typing import TypedDict

from ed_core.application.features.common.dtos.order_dto import OrderDto


class DriverPaymentSummaryDto(TypedDict):
    total_revenue: float
    debt: float
    net_revenue: float
    orders: list[OrderDto]
