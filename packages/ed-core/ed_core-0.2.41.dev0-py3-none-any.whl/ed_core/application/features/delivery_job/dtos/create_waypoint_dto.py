from datetime import datetime
from typing import TypedDict
from uuid import UUID

from ed_domain.core.entities.waypoint import WaypointStatus, WaypointType


class CreateWaypointDto(TypedDict):
    order_id: UUID
    expected_arrival_time: datetime
    actual_arrival_time: datetime
    sequence: int
    waypoint_type: WaypointType
    waypoint_status: WaypointStatus
