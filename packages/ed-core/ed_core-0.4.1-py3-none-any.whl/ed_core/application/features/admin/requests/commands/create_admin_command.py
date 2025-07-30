from dataclasses import dataclass

from rmediator.decorators import request
from rmediator.mediator import Request

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.admin.dtos import CreateAdminDto
from ed_core.application.features.common.dtos import AdminDto


@request(BaseResponse[AdminDto])
@dataclass
class CreateAdminCommand(Request):
    dto: CreateAdminDto
