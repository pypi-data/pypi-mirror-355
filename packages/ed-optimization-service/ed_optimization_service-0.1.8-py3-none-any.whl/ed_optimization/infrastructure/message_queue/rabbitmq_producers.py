from ed_core.documentation.message_queue.rabbitmq.abc_core_rabbitmq_subscriber import \
    ABCCoreRabbitMQSubscriber

from ed_optimization.application.contracts.infrastructure.message_queue.abc_rabbitmq_producers import \
    ABCRabbitMQProducers
from ed_optimization.common.typing.config import Config


class RabbitMQProducers(ABCRabbitMQProducers):
    def __init__(self, config: Config) -> None:
        # self._core = CoreRabbitMQSubscriber(config["rabbitmq"]["url"])
        ...

    @property
    def core(self) -> ABCCoreRabbitMQSubscriber: ...
