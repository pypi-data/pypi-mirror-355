from datetime import datetime
from typing import TypedDict
from uuid import UUID

from ed_core.application.features.business.dtos.create_parcel_dto import \
    CreateParcelDto


class CreateOrderDto(TypedDict):
    consumer_id: UUID
    latest_time_of_delivery: datetime
    parcel: CreateParcelDto
