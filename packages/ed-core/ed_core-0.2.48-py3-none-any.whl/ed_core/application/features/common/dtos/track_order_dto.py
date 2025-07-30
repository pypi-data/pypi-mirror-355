from typing import Optional

from pydantic import BaseModel

from ed_core.application.features.common.dtos.driver_dto import DriverDto
from ed_core.application.features.common.dtos.order_dto import OrderDto


class TrackOrderDto(BaseModel):
    order: OrderDto
    driver: Optional[DriverDto]
