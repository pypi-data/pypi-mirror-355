from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from ed_domain.common.logging import get_logger
from fastapi import APIRouter, Depends
from rmediator.mediator import Mediator

from ed_core.application.features.business.dtos import (BusinessReportDto,
                                                        CreateApiKeyDto,
                                                        CreateBusinessDto,
                                                        CreateOrderDto,
                                                        UpdateBusinessDto)
from ed_core.application.features.business.requests.commands import (
    CreateApiKeyCommand, CreateBusinessCommand, CreateOrderCommand,
    UpdateBusinessCommand)
from ed_core.application.features.business.requests.queries import (
    GetAllBusinessQuery, GetBusinessApiKeysQuery, GetBusinessByUserIdQuery,
    GetBusinessOrdersQuery, GetBusinessQuery, GetBusinessReportQuery)
from ed_core.application.features.common.dtos import BusinessDto, OrderDto
from ed_core.application.features.common.dtos.api_key_dto import ApiKeyDto
from ed_core.webapi.common.helpers import GenericResponse, rest_endpoint
from ed_core.webapi.dependency_setup import mediator

LOG = get_logger()
router = APIRouter(prefix="/businesses", tags=["Business Feature"])


@router.post("/", response_model=GenericResponse[BusinessDto])
@rest_endpoint
async def create_business(
    request_dto: CreateBusinessDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(CreateBusinessCommand(dto=request_dto))


@router.get("/", response_model=GenericResponse[list[BusinessDto]])
@rest_endpoint
async def get_all_businesses(
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetAllBusinessQuery())


@router.put("/{business_id}", response_model=GenericResponse[BusinessDto])
@rest_endpoint
async def update_business(
    business_id: UUID,
    dto: UpdateBusinessDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(UpdateBusinessCommand(id=business_id, dto=dto))


@router.get("/{business_id}", response_model=GenericResponse[BusinessDto])
@rest_endpoint
async def get_business(
    business_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetBusinessQuery(business_id=business_id))


@router.get("/users/{user_id}", response_model=GenericResponse[BusinessDto])
@rest_endpoint
async def get_business_by_user_id(
    user_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetBusinessByUserIdQuery(user_id=user_id))


@router.get("/{business_id}/orders", response_model=GenericResponse[list[OrderDto]])
@rest_endpoint
async def get_business_orders(
    business_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetBusinessOrdersQuery(business_id=business_id))


@router.post("/{business_id}/orders", response_model=GenericResponse[OrderDto])
@rest_endpoint
async def create_order(
    business_id: UUID,
    request_dto: CreateOrderDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(
        CreateOrderCommand(business_id=business_id, dto=request_dto)
    )


@router.get("/{business_id}/api-keys", response_model=GenericResponse[list[ApiKeyDto]])
@rest_endpoint
async def get_business_api_keys(
    business_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetBusinessApiKeysQuery(business_id=business_id))


@router.post("/{business_id}/api-keys", response_model=GenericResponse[ApiKeyDto])
@rest_endpoint
async def create_api_key(
    business_id: UUID,
    dto: CreateApiKeyDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(CreateApiKeyCommand(business_id=business_id, dto=dto))


@router.get("/{business_id}/report", response_model=GenericResponse[BusinessReportDto])
@rest_endpoint
async def get_business_report(
    business_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    return await mediator.send(
        GetBusinessReportQuery(business_id, start_date, end_date)
    )
