from typing import Type

from ed_domain.common.logging import get_logger
from ed_infrastructure.documentation.message_queue.rabbitmq.rabbitmq_multiple_queue_producers import \
    RabbitMQMultipleQueuesProducer

from ed_optimization.application.features.order.dtos.create_order_dto import \
    CreateOrderDto
from ed_optimization.documentation.message_queue.rabbitmq.abc_optimization_rabbitmq_subscriber import (
    ABCOptimizationRabbitMQSubscriber, OptimizationQueues)
from ed_optimization.documentation.message_queue.rabbitmq.optimization_queue_descriptions import \
    OptimizationQueueDescriptions

LOG = get_logger()


class OptimizationRabbitMQSubscriber(ABCOptimizationRabbitMQSubscriber):
    def __init__(self, connection_url: str) -> None:
        self._connection_url = connection_url
        self._queue_descriptions = OptimizationQueueDescriptions(
            connection_url
        ).descriptions

        all_optimization_queue_names = []
        producer_generic_model: Type[object] = object

        for desc in self._queue_descriptions:
            if "request_model" in desc:
                all_optimization_queue_names.append(
                    desc["connection_parameters"]["queue"]
                )
                if desc["request_model"] == CreateOrderDto:
                    producer_generic_model = (
                        CreateOrderDto  # Or a common base class if applicable
                    )

        if all_optimization_queue_names:
            producer_url = self._queue_descriptions[0]["connection_parameters"]["url"]
            self._optimization_producer = RabbitMQMultipleQueuesProducer[
                producer_generic_model
            ](
                url=producer_url,
                queues=all_optimization_queue_names,  # Pass the list of all queues
            )
        else:
            LOG.warning(
                "No optimization queue descriptions found. Optimization producer not initialized."
            )
            self._optimization_producer = None

    async def create_order(self, create_order_dto: CreateOrderDto) -> None:
        if not self._optimization_producer:
            LOG.error(
                "Optimization producer not initialized. Cannot create order.")
            raise RuntimeError(
                "RabbitMQ producer not available for order creation.")

        target_queue = OptimizationQueues.CREATE_ORDER.value
        LOG.info(
            f"Publishing create_order_dto to {target_queue} queue: {create_order_dto}"
        )
        await self._optimization_producer.publish(create_order_dto, target_queue)

    async def start(self) -> None:
        LOG.info("Starting Optimization RabbitMQ producer.")
        if self._optimization_producer:
            try:
                await self._optimization_producer.start()
                LOG.info(
                    f"Optimization producer started and declared queues: {self._optimization_producer._queues}"
                )
            except Exception as e:
                LOG.error(f"Failed to start Optimization producer: {e}")
                raise
        else:
            LOG.info("No Optimization producer to start.")

    def stop_producers(self) -> None:
        LOG.info("Stopping Optimization RabbitMQ producer.")
        if self._optimization_producer:
            self._optimization_producer.stop()
        else:
            LOG.info("No Optimization producer to stop.")
