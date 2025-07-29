from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Consumer
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.common.dtos.consumer_dto import ConsumerDto
from ed_core.application.features.common.dtos.create_consumer_dto import \
    CreateConsumerDto
from ed_core.application.features.consumer.dtos.update_consumer_dto import \
    UpdateConsumerDto
from ed_core.application.services.abc_service import ABCService
from ed_core.application.services.location_service import LocationService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class ConsumerService(
    ABCService[Consumer, CreateConsumerDto, UpdateConsumerDto, ConsumerDto]
):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Consumer", uow.consumer_repository)

        self._uow = uow
        self._location_service = LocationService(self._uow)

        LOG.info("ConsumerService initialized with UnitOfWork.")

    async def create(self, dto: CreateConsumerDto) -> Consumer:
        location = await self._location_service.create(dto["location"])

        consumer = Consumer(
            id=get_new_id(),
            user_id=dto["user_id"],
            first_name=dto["first_name"],
            last_name=dto["last_name"],
            phone_number=dto["phone_number"],
            email=dto["email"],
            profile_image_url="",
            location_id=location.id,
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        consumer = await self._uow.consumer_repository.create(consumer)
        LOG.info(f"Consumer created with ID: {consumer.id}")
        return consumer

    async def update(self, id: UUID, dto: UpdateConsumerDto) -> Optional[Consumer]:
        consumer = await self._uow.consumer_repository.get(id=id)
        if not consumer:
            LOG.error(f"Cannot update: No consumer found for ID: {id}")
            return None

        if "location" in dto:
            updated_location = await self._location_service.update(
                consumer.location_id, dto["location"]
            )
            assert updated_location is not None

            consumer.location_id = updated_location.id

        if "profile_image_url" in dto:
            consumer.profile_image_url = dto["profile_image_url"]

        consumer.update_datetime = datetime.now(UTC)
        await self._uow.consumer_repository.save(consumer)

        LOG.info(f"Consumer with ID: {id} updated.")
        return consumer

    async def to_dto(self, entity: Consumer) -> ConsumerDto:
        location = await self._location_service.get(entity.location_id)
        assert location is not None

        location_dto = await self._location_service.to_dto(location)

        return ConsumerDto(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone_number=entity.phone_number,
            email=entity.email,
            location=location_dto,
        )
