from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DeliveryJobDto
from ed_core.application.features.driver.requests.queries.get_driver_delivery_jobs_query import \
    GetDriverDeliveryJobsQuery
from ed_core.application.services import DeliveryJobService


@request_handler(GetDriverDeliveryJobsQuery, BaseResponse[list[DeliveryJobDto]])
class GetDriverDeliveryJobsQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._delivery_job_service = DeliveryJobService(uow)

    async def handle(
        self, request: GetDriverDeliveryJobsQuery
    ) -> BaseResponse[list[DeliveryJobDto]]:
        async with self._uow.transaction():
            delivery_jobs = await self._uow.delivery_job_repository.get_all(
                driver_id=request.driver_id
            )
            delivery_job_dtos = [
                await self._delivery_job_service.to_dto(delivery_job)
                for delivery_job in delivery_jobs
            ]

        return BaseResponse[list[DeliveryJobDto]].success(
            "Driver delivery jobs fetched successfully.", delivery_job_dtos
        )
