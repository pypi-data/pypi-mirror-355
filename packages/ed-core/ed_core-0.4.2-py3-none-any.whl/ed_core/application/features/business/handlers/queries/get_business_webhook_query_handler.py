from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.requests.queries import \
    GetBusinessWebhookQuery
from ed_core.application.features.common.dtos.webhook_dto import WebhookDto
from ed_core.application.services.webhook_service import WebhookService


@request_handler(GetBusinessWebhookQuery, BaseResponse[WebhookDto])
class GetBusinessWebhookQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._webhook_service = WebhookService(uow)

        self._success_message = "Webhook retrieved succesfully."
        self._error_message = "Webhook were not retrieved succesfuly."

    async def handle(
        self, request: GetBusinessWebhookQuery
    ) -> BaseResponse[WebhookDto]:
        async with self._uow.transaction():
            webhook = await self._uow.webhook_repository.get(
                business_id=request.business_id
            )
            if webhook is None:
                return BaseResponse[WebhookDto].success(
                    self._success_message, WebhookDto(url="")
                )

            webhook_dto = await self._webhook_service.to_dto(webhook)

        return BaseResponse[WebhookDto].success(self._success_message, webhook_dto)
