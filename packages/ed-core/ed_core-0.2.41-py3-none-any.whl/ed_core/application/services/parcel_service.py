from datetime import UTC, datetime

from ed_domain.common.logging import get_logger
from ed_domain.core.entities.parcel import Parcel
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.business.dtos.create_parcel_dto import \
    CreateParcelDto
from ed_core.application.features.common.dtos.parcel_dto import ParcelDto
from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class ParcelService(ABCService[Parcel, CreateParcelDto, None, ParcelDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Parcel", uow.parcel_repository)

        self._uow = uow
        LOG.info("ParcelService initialized with UnitOfWork.")

    async def create(self, dto: CreateParcelDto) -> Parcel:
        parcel = Parcel(
            id=get_new_id(),
            size=dto["size"],
            length=dto["length"],
            width=dto["width"],
            height=dto["height"],
            weight=dto["weight"],
            fragile=dto["fragile"],
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        parcel = await self._uow.parcel_repository.create(parcel)
        LOG.info(f"Parcel created with ID: {parcel.id}")
        return parcel

    async def to_dto(self, entity: Parcel) -> ParcelDto:
        return ParcelDto(**entity.__dict__)
