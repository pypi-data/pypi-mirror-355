from typing import Annotated

from fastapi import Depends

from ed_core.application.contracts.infrastructure.abc_rabbitmq_producers import \
    ABCRabbitMQProducers
from ed_core.common.generic_helpers import get_config
from ed_core.common.typing.config import Config
from ed_core.infrastructure.api.rabbitmq_handler import RabbitMQHandler


async def get_rabbitmq_handler(
    config: Annotated[Config, Depends(get_config)],
) -> ABCRabbitMQProducers:
    handler = RabbitMQHandler(config["rabbitmq"])
    await handler.start()

    return handler
