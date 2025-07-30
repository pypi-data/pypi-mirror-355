from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.common.logging import get_logger
from ed_domain.core.entities.api_key import ApiKeyStatus
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from ed_domain.utils.security.password import ABCPasswordHandler
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.business.requests.queries import \
    VerifyApiKeyQuery
from ed_core.application.features.common.dtos.business_dto import BusinessDto
from ed_core.application.services import ApiKeyService
from ed_core.application.services.business_service import BusinessService

LOG = get_logger()


@request_handler(VerifyApiKeyQuery, BaseResponse[BusinessDto])
class VerifyApiKeyQueryHandler(RequestHandler):

    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
        password: ABCPasswordHandler,
    ):
        self._uow = uow
        self._password = password
        self._api_key_service = ApiKeyService(uow)
        self._business_service = BusinessService(uow)

        self._error_message = "API key was not verified successfully."
        self._success_message = "API key verified successfully."

    async def handle(self, request: VerifyApiKeyQuery) -> BaseResponse[BusinessDto]:
        full_api_key = request.api_key
        prefix = full_api_key.split("_")[0]

        async with self._uow.transaction():
            api_key = await self._api_key_service.get_api_key_by_prefix(prefix)
            print("API", api_key)

            if not api_key:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    [f"API key record not found for prefix: {prefix}"],
                )

            if api_key.status != ApiKeyStatus.ACTIVE:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    [f"API key with prefix {prefix} is inactive."],
                )

            if not self._password.verify(full_api_key, api_key.key_hash):
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    self._error_message,
                    [f"API key verification failed for prefix: {prefix}."],
                )

            business = await self._business_service.get_by_id(api_key.business_id)
            assert business is not None

            business_dto = await self._business_service.to_dto(business)

        return BaseResponse[BusinessDto].success(self._success_message, business_dto)
