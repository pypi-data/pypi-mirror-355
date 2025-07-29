from collections import defaultdict
from datetime import datetime
from typing import Callable, Optional

from ed_domain.core.aggregate_roots import Order
from ed_domain.core.aggregate_roots.order import OrderStatus
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.dtos import BusinessReportDto
from ed_core.application.features.business.dtos.business_report_dto import \
    DeliveryPerformanceData
from ed_core.application.features.business.requests.queries import \
    GetBusinessReportQuery
from ed_core.application.services.order_service import OrderService


@request_handler(GetBusinessReportQuery, BaseResponse[BusinessReportDto])
class GetBusinessReportQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        self._order_service = OrderService(uow)

    async def handle(
        self, request: GetBusinessReportQuery
    ) -> BaseResponse[BusinessReportDto]:
        async with self._uow.transaction():
            # For demonstration, let's assume we can pass start/end dates for filtering if needed
            # For now, we'll get all and filter in _generate_report if dates are present in request
            orders = await self._uow.order_repository.get_all(
                business_id=request.business_id
            )
            report = await self._generate_report(
                orders, request.report_start_date, request.report_end_date
            )

        return BaseResponse[BusinessReportDto].success(
            "Business report generated successfully.", report
        )

    async def _generate_report(
        self,
        orders: list[Order],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> BusinessReportDto:
        filtered_orders = self._filter_orders_by_date(
            orders, start_date, end_date)

        total_orders = len(filtered_orders)
        completed_deliveries = self._count(
            filtered_orders, lambda x: x.order_status == OrderStatus.COMPLETED
        )
        cancelled_deliveries = self._count(
            filtered_orders, lambda x: x.order_status == OrderStatus.CANCELLED
        )
        failed_deliveries = self._count(
            filtered_orders, lambda x: x.order_status == OrderStatus.FAILED
        )
        pending_deliveries = self._count(
            filtered_orders, lambda x: x.order_status == OrderStatus.PENDING
        )

        total_revenue_birr = sum(
            [order.bill.amount_in_birr for order in filtered_orders]
        )
        average_order_value_birr = self._average(
            [order.bill.amount_in_birr for order in filtered_orders]
        )

        # Delivery time metrics
        delivery_times = []
        on_time_deliveries = 0
        late_deliveries = 0
        for order in filtered_orders:
            if order.actual_delivery_time and order.picked_up_datetime:
                duration = order.actual_delivery_time - order.picked_up_datetime
                delivery_times.append(
                    duration.total_seconds() / 60)  # in minutes

                # Assuming 'expected_delivery_time' is a good benchmark for on-time
                if (
                    order.expected_delivery_time
                    and order.actual_delivery_time <= order.expected_delivery_time
                ):
                    on_time_deliveries += 1
                elif (
                    order.expected_delivery_time
                    and order.actual_delivery_time > order.expected_delivery_time
                ):
                    late_deliveries += 1

        average_delivery_time_minutes = self._average(delivery_times)
        on_time_delivery_rate = (
            (on_time_deliveries / completed_deliveries) * 100
            if completed_deliveries > 0
            else 0
        )

        # Customer satisfaction
        customer_ratings = [
            float(order.customer_rating)
            for order in filtered_orders
            if order.customer_rating is not None
        ]
        customer_satisfaction_average_rating = self._average(customer_ratings)

        # Customer segmentation (new vs. repeat)
        consumer_ids = [order.consumer_id for order in filtered_orders]
        unique_consumers = set(consumer_ids)
        # This is a simplified approach. A true new/repeat customer metric
        # would likely involve querying historical order data beyond the report period.
        # For this report, we'll count unique consumers in this period as "new" for this specific report's context,
        # and those with multiple orders as "repeat".
        new_customers = len(unique_consumers)
        repeat_customers = 0
        consumer_order_counts = defaultdict(int)
        for consumer_id in consumer_ids:
            consumer_order_counts[consumer_id] += 1
        repeat_customers = sum(
            1 for count in consumer_order_counts.values() if count > 1
        )

        # Average driver rating
        driver_ratings = []
        for order in filtered_orders:
            # This would ideally come from a driver's historical rating, but for this context,
            # if an order has a driver and a customer rating, we can infer a driver rating.
            # In a real system, you'd likely have a dedicated Driver entity with its own rating.
            if order.driver_id and order.customer_rating is not None:
                driver_ratings.append(
                    order.customer_rating
                )  # Simplistic: using customer rating as proxy for driver rating on that order
        average_driver_rating = self._average(driver_ratings)

        # Peak delivery hours and days
        peak_delivery_hours = defaultdict(int)
        peak_delivery_days = defaultdict(int)
        for order in filtered_orders:
            if order.completed_datetime:
                hour = order.completed_datetime.strftime("%H")
                day_of_week = order.completed_datetime.strftime("%A")
                peak_delivery_hours[hour] += 1
                peak_delivery_days[day_of_week] += 1

        # New creative metrics
        customer_retention_rate = (
            (repeat_customers / new_customers) * 100 if new_customers > 0 else 0
        )
        delivery_success_rate = (
            (completed_deliveries / total_orders) *
            100 if total_orders > 0 else 0
        )

        # Determine report start and end dates based on filtered orders
        report_start_date = (
            min([order.latest_time_of_delivery for order in filtered_orders])
            if filtered_orders
            else (start_date if start_date else datetime.min)
        )
        report_end_date = (
            max([order.latest_time_of_delivery for order in filtered_orders])
            if filtered_orders
            else (end_date if end_date else datetime.max)
        )

        if start_date:
            report_start_date = start_date
        if end_date:
            report_end_date = end_date

        return BusinessReportDto(
            orders=[
                await self._order_service.to_dto(order) for order in filtered_orders
            ],
            total_orders=total_orders,
            completed_deliveries=completed_deliveries,
            cancelled_deliveries=cancelled_deliveries,
            failed_deliveries=failed_deliveries,
            pending_deliveries=pending_deliveries,
            average_order_value_birr=average_order_value_birr,
            total_revenue_birr=total_revenue_birr,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            average_delivery_time_minutes=average_delivery_time_minutes,
            on_time_delivery_rate=on_time_delivery_rate,
            late_deliveries=late_deliveries,
            customer_satisfaction_average_rating=customer_satisfaction_average_rating,
            new_customers=new_customers,
            repeat_customers=repeat_customers,
            average_driver_rating=average_driver_rating,
            peak_delivery_hours=dict(peak_delivery_hours),
            peak_delivery_days=dict(peak_delivery_days),
            customer_retention_rate=customer_retention_rate,
            delivery_success_rate=delivery_success_rate,
            delivery_performance_data=self.generate_delivery_performance_data(
                orders),
        )

    def _count(self, orders: list[Order], fn: Callable[[Order], bool]) -> int:
        return sum(1 for order in orders if fn(order))

    def _average(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    def _filter_orders_by_date(
        self,
        orders: list[Order],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> list[Order]:
        """Filters orders based on a date range using their `latest_time_of_delivery`."""
        if not start_date and not end_date:
            return orders

        filtered = []
        for order in orders:
            # Using latest_time_of_delivery as a general timestamp for filtering
            order_date = order.latest_time_of_delivery
            if start_date and order_date < start_date:
                continue
            if end_date and order_date > end_date:
                continue
            filtered.append(order)
        return filtered

    def generate_delivery_performance_data(
        self,
        orders: list[Order],
    ) -> DeliveryPerformanceData:
        performance_data: list[tuple[datetime,
                                     Optional[float], Optional[float]]] = []

        for order in orders:
            if order.picked_up_datetime:
                timestamp = order.picked_up_datetime

                expected_duration_minutes: Optional[float] = None
                if order.expected_delivery_time:
                    expected_duration = (
                        order.expected_delivery_time - order.picked_up_datetime
                    )
                    expected_duration_minutes = round(
                        expected_duration.total_seconds() / 60, 2
                    )

                actual_duration_minutes: Optional[float] = None
                if order.actual_delivery_time:
                    actual_duration = (
                        order.actual_delivery_time - order.picked_up_datetime
                    )
                    actual_duration_minutes = round(
                        actual_duration.total_seconds() / 60, 2
                    )

                performance_data.append(
                    (timestamp, expected_duration_minutes, actual_duration_minutes)
                )
            elif order.completed_datetime:
                # Fallback if picked_up_datetime is missing, use completed_datetime as a reference
                timestamp = order.completed_datetime
                expected_duration_minutes: Optional[float] = (
                    None  # Cannot calculate without pickup time
                )
                actual_duration_minutes: Optional[float] = (
                    None  # Cannot calculate without pickup time
                )
                performance_data.append(
                    (timestamp, expected_duration_minutes, actual_duration_minutes)
                )

        # Sort data by timestamp for chronological plotting
        performance_data.sort(key=lambda x: x[0])
        return performance_data
