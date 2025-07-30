from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.requests.queries import \
    GetBusinessApiKeyByPrefixQuery
from ed_core.application.features.common.dtos.api_key_dto import ApiKeyDto
from ed_core.application.services.api_key_service import ApiKeyService


@request_handler(GetBusinessApiKeyByPrefixQuery, BaseResponse[ApiKeyDto])
class GetBusinessApiKeyByPrefixQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._api_key_service = ApiKeyService(uow)

        self._success_message = "API key retrieved succesfully."
        self._error_message = "API key were not retrieved succesfuly."

    async def handle(
        self, request: GetBusinessApiKeyByPrefixQuery
    ) -> BaseResponse[ApiKeyDto]:
        async with self._uow.transaction():
            api_key = await self._api_key_service.get_api_key_by_prefix(
                request.api_key_prefix
            )
            if api_key is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    self._error_message,
                    [f"API key with prefix {request.api_key_prefix} not found."],
                )

            api_key_dto = await self._api_key_service.to_dto(api_key)

        return BaseResponse[ApiKeyDto].success(self._success_message, api_key_dto)
