from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Business
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.business.dtos.create_business_dto import \
    CreateBusinessDto
from ed_core.application.features.business.dtos.update_business_dto import \
    UpdateBusinessDto
from ed_core.application.features.common.dtos.business_dto import BusinessDto
from ed_core.application.services.abc_service import ABCService
from ed_core.application.services.location_service import LocationService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class BusinessService(
    ABCService[Business, CreateBusinessDto, UpdateBusinessDto, BusinessDto]
):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Business", uow.business_repository)

        self._uow = uow
        self._location_service = LocationService(self._uow)

        LOG.info("BusinessService initialized with UnitOfWork.")

    async def create(self, dto: CreateBusinessDto) -> Business:
        location = await self._location_service.create(dto["location"])

        business = Business(
            id=get_new_id(),
            user_id=dto["user_id"],
            business_name=dto["business_name"],
            owner_first_name=dto["owner_first_name"],
            owner_last_name=dto["owner_last_name"],
            phone_number=dto["phone_number"],
            email=dto["email"],
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
            location_id=location.id,
            api_keys=[],
        )
        business = await self._uow.business_repository.create(business)
        LOG.info(f"Business created with ID: {business.id}")
        return business

    async def update(self, id: UUID, dto: UpdateBusinessDto) -> Optional[Business]:
        business = await self._uow.business_repository.get(id=id)
        if not business:
            LOG.error(f"Cannot update: No business found for ID: {id}")
            return None

        if "phone_number" in dto:
            business.phone_number = dto["phone_number"]
        if "email" in dto:
            business.email = dto["email"]
        if "location" in dto:
            updated_location = await self._location_service.update(
                business.location_id, dto["location"]
            )
            assert updated_location is not None

            business.location_id = updated_location.id

        business.update_datetime = datetime.now(UTC)
        updated = await self._uow.business_repository.save(business)

        LOG.info(f"Business with ID: {id} updated {updated}.")
        return business

    async def to_dto(self, entity: Business) -> BusinessDto:
        location = await self._location_service.get(entity.location_id)
        assert location is not None

        location_dto = await self._location_service.to_dto(location)

        return BusinessDto(
            id=entity.id,
            business_name=entity.business_name,
            owner_first_name=entity.owner_first_name,
            owner_last_name=entity.owner_last_name,
            phone_number=entity.phone_number,
            email=entity.email,
            location=location_dto,
        )
