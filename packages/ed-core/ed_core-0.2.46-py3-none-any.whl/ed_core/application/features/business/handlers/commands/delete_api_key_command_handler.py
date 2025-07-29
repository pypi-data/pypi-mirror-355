from ed_auth.application.common.responses.base_response import BaseResponse
from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.features.business.requests.commands import \
    DeleteApiKeyCommand
from ed_core.application.services.api_key_service import ApiKeyService

LOG = get_logger()


@request_handler(DeleteApiKeyCommand, BaseResponse[None])
class DeleteApiKeyCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._api_key_service = ApiKeyService(uow)
        self._success_message = "ApiKey deleted successfully."
        self._error_message = "ApiKey deletion failed."

    async def handle(self, request: DeleteApiKeyCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            api_key = await self._api_key_service.get_api_key_by_prefix(request.prefix)

            if api_key is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    self._error_message,
                    ["ApiKey not found."],
                )

            if api_key.business_id != request.business_id:
                raise ApplicationException(
                    Exceptions.UnauthorizedException,
                    self._error_message,
                    ["ApiKey blongs to different business"],
                )

            deleted = await self._uow.api_key_repository.delete(api_key.id)

            if not deleted:
                raise ApplicationException(
                    Exceptions.InternalServerException,
                    self._error_message,
                    ["Internal server error."],
                )

        return BaseResponse[None].success(self._success_message, None)
