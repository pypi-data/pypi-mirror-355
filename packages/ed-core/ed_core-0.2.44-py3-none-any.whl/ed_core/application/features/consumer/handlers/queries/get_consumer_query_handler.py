from dataclasses import dataclass

from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import ConsumerDto
from ed_core.application.features.consumer.requests.queries.get_consumer_query import \
    GetConsumerQuery
from ed_core.application.services.consumer_service import ConsumerService


@request_handler(GetConsumerQuery, BaseResponse[ConsumerDto])
@dataclass
class GetConsumerQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._consumer_service = ConsumerService(uow)

        self._error_message = "Consumer couldn't be fetched."
        self._success_message = "Consumer fetched successfully."

    async def handle(self, request: GetConsumerQuery) -> BaseResponse[ConsumerDto]:
        async with self._uow.transaction():
            consumer = await self._uow.consumer_repository.get(id=request.consumer_id)

            if consumer is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    self._error_message,
                    [f"Consumer with id {request.consumer_id} does not exist."],
                )

            consumer_dto = await self._consumer_service.to_dto(consumer)

        return BaseResponse[ConsumerDto].success(self._success_message, consumer_dto)
