from datetime import UTC, datetime

from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import DeliveryJob
from ed_domain.core.aggregate_roots.delivery_job import DeliveryJobStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.common.dtos.delivery_job_dto import \
    DeliveryJobDto
from ed_core.application.features.delivery_job.dtos.create_delivery_job_dto import \
    CreateDeliveryJobDto
from ed_core.application.services.abc_service import ABCService
from ed_core.application.services.waypoint_service import WaypointService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class DeliveryJobService(
    ABCService[DeliveryJob, CreateDeliveryJobDto, None, DeliveryJobDto]
):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("DeliveryJob", uow.delivery_job_repository)

        self._uow = uow
        self._waypoint_service = WaypointService(uow)

        LOG.info("DeliveryJobService initialized with UnitOfWork.")

    async def create(self, dto: CreateDeliveryJobDto) -> DeliveryJob:
        delivery_job = DeliveryJob(
            id=get_new_id(),
            waypoints=[],
            estimated_distance_in_kms=dto["estimated_distance_in_kms"],
            estimated_time_in_minutes=dto["estimated_time_in_minutes"],
            estimated_payment_in_birr=dto["estimated_payment"],
            estimated_completion_time=dto["estimated_completion_time"],
            status=DeliveryJobStatus.AVAILABLE,
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        delivery_job = await self._repository.create(delivery_job)
        LOG.info(f"DeliveryJob created with ID: {delivery_job.id}")
        return delivery_job

    async def to_dto(self, entity: DeliveryJob) -> DeliveryJobDto:
        waypoint_dtos = [
            await self._waypoint_service.to_dto(waypoint)
            for waypoint in entity.waypoints
        ]

        return DeliveryJobDto(
            id=entity.id,
            waypoints=waypoint_dtos,
            estimated_distance_in_kms=entity.estimated_distance_in_kms,
            estimated_time_in_minutes=entity.estimated_time_in_minutes,
            driver=entity.driver_id,
            status=entity.status,
            estimated_payment_in_birr=entity.estimated_payment_in_birr,
            estimated_completion_time=entity.estimated_completion_time,
        )
