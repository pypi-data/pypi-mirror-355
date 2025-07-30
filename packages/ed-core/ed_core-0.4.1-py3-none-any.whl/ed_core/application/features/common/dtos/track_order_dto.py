from typing import Optional

from typing import TypedDict

from ed_core.application.features.common.dtos.driver_dto import DriverDto
from ed_core.application.features.common.dtos.order_dto import OrderDto


class TrackOrderDto(TypedDict):
    order: OrderDto
    driver: Optional[DriverDto]
