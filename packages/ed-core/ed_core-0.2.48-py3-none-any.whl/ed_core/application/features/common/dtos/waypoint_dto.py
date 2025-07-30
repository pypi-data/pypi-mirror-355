from datetime import datetime

from ed_domain.core.entities.waypoint import WaypointType
from pydantic import BaseModel

from ed_core.application.features.common.dtos.order_dto import OrderDto


class WaypointDto(BaseModel):
    order: OrderDto
    type: WaypointType
    expected_arrival_time: datetime
    sequence: int
