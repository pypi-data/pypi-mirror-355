from typing import Type

from ed_domain.common.logging import get_logger
from ed_infrastructure.documentation.message_queue.rabbitmq.rabbitmq_multiple_queue_producers import \
    RabbitMQMultipleQueuesProducer

from ed_core.application.features.delivery_job.dtos.create_delivery_job_dto import \
    CreateDeliveryJobDto
from ed_core.documentation.message_queue.rabbitmq.abc_core_rabbitmq_subscriber import (  # Assuming CoreQueues enum exists
    ABCCoreRabbitMQSubscriber, CoreQueues)
from ed_core.documentation.message_queue.rabbitmq.core_queue_descriptions import \
    CoreQueueDescriptions

LOG = get_logger()


class CoreRabbitMQSubscriber(ABCCoreRabbitMQSubscriber):
    def __init__(self, connection_url: str) -> None:
        self._connection_url = connection_url
        self._queue_descriptions = CoreQueueDescriptions(
            connection_url).descriptions

        all_core_queue_names = []
        producer_generic_model: Type[object] = object

        for desc in self._queue_descriptions:
            if "name" in desc and "request_model" in desc:
                all_core_queue_names.append(
                    desc["connection_parameters"]["queue"])

                if desc["request_model"] == CreateDeliveryJobDto:
                    producer_generic_model = CreateDeliveryJobDto

        if all_core_queue_names:
            producer_url = self._queue_descriptions[0]["connection_parameters"]["url"]
            self._core_producer = RabbitMQMultipleQueuesProducer[
                producer_generic_model
            ](
                url=producer_url,
                queues=all_core_queue_names,
            )
        else:
            LOG.warning(
                "No core queue descriptions found. Core producer not initialized."
            )
            self._core_producer = None

    async def create_delivery_job(
        self, create_delivery_job_dto: CreateDeliveryJobDto
    ) -> None:
        if not self._core_producer:
            LOG.error(
                "Core producer not initialized. Cannot create delivery job.")
            raise RuntimeError(
                "RabbitMQ producer not available for delivery job creation."
            )

        target_queue = CoreQueues.CREATE_DELIVERY_JOB.value
        LOG.info(
            f"Publishing create_delivery_job_dto to {target_queue} queue: {create_delivery_job_dto}"
        )
        await self._core_producer.publish(create_delivery_job_dto, target_queue)

    async def start(self) -> None:
        LOG.info("Starting Core RabbitMQ producer.")
        if self._core_producer:
            try:
                await self._core_producer.start()
                LOG.info(
                    f"Core producer started and declared queues: {self._core_producer._queues}"
                )
            except Exception as e:
                LOG.error(f"Failed to start Core producer: {e}")
                raise
        else:
            LOG.info("No Core producer to start.")

    def stop_producers(self) -> None:
        LOG.info("Stopping Core RabbitMQ producer.")
        if self._core_producer:
            self._core_producer.stop()
        else:
            LOG.info("No Core producer to stop.")
