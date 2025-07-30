from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.core.aggregate_roots.order import OrderStatus
from ed_domain.core.entities.waypoint import WaypointType
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_core.application.common.responses.base_response import BaseResponse
from ed_core.application.features.common.dtos import DeliveryJobDto
from ed_core.application.features.delivery_job.requests.commands.claim_delivery_job_command import \
    ClaimDeliveryJobCommand
from ed_core.application.services.delivery_job_service import \
    DeliveryJobService
from ed_core.application.services.order_service import OrderService


@request_handler(ClaimDeliveryJobCommand, BaseResponse[DeliveryJobDto])
class ClaimDeliveryJobCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

        self._order_service = OrderService(uow)
        self._delivery_job_service = DeliveryJobService(uow)

        self._error_message = "Delivery job was not claimed."
        self._success_message = "Delivery job claimed successfully."

    async def handle(
        self, request: ClaimDeliveryJobCommand
    ) -> BaseResponse[DeliveryJobDto]:
        async with self._uow.transaction():
            delivery_job = await self._delivery_job_service.get(request.delivery_job_id)

            if delivery_job is None:
                raise ApplicationException(
                    Exceptions.NotFoundException,
                    self._error_message,
                    [f"Delivery job with id {request.delivery_job_id} not found."],
                )

            try:
                delivery_job.assign_driver(request.driver_id)
            except ValueError as e:
                raise ApplicationException(
                    Exceptions.BadRequestException, self._error_message, [
                        f"{e}"]
                )

            for waypoint in delivery_job.waypoints:
                if waypoint.waypoint_type is WaypointType.DROP_OFF:
                    continue

                order = await self._order_service.get(waypoint.order_id)
                assert order is not None

                try:
                    order.assign_driver(request.driver_id)
                    await self._uow.order_repository.save(order)
                except ValueError as e:
                    raise ApplicationException(
                        Exceptions.BadRequestException, self._error_message, [
                            f"{e}"]
                    )

            await self._uow.delivery_job_repository.save(delivery_job)
            delivery_job_dto = await self._delivery_job_service.to_dto(delivery_job)

        return BaseResponse[DeliveryJobDto].success(
            self._success_message, delivery_job_dto
        )
