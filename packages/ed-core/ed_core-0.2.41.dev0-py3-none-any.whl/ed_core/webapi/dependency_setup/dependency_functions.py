from typing import Annotated

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from ed_domain.utils.otp.abc_otp_generator import ABCOtpGenerator
from ed_domain.utils.security.password.abc_password_handler import \
    ABCPasswordHandler
from ed_infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork
from ed_infrastructure.utils.otp.otp_generator import OtpGenerator
from ed_infrastructure.utils.password.password_handler import PasswordHandler
from fastapi import Depends
from rmediator.mediator import Mediator

from ed_core.application.contracts.infrastructure.api.abc_api import ABCApi
from ed_core.application.contracts.infrastructure.email.abc_email_templater import \
    ABCEmailTemplater
from ed_core.application.features.business.handlers.commands import (
    CreateApiKeyCommandHandler, CreateBusinessCommandHandler,
    CreateOrderCommandHandler, UpdateBusinessCommandHandler)
from ed_core.application.features.business.handlers.queries import (
    GetAllBusinessesQueryHandler, GetBusinessApiKeysQueryHandler,
    GetBusinessByUserIdQueryHandler, GetBusinessOrdersQueryHandler,
    GetBusinessQueryHandler, GetBusinessReportQueryHandler)
from ed_core.application.features.business.requests.commands import (
    CreateApiKeyCommand, CreateBusinessCommand, CreateOrderCommand,
    UpdateBusinessCommand)
from ed_core.application.features.business.requests.queries import (
    GetAllBusinessQuery, GetBusinessApiKeysQuery, GetBusinessByUserIdQuery,
    GetBusinessOrdersQuery, GetBusinessQuery, GetBusinessReportQuery)
from ed_core.application.features.consumer.handlers.commands import (
    CreateConsumerCommandHandler, UpdateConsumerCommandHandler)
from ed_core.application.features.consumer.handlers.queries import (
    GetConsumerByUserIdQueryHandler, GetConsumerOrdersQueryHandler,
    GetConsumerQueryHandler, GetConsumersQueryHandler)
from ed_core.application.features.consumer.requests.commands import (
    CreateConsumerCommand, UpdateConsumerCommand)
from ed_core.application.features.consumer.requests.queries import (
    GetConsumerByUserIdQuery, GetConsumerOrdersQuery, GetConsumerQuery,
    GetConsumersQuery)
from ed_core.application.features.delivery_job.handlers.commands import (
    CancelDeliveryJobCommandHandler, ClaimDeliveryJobCommandHandler,
    CreateDeliveryJobCommandHandler)
from ed_core.application.features.delivery_job.handlers.queries import (
    GetDeliveryJobQueryHandler, GetDeliveryJobsQueryHandler)
from ed_core.application.features.delivery_job.requests.commands import (
    CancelDeliveryJobCommand, ClaimDeliveryJobCommand,
    CreateDeliveryJobCommand)
from ed_core.application.features.delivery_job.requests.queries import (
    GetDeliveryJobQuery, GetDeliveryJobsQuery)
from ed_core.application.features.driver.handlers.commands import (
    CreateDriverCommandHandler, FinishOrderDeliveryCommandHandler,
    FinishOrderPickUpCommandHandler, StartOrderDeliveryCommandHandler,
    StartOrderPickUpCommandHandler, UpdateDriverCommandHandler,
    UpdateDriverCurrentLocationCommandHandler)
from ed_core.application.features.driver.handlers.queries import (
    GetAllDriversQueryHandler, GetDriverByUserIdQueryHandler,
    GetDriverDeliveryJobsQueryHandler, GetDriverOrdersQueryHandler,
    GetDriverPaymentSummaryQueryHandler, GetDriverQueryHandler)
from ed_core.application.features.driver.requests.commands import (
    CreateDriverCommand, FinishOrderDeliveryCommand, FinishOrderPickUpCommand,
    StartOrderDeliveryCommand, StartOrderPickUpCommand, UpdateDriverCommand,
    UpdateDriverCurrentLocationCommand)
from ed_core.application.features.driver.requests.queries import (
    GetAllDriversQuery, GetDriverByUserIdQuery, GetDriverDeliveryJobsQuery,
    GetDriverOrdersQuery, GetDriverPaymentSummaryQuery, GetDriverQuery)
from ed_core.application.features.notification.handlers.queries import \
    GetNotificationsQueryHandler
from ed_core.application.features.notification.requests.queries import \
    GetNotificationsQuery
from ed_core.application.features.order.handlers.commands import \
    CancelOrderCommandHandler
from ed_core.application.features.order.handlers.queries import (
    GetOrderQueryHandler, GetOrdersQueryHandler, TrackOrderQueryHandler)
from ed_core.application.features.order.requests.commands import \
    CancelOrderCommand
from ed_core.application.features.order.requests.queries import (
    GetOrderQuery, GetOrdersQuery, TrackOrderQuery)
from ed_core.common.generic_helpers import get_config
from ed_core.common.typing.config import Config, Environment
from ed_core.infrastructure.api.api_handler import ApiHandler
from ed_core.infrastructure.email.email_templater import EmailTemplater


