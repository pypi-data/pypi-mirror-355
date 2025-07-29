from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel

from ed_core.application.features.common.dtos.order_dto import OrderDto

DeliveryPerformanceData = Annotated[
    list[tuple[datetime, Optional[float], Optional[float]]
         ], "DeliveryPerformanceData"
]


class BusinessReportDto(BaseModel):
    total_orders: int
    completed_deliveries: int
    cancelled_deliveries: int
    pending_deliveries: int
    failed_deliveries: int
    delivery_success_rate: float

    total_revenue_birr: float
    average_order_value_birr: float

    report_start_date: datetime
    report_end_date: datetime

    average_delivery_time_minutes: float

    # average_delivery_distance_km: float
    on_time_delivery_rate: float
    late_deliveries: int

    customer_satisfaction_average_rating: float
    customer_retention_rate: float
    new_customers: int
    repeat_customers: int

    average_driver_rating: Optional[float]  # Overall average driver rating
    peak_delivery_hours: Optional[dict[str, int]]
    peak_delivery_days: Optional[dict[str, int]]
    delivery_performance_data: DeliveryPerformanceData

    orders: list[OrderDto]
