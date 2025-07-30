from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Admin
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.features.admin.dtos import (CreateAdminDto,
                                                     UpdateAdminDto)
from ed_core.application.features.common.dtos.admin_dto import AdminDto
from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class AdminService(ABCService[Admin, CreateAdminDto, UpdateAdminDto, AdminDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Admin", uow.admin_repository)

        LOG.info("AdminService initialized with UnitOfWork.")

    async def create(self, dto: CreateAdminDto) -> Admin:
        admin = Admin(
            id=get_new_id(),
            user_id=dto["user_id"],
            first_name=dto["first_name"],
            last_name=dto["last_name"],
            phone_number=dto["phone_number"],
            email=dto["email"],
            role=dto["role"],
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        admin = await self._repository.create(admin)
        LOG.info(f"Admin created with ID: {admin.id}")
        return admin

    async def update(self, id: UUID, dto: UpdateAdminDto) -> Optional[Admin]:
        admin = await self._repository.get(id=id)
        if not admin:
            LOG.error(f"Cannot update: No admin found for ID: {id}")
            return None

        admin.update_datetime = datetime.now(UTC)
        await self._repository.save(admin)

        LOG.info(f"Admin with ID: {id} updated.")
        return admin

    async def to_dto(self, entity: Admin) -> AdminDto:
        return AdminDto(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone_number=entity.phone_number,
            email=entity.email,
            role=entity.role,
        )
