from dataclasses import dataclass
from uuid import UUID

from rmediator.decorators import request
from rmediator.mediator import Request

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos.order_dto import OrderDto
from ed_core.application.features.consumer.dtos import RateDeliveryDto


@request(BaseResponse[OrderDto])
@dataclass
class RateDeliveryCommand(Request):
    consumer_id: UUID
    order_id: UUID
    dto: RateDeliveryDto
