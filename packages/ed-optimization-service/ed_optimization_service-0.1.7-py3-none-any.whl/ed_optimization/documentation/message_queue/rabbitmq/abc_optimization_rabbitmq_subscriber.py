from abc import ABCMeta, abstractmethod
from enum import StrEnum

from ed_optimization.application.features.order.dtos.create_order_dto import \
    CreateOrderDto


class OptimizationQueues(StrEnum):
    CREATE_ORDER = "optimization.create_order"


class ABCOptimizationRabbitMQSubscriber(metaclass=ABCMeta):
    @abstractmethod
    async def create_order(self, create_order_dto: CreateOrderDto) -> None: ...
