from datetime import UTC, datetime, timedelta
from typing import TypedDict
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.core.entities import Otp
from ed_domain.core.entities.otp import OtpType
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_core.application.services.abc_service import ABCService
from ed_core.common.generic_helpers import get_new_id

LOG = get_logger()


class CreateOtpDto(TypedDict):
    user_id: UUID
    value: str
    otp_type: OtpType


class OtpService(ABCService[Otp, CreateOtpDto, None, None]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow
        LOG.info("OtpService initialized with UnitOfWork.")

    async def create(self, dto: CreateOtpDto) -> Otp:
        otp = Otp(
            id=get_new_id(),
            user_id=dto["user_id"],
            value=dto["value"],
            otp_type=dto["otp_type"],
            expiry_datetime=datetime.now(UTC) + timedelta(minutes=5),
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        otp = await self._uow.otp_repository.create(otp)
        LOG.info(f"Otp created with ID: {otp.id}")
        return otp
