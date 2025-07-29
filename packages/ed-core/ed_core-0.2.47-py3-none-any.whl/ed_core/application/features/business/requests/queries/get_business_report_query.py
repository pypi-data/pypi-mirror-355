from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from rmediator.decorators import request
from rmediator.mediator import Request

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.dtos import BusinessReportDto


@request(BaseResponse[BusinessReportDto])
@dataclass
class GetBusinessReportQuery(Request):
    business_id: UUID

    report_start_date: Optional[datetime]
    report_end_date: Optional[datetime]
