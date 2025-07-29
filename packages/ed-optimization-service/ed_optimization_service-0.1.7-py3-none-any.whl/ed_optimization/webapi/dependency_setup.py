from typing import Annotated

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from ed_infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork
from fastapi import Depends
from rmediator.mediator import Mediator

from ed_optimization.application.contracts.infrastructure.cache.abc_cache import \
    ABCCache
from ed_optimization.application.contracts.infrastructure.google.abc_google_maps_route_api import \
    ABCGoogleMapsRoutesAPI
from ed_optimization.application.contracts.infrastructure.message_queue.abc_rabbitmq_producers import \
    ABCRabbitMQProducers
from ed_optimization.application.features.order.handlers.commands import (
    CalculateOrderDetailsCommandHandler, ProcessOrderCommandHandler)
from ed_optimization.application.features.order.requests.commands import (
    CalculateOrderDetailsCommand, ProcessOrderCommand)
from ed_optimization.common.generic_helpers import get_config
from ed_optimization.common.typing.config import Config
from ed_optimization.infrastructure.cache.in_memory_cache import InMemoryCache
from ed_optimization.infrastructure.google_maps.google_maps_routes_api import \
    GoogleMapsRoutesAPI
from ed_optimization.infrastructure.message_queue.rabbitmq_producers import \
    RabbitMQProducers


def get_google_maps_api(
    config: Annotated[Config, Depends(get_config)],
) -> ABCGoogleMapsRoutesAPI:
    return GoogleMapsRoutesAPI(config["google_maps_api"])


def get_cache() -> ABCCache:
    return InMemoryCache()


def get_uow(config: Annotated[Config, Depends(get_config)]) -> ABCAsyncUnitOfWork:
    return UnitOfWork(config["db"])


def get_rabbitmq_producers(
    config: Annotated[Config, Depends(get_config)],
) -> ABCRabbitMQProducers:
    return RabbitMQProducers(config)


def mediator(
    google_maps_api: Annotated[ABCGoogleMapsRoutesAPI, Depends(get_google_maps_api)],
    uow: Annotated[ABCAsyncUnitOfWork, Depends(get_uow)],
    cache: Annotated[ABCCache, Depends(get_cache)],
) -> Mediator:
    mediator = Mediator()

    handlers = [
        (
            ProcessOrderCommand,
            ProcessOrderCommandHandler(uow, cache, google_maps_api),
        ),
        (
            CalculateOrderDetailsCommand,
            CalculateOrderDetailsCommandHandler(uow, google_maps_api),
        ),
    ]
    for command, handler in handlers:
        mediator.register_handler(command, handler)

    return mediator
