from datetime import datetime
from typing import Optional
from uuid import UUID

from ed_domain.core.aggregate_roots.delivery_job import DeliveryJobStatus
from pydantic import BaseModel

from ed_core.application.features.common.dtos.waypoint_dto import WaypointDto


class DeliveryJobDto(BaseModel):
    id: UUID
    waypoints: list[WaypointDto]
    estimated_distance_in_kms: float
    estimated_time_in_minutes: int
    driver: Optional[UUID]
    status: DeliveryJobStatus
    estimated_payment_in_birr: float
    estimated_completion_time: datetime
