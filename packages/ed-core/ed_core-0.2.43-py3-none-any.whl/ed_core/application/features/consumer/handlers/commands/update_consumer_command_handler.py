from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos.consumer_dto import ConsumerDto
from ed_core.application.features.consumer.dtos.validators import \
    UpdateConsumerDtoValidator
from ed_core.application.features.consumer.requests.commands import \
    UpdateConsumerCommand
from ed_core.application.services import ConsumerService

LOG = get_logger()


@request_handler(UpdateConsumerCommand, BaseResponse[ConsumerDto])
class UpdateConsumerCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._consumer_service = ConsumerService(uow)

        self._error_message = "Update consumer failed."
        self._success_message = "Consumer updated successfully."

    async def handle(self, request: UpdateConsumerCommand) -> BaseResponse[ConsumerDto]:
        dto_validator = UpdateConsumerDtoValidator().validate(request.dto)

        if not dto_validator.is_valid:
            raise ApplicationException(
                Exceptions.ValidationException,
                self._error_message,
                dto_validator.errors,
            )

        async with self._uow.transaction():
            consumer = await self._consumer_service.update(
                request.consumer_id, request.dto
            )
            assert consumer is not None

            consumer_dto = await self._consumer_service.to_dto(consumer)

        return BaseResponse[ConsumerDto].success(self._success_message, consumer_dto)
