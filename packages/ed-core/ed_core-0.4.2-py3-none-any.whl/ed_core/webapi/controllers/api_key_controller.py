from typing import Annotated

from ed_domain.common.logging import get_logger
from fastapi import APIRouter, Depends
from rmediator.mediator import Mediator

from ed_core.application.features.business.requests.queries import (
    GetBusinessApiKeyByPrefixQuery, VerifyApiKeyQuery)
from ed_core.application.features.common.dtos import ApiKeyDto
from ed_core.application.features.common.dtos.business_dto import BusinessDto
from ed_core.webapi.common.helpers import GenericResponse, rest_endpoint
from ed_core.webapi.dependency_setup import mediator

LOG = get_logger()
router = APIRouter(prefix="/api-keys", tags=["ApiKey Feature"])


@router.get("/{api_key_prefix}", response_model=GenericResponse[ApiKeyDto])
@rest_endpoint
async def get_api_key_by_prefix(
    api_key_prefix: str,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(GetBusinessApiKeyByPrefixQuery(api_key_prefix))


@router.get(
    "/{api_key}/verify",
    response_model=GenericResponse[BusinessDto],
)
@rest_endpoint
async def verify_api_key(
    api_key: str,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(VerifyApiKeyQuery(api_key))
