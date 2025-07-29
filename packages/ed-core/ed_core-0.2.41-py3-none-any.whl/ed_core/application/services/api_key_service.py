from datetime import UTC, datetime
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.entities.api_key import ApiKey, ApiKeyStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.business.dtos import CreateApiKeyDto
from ed_core.application.features.common.dtos import ApiKeyDto
from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class ApiKeyService(ABCService[ApiKey, CreateApiKeyDto, None, ApiKeyDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("ApiKey", uow.api_key_repository)

        self._uow = uow

        LOG.info("ApiKeyService initialized with UnitOfWork.")

    async def create_api_key(
        self, dto: CreateApiKeyDto, business_id: UUID, prefix: str, key_hash: str
    ) -> ApiKey:
        api_key = ApiKey(
            id=get_new_id(),
            business_id=business_id,
            name=dto["name"],
            description=dto["description"],
            prefix=prefix,
            key_hash=key_hash,
            status=ApiKeyStatus.ACTIVE,
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        api_key = await self._repository.create(api_key)
        LOG.info(f"ApiKey created with ID: {api_key.id}")
        return api_key

    async def to_dto(self, entity: ApiKey) -> ApiKeyDto:
        return ApiKeyDto(**entity.__dict__)
