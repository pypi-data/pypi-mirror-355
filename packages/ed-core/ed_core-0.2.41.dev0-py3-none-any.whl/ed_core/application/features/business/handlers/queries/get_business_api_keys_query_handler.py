from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.requests.queries import \
    GetBusinessApiKeysQuery
from ed_core.application.features.common.dtos.api_key_dto import ApiKeyDto
from ed_core.application.services.api_key_service import ApiKeyService


@request_handler(GetBusinessApiKeysQuery, BaseResponse[list[ApiKeyDto]])
class GetBusinessApiKeysQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._api_key_service = ApiKeyService(uow)

        self._success_message = "API keys retrieved succesfully."
        self._error_message = "API keys were not retrieved succesfuly."

    async def handle(
        self, request: GetBusinessApiKeysQuery
    ) -> BaseResponse[list[ApiKeyDto]]:
        async with self._uow.transaction():
            api_keys = await self._uow.api_key_repository.get_all(
                business_id=request.business_id
            )
            api_key_dtos = [
                await self._api_key_service.to_dto(api_key) for api_key in api_keys
            ]

        return BaseResponse[list[ApiKeyDto]].success(
            self._success_message, api_key_dtos
        )
