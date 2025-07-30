from dataclasses import dataclass
from uuid import UUID

from rmediator.decorators import request
from rmediator.mediator import Request

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.admin.dtos import \
    SettleDriverPaymentRequestDto
from ed_core.application.features.driver.dtos import DriverPaymentSummaryDto


@request(BaseResponse[DriverPaymentSummaryDto])
@dataclass
class SettleDriverPaymentCommand(Request):
    admin_id: UUID
    driver_id: UUID
    dto: SettleDriverPaymentRequestDto
