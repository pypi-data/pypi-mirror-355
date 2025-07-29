from typing import Annotated

from fastapi import Depends
from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit.schemas import RabbitQueue
from rmediator.mediator import Mediator

from ed_optimization.application.features.order.dtos.create_order_dto import \
    CreateOrderDto
from ed_optimization.application.features.order.requests.commands.process_order_command import \
    ProcessOrderCommand
from ed_optimization.common.generic_helpers import get_config
from ed_optimization.common.logging_helpers import get_logger
from ed_optimization.webapi.dependency_setup import mediator

config = get_config()
router = RabbitRouter(config["rabbitmq"]["url"])
queue = RabbitQueue(name=config["rabbitmq"]["queue"], durable=True)

LOG = get_logger()


@router.subscriber(queue)
async def create_order(
    model: CreateOrderDto,
    mediator: Annotated[Mediator, Depends(mediator)],
):
    return await mediator.send(ProcessOrderCommand(model=model))
