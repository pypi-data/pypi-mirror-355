from dataclasses import dataclass
from uuid import UUID

from ed_auth.application.common.responses.base_response import BaseResponse
from rmediator.decorators import request
from rmediator.mediator import Request


@request(BaseResponse[None])
@dataclass
class DeleteApiKeyCommand(Request):
    business_id: UUID
    prefix: str
