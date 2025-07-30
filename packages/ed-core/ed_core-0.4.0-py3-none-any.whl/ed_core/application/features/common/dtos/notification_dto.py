from datetime import datetime
from uuid import UUID

from ed_domain.core.entities.notification import NotificationType
from typing import TypedDict


class NotificationDto(TypedDict):
    id: UUID
    user_id: UUID
    notification_type: NotificationType
    message: str
    read_status: bool
    create_datetime: datetime
