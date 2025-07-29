from datetime import UTC, datetime, timedelta
from uuid import UUID

from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.core.aggregate_roots import Consumer, Order
from ed_domain.core.entities import Otp, Waypoint
from ed_domain.core.entities.notification import NotificationType
from ed_domain.core.entities.otp import OtpType
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from ed_domain.utils.otp import ABCOtpGenerator
from ed_notification.application.features.notification.dtos import \
    NotificationDto
from ed_notification.documentation.api.notification_api_client import \
    ABCNotificationApiClient

from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.features.common.dtos.create_consumer_dto import \
    CreateConsumerDto
from ed_core.common.generic_helpers import get_new_id


async def create_otp(
    user_id: UUID, otp_type: OtpType, uow: ABCAsyncUnitOfWork, otp: ABCOtpGenerator
) -> str:
    new_otp = otp.generate()
    await uow.otp_repository.create(
        Otp(
            id=get_new_id(),
            user_id=user_id,
            value=new_otp,
            otp_type=otp_type,
            expiry_datetime=datetime.now(UTC) + timedelta(minutes=5),
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
    )

    return new_otp


async def send_notification(
    user_id: UUID,
    message: str,
    notification_api: ABCNotificationApiClient,
    error_message: str,
) -> NotificationDto:
    notification_response = await notification_api.send_notification(
        {
            "user_id": user_id,
            "notification_type": NotificationType.EMAIL,
            "message": message,
        }
    )

    if not notification_response["is_success"]:
        raise ApplicationException(
            Exceptions.InternalServerException,
            error_message,
            [
                f"Failed to send notification to user with id {user_id}.",
                notification_response["message"],
            ],
        )

    return notification_response["data"]


async def get_order(
    order_id: UUID,
    uow: ABCAsyncUnitOfWork,
    error_message: str,
) -> Order:
    order = await uow.order_repository.get(id=order_id)
    if not order:
        raise ApplicationException(
            Exceptions.NotFoundException,
            error_message,
            [f"Order with id {order_id} not found."],
        )

    return order


async def get_order_waypoint(
    delivery_job_id: UUID,
    order_id: UUID,
    uow: ABCAsyncUnitOfWork,
    error_message: str,
) -> Waypoint:
    waypoint = await uow.waypoint_repository.get(
        order_id=order_id, delivery_job_id=delivery_job_id
    )

    if waypoint is None:
        raise ApplicationException(
            Exceptions.BadRequestException,
            error_message,
            [f"Order with id {order_id} is not in the delivery job waypoints."],
        )

    return waypoint


async def create_or_get_consumer(
    consumer: CreateConsumerDto, uow: ABCAsyncUnitOfWork
) -> Consumer:
    if existing_consumer := await uow.consumer_repository.get(user_id=consumer.user_id):
        return existing_consumer

    return await consumer.create_consumer(uow)
