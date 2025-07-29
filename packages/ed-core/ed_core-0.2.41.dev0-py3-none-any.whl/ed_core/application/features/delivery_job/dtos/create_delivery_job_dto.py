from datetime import datetime
from typing import TypedDict

from ed_core.application.features.delivery_job.dtos.create_waypoint_dto import \
    CreateWaypointDto


class CreateDeliveryJobDto(TypedDict):
    waypoints: list[CreateWaypointDto]
    estimated_distance_in_kms: float
    estimated_time_in_minutes: int
    estimated_payment: float
    estimated_completion_time: datetime
