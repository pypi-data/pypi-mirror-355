from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DeliveryJobDto
from ed_core.application.features.delivery_job.requests.commands.create_delivery_job_command import \
    CreateDeliveryJobCommand
from ed_core.application.services.delivery_job_service import \
    DeliveryJobService
from ed_core.application.services.waypoint_service import WaypointService


@request_handler(CreateDeliveryJobCommand, BaseResponse[DeliveryJobDto])
class CreateDeliveryJobCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._delivery_job_service = DeliveryJobService(uow)
        self._waypoint_service = WaypointService(uow)

        self._error_message = "Delivery job was not created."
        self._success_message = "Delivery job created successfully."

    async def handle(
        self, request: CreateDeliveryJobCommand
    ) -> BaseResponse[DeliveryJobDto]:
        async with self._uow.transaction():
            delivery_job = await self._delivery_job_service.create(request.dto)

            for waypoint_dto in request.dto.waypoints:
                waypoint = await self._waypoint_service.create_waypoint(
                    waypoint_dto, delivery_job.id
                )
                delivery_job.add_waypoint(waypoint)

            delivery_job_dto = await self._delivery_job_service.to_dto(delivery_job)

        return BaseResponse[DeliveryJobDto].success(
            self._success_message, delivery_job_dto
        )
