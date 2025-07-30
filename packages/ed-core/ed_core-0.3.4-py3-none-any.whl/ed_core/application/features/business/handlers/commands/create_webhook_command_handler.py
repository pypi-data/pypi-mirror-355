from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.requests.commands import \
    CreateWebhookCommand
from ed_core.application.features.common.dtos import WebhookDto
from ed_core.application.services import WebhookService

LOG = get_logger()


@request_handler(CreateWebhookCommand, BaseResponse[WebhookDto])
class CreateWebhookCommandHandler(RequestHandler):
    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
    ):
        self._uow = uow

        self._webhook_service = WebhookService(uow)

        self._error_message = "Failed to created Webhook."
        self._success_message = "Webhook created succesfully."

    async def handle(self, request: CreateWebhookCommand) -> BaseResponse[WebhookDto]:
        async with self._uow.transaction():
            webhook = await self._webhook_service.create_webhook(
                request.dto, request.business_id
            )
            webhook_dto = await self._webhook_service.to_dto(webhook)

        return BaseResponse[WebhookDto].success(self._success_message, webhook_dto)
