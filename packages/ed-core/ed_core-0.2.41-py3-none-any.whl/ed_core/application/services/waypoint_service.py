from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.entities.waypoint import Waypoint, WaypointType
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.common.dtos.waypoint_dto import WaypointDto
from ed_core.application.features.delivery_job.dtos.create_waypoint_dto import \
    CreateWaypointDto
from ed_core.application.services.abc_service import ABCService
from ed_core.application.services.order_service import OrderService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class WaypointService(ABCService[Waypoint, CreateWaypointDto, None, WaypointDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Waypoint", uow.waypoint_repository)

        self._order_service = OrderService(uow)

        LOG.info("WaypointService initialized with UnitOfWork.")

    async def get_order_waypoint(
        self, order_id: UUID, waypoint_type: WaypointType
    ) -> Optional[Waypoint]:
        return await self._repository.get(
            order_id=order_id, waypoint_type=waypoint_type
        )

    async def create_waypoint(
        self, dto: CreateWaypointDto, delivery_job_id: UUID
    ) -> Waypoint:
        waypoint = Waypoint(
            id=get_new_id(),
            delivery_job_id=delivery_job_id,
            order_id=dto["order_id"],
            expected_arrival_time=dto["expected_arrival_time"],
            actual_arrival_time=dto["actual_arrival_time"],
            sequence=dto["sequence"],
            waypoint_type=dto["waypoint_type"],
            waypoint_status=dto["waypoint_status"],
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        waypoint = await self._repository.create(waypoint)
        LOG.info(f"Waypoint created with ID: {waypoint.id}")
        return waypoint

    async def to_dto(self, entity: Waypoint) -> WaypointDto:
        order = await self._order_service.get(entity.order_id)
        assert order is not None

        return WaypointDto(
            order=await self._order_service.to_dto(order),
            type=entity.waypoint_type,
            expected_arrival_time=entity.expected_arrival_time,
            sequence=entity.sequence,
        )
