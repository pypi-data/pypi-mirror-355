from typing import Annotated
from uuid import UUID

from ed_domain.common.logging import get_logger
from fastapi import APIRouter, Depends
from rmediator.mediator import Mediator

from ed_core.application.features.admin.dtos import (
    CreateAdminDto, SettleDriverPaymentRequestDto, UpdateAdminDto)
from ed_core.application.features.admin.requests.commands import (
    CreateAdminCommand, SettleDriverPaymentCommand, UpdateAdminCommand)
from ed_core.application.features.admin.requests.queries import (
    GetAdminByUserIdQuery, GetAdminQuery, GetAdminsQuery)
from ed_core.application.features.common.dtos import AdminDto
from ed_core.application.features.driver.dtos import DriverPaymentSummaryDto
from ed_core.webapi.common.helpers import GenericResponse, rest_endpoint
from ed_core.webapi.dependency_setup import mediator

LOG = get_logger()
router = APIRouter(prefix="/admins", tags=["Admin Feature"])


@router.get("", response_model=GenericResponse[list[AdminDto]])
@rest_endpoint
async def get_all_admins(
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetAdminsQuery())


@router.post("", response_model=GenericResponse[AdminDto])
@rest_endpoint
async def create_admin(
    request_dto: CreateAdminDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(CreateAdminCommand(dto=request_dto))


@router.get("/{admin_id}", response_model=GenericResponse[AdminDto])
@rest_endpoint
async def get_admin(
    admin_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetAdminQuery(admin_id))


@router.put("/{admin_id}", response_model=GenericResponse[AdminDto])
@rest_endpoint
async def update_admin(
    admin_id: UUID,
    dto: UpdateAdminDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):

    return await mediator.send(UpdateAdminCommand(admin_id, dto))


@router.post(
    "/{admin_id}/settle-driver-payment/{driver_id}",
    response_model=GenericResponse[DriverPaymentSummaryDto],
)
@rest_endpoint
async def settle_driver_payment(
    admin_id: UUID,
    driver_id: UUID,
    dto: SettleDriverPaymentRequestDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(SettleDriverPaymentCommand(admin_id, driver_id, dto))


@router.get("/users/{user_id}", response_model=GenericResponse[AdminDto])
@rest_endpoint
async def get_admin_by_user_id(
    user_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetAdminByUserIdQuery(user_id))
