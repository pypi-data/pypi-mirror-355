from datetime import UTC, datetime
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.entities.webhook import Webhook
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.business.dtos.create_webhook_dto import \
    CreateWebhookDto
from ed_core.application.features.common.dtos import WebhookDto
from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class WebhookService(ABCService[Webhook, CreateWebhookDto, None, WebhookDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Webhook", uow.webhook_repository)

        LOG.info("WebhookService initialized with UnitOfWork.")

    async def create_webhook(self, dto: CreateWebhookDto, business_id: UUID) -> Webhook:
        webhook = Webhook(
            id=get_new_id(),
            business_id=business_id,
            url=dto["url"],
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        webhook = await self._repository.create(webhook)
        LOG.info(f"Webhook created with ID: {webhook.id}")
        return webhook

    async def to_dto(self, entity: Webhook) -> WebhookDto:
        return WebhookDto(**entity.__dict__)
