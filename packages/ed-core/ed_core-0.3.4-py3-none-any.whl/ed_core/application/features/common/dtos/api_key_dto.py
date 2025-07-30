from ed_domain.core.entities.api_key import ApiKeyStatus
from typing import TypedDict


class ApiKeyDto(TypedDict):
    name: str
    description: str
    prefix: str
    status: ApiKeyStatus
    key: str | None = None
