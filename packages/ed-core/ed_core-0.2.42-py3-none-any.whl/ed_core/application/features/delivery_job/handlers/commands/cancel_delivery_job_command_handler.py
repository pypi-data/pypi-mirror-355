from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DeliveryJobDto
from ed_core.application.features.delivery_job.requests.commands import \
    CancelDeliveryJobCommand
from ed_core.application.services.delivery_job_service import \
    DeliveryJobService


@request_handler(CancelDeliveryJobCommand, BaseResponse[DeliveryJobDto])
class CancelDeliveryJobCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._delivery_job_service = DeliveryJobService(uow)

        self._error_message = "Delivery job cancelling failed."
        self._success_message = "Delivery job cancelled successfully."

    async def handle(
        self, request: CancelDeliveryJobCommand
    ) -> BaseResponse[DeliveryJobDto]:
        async with self._uow.transaction():
            delivery_job = await self._uow.delivery_job_repository.get(
                id=request.delivery_job_id
            )

            if delivery_job is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    self._error_message,
                    [f"Delivery job with id {request.delivery_job_id} not found."],
                )

            delivery_job.cancel_job()
            updated = await self._uow.delivery_job_repository.update(
                delivery_job.id, delivery_job
            )

            delivery_job_dto = await self._delivery_job_service.to_dto(delivery_job)

        if not updated:
            raise ApplicationException(
                Exceptions.NotFoundException,
                self._error_message,
                ["Internal server error occured."],
            )

        return BaseResponse[DeliveryJobDto].success(
            self._success_message, delivery_job_dto
        )
