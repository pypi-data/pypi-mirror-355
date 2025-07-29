from abc import ABCMeta, abstractmethod

from ed_core.documentation.message_queue.rabbitmq.abc_core_rabbitmq_subscriber import \
    ABCCoreRabbitMQSubscriber


class ABCRabbitMQProducers(metaclass=ABCMeta):
    @property
    @abstractmethod
    def core(self) -> ABCCoreRabbitMQSubscriber: ...
