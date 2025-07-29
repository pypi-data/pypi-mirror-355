from datetime import UTC, datetime
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Order
from ed_domain.core.aggregate_roots.order import OrderStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.business.dtos import CreateOrderDto
from ed_core.application.features.common.dtos import OrderDto
from ed_core.application.services.abc_service import ABCService
from ed_core.application.services.bill_service import (BillService,
                                                       CreateBillDto)
from ed_core.application.services.business_service import BusinessService
from ed_core.application.services.consumer_service import ConsumerService
from ed_core.application.services.parcel_service import ParcelService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class OrderService(ABCService[Order, CreateOrderDto, None, OrderDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Order", uow.order_repository)

        self._uow = uow
        self._bill_service = BillService(self._uow)
        self._business_service = BusinessService(self._uow)
        self._consumer_service = ConsumerService(self._uow)
        self._parcel_service = ParcelService(self._uow)

        LOG.info("OrderService initialized with UnitOfWork.")

    async def create_order(
        self,
        dto: CreateOrderDto,
        business_id: UUID,
        bill_amount: float,
    ) -> Order:
        bill = await self._bill_service.create(
            CreateBillDto(amount_in_birr=bill_amount)
        )
        parcel = await self._parcel_service.create(dto["parcel"])

        order = Order(
            id=get_new_id(),
            order_number=self._generate_order_number(),
            business_id=business_id,
            consumer_id=dto["consumer_id"],
            bill=bill,
            latest_time_of_delivery=dto["latest_time_of_delivery"],
            parcel=parcel,
            order_status=OrderStatus.PENDING,
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        order = await self._uow.order_repository.create(order)
        LOG.info(f"Order created with ID: {order.id}")
        return order

    async def to_dto(self, entity: Order) -> OrderDto:
        business = await self._business_service.get(entity.business_id)
        assert business is not None

        consumer = await self._consumer_service.get(entity.consumer_id)
        assert consumer is not None

        return OrderDto(
            id=entity.id,
            business=await self._business_service.to_dto(business),
            consumer=await self._consumer_service.to_dto(consumer),
            latest_time_of_delivery=entity.latest_time_of_delivery,
            parcel=await self._parcel_service.to_dto(entity.parcel),
            order_status=entity.order_status,
            bill=await self._bill_service.to_dto(entity.bill),
        )

    def _generate_order_number(self):
        now = datetime.now(UTC)
        date_time_segment = now.strftime("%m%H%M%S")
        return f"easy-{now.year}-{date_time_segment}"
