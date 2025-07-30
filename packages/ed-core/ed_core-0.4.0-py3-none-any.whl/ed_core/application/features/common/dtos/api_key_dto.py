from typing import Optional, TypedDict

from ed_domain.core.entities.api_key import ApiKeyStatus


class ApiKeyDto(TypedDict):
    name: str
    description: str
    prefix: str
    status: ApiKeyStatus
    key: Optional[str]
