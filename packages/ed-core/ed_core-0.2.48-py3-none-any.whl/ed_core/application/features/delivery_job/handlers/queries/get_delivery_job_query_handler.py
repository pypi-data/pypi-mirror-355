from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DeliveryJobDto
from ed_core.application.features.delivery_job.requests.queries.get_delivery_job_query import \
    GetDeliveryJobQuery
from ed_core.application.services import DeliveryJobService


@request_handler(GetDeliveryJobQuery, BaseResponse[DeliveryJobDto])
class GetDeliveryJobQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._delivery_job_service = DeliveryJobService(uow)

    async def handle(
        self, request: GetDeliveryJobQuery
    ) -> BaseResponse[DeliveryJobDto]:
        async with self._uow.transaction():
            delivery_job = await self._delivery_job_service.get(request.delivery_job_id)

            if delivery_job is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    "Delivery job not found.",
                    [f"Delivery job with id {request.delivery_job_id} not found."],
                )

            delivery_job_dto = await self._delivery_job_service.to_dto(delivery_job)

        return BaseResponse[DeliveryJobDto].success(
            "Delivery job fetched successfully.", delivery_job_dto
        )