def get_password(config: Annotated[Config, Depends(get_config)]) -> ABCPasswordHandler:
    return PasswordHandler(config["hash_scheme"])


def get_otp_generator(
    config: Annotated[Config, Depends(get_config)],
) -> ABCOtpGenerator:
    return OtpGenerator(dev_mode=config["environment"] == Environment.DEV)


def get_api(config: Annotated[Config, Depends(get_config)]) -> ABCApi:
    return ApiHandler(config)


def get_uow(config: Annotated[Config, Depends(get_config)]) -> ABCAsyncUnitOfWork:
    return UnitOfWork(config["db"])


def email_templater() -> ABCEmailTemplater:
    return EmailTemplater()


def mediator(
    email_templater: Annotated[ABCEmailTemplater, Depends(email_templater)],
    password: Annotated[ABCPasswordHandler, Depends(get_password)],
    uow: Annotated[ABCAsyncUnitOfWork, Depends(get_uow)],
    api: Annotated[ABCApi, Depends(get_api)],
    otp: Annotated[ABCOtpGenerator, Depends(get_otp_generator)],
) -> Mediator:
    mediator = Mediator()

    handlers = [
        # Delivery job handler
        (CreateDeliveryJobCommand, CreateDeliveryJobCommandHandler(uow)),
        (ClaimDeliveryJobCommand, ClaimDeliveryJobCommandHandler(uow)),
        (GetDeliveryJobsQuery, GetDeliveryJobsQueryHandler(uow)),
        (GetDeliveryJobQuery, GetDeliveryJobQueryHandler(uow)),
        # Driver handlers
        (CreateDriverCommand, CreateDriverCommandHandler(uow)),
        (GetAllDriversQuery, GetAllDriversQueryHandler(uow)),
        (GetDriverOrdersQuery, GetDriverOrdersQueryHandler(uow)),
        (GetDriverDeliveryJobsQuery, GetDriverDeliveryJobsQueryHandler(uow)),
        (GetDriverQuery, GetDriverQueryHandler(uow)),
        (GetDriverByUserIdQuery, GetDriverByUserIdQueryHandler(uow)),
        (GetDriverPaymentSummaryQuery, GetDriverPaymentSummaryQueryHandler(uow)),
        (StartOrderDeliveryCommand, StartOrderDeliveryCommandHandler(uow, api, otp)),
        (
            FinishOrderDeliveryCommand,
            FinishOrderDeliveryCommandHandler(uow, api),
        ),
        (StartOrderPickUpCommand, StartOrderPickUpCommandHandler(uow, api, otp)),
        (
            FinishOrderPickUpCommand,
            FinishOrderPickUpCommandHandler(uow, api),
        ),
        (UpdateDriverCommand, UpdateDriverCommandHandler(uow)),
        (
            UpdateDriverCurrentLocationCommand,
            UpdateDriverCurrentLocationCommandHandler(uow),
        ),
        (CancelDeliveryJobCommand, CancelDeliveryJobCommandHandler(uow)),
        # Business handlers
        (CreateBusinessCommand, CreateBusinessCommandHandler(uow)),
        (CreateOrderCommand, CreateOrderCommandHandler(uow, api, email_templater)),
        (GetBusinessQuery, GetBusinessQueryHandler(uow)),
        (GetBusinessByUserIdQuery, GetBusinessByUserIdQueryHandler(uow)),
        (GetBusinessOrdersQuery, GetBusinessOrdersQueryHandler(uow)),
        (GetAllBusinessQuery, GetAllBusinessesQueryHandler(uow)),
        (UpdateBusinessCommand, UpdateBusinessCommandHandler(uow)),
        (TrackOrderQuery, TrackOrderQueryHandler(uow)),
        (GetBusinessApiKeysQuery, GetBusinessApiKeysQueryHandler(uow)),
        (CreateApiKeyCommand, CreateApiKeyCommandHandler(uow, password)),
        (GetBusinessReportQuery, GetBusinessReportQueryHandler(uow)),
        # Order handlers
        (GetOrdersQuery, GetOrdersQueryHandler(uow)),
        (GetOrderQuery, GetOrderQueryHandler(uow)),
        (CancelOrderCommand, CancelOrderCommandHandler(uow)),
        # Consumer handlers
        (CreateConsumerCommand, CreateConsumerCommandHandler(uow)),
        (UpdateConsumerCommand, UpdateConsumerCommandHandler(uow)),
        (GetConsumersQuery, GetConsumersQueryHandler(uow)),
        (GetConsumerQuery, GetConsumerQueryHandler(uow)),
        (GetConsumerByUserIdQuery, GetConsumerByUserIdQueryHandler(uow)),
        (GetConsumerOrdersQuery, GetConsumerOrdersQueryHandler(uow)),
        # Notification handlers
        (GetNotificationsQuery, GetNotificationsQueryHandler(uow)),
    ]

    for command, handler in handlers:
        mediator.register_handler(command, handler)

    return mediator
