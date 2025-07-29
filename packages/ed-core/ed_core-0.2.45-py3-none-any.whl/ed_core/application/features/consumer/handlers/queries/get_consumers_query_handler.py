from dataclasses import dataclass

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import ConsumerDto
from ed_core.application.features.consumer.requests.queries import \
    GetConsumersQuery
from ed_core.application.services.consumer_service import ConsumerService


@request_handler(GetConsumersQuery, BaseResponse[list[ConsumerDto]])
@dataclass
class GetConsumersQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._consumer_service = ConsumerService(uow)

        self._success_message = "Consumers fetched successfully."

    async def handle(
        self, request: GetConsumersQuery
    ) -> BaseResponse[list[ConsumerDto]]:
        async with self._uow.transaction():
            consumers = await self._uow.consumer_repository.get_all()
            consumer_dtos = [
                await self._consumer_service.to_dto(consumer) for consumer in consumers
            ]

        return BaseResponse[list[ConsumerDto]].success(
            self._success_message, consumer_dtos
        )
