from typing import TypedDict
from uuid import UUID

from ed_domain.core.aggregate_roots.admin import AdminRole


class AdminDto(TypedDict):
    id: UUID
    first_name: str
    last_name: str
    phone_number: str
    email: str
    role: AdminRole
