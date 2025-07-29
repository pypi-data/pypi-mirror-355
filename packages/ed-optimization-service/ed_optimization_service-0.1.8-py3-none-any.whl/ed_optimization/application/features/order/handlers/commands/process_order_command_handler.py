from ed_domain.core.aggregate_roots import Order
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_optimization.application.common.responses.base_response import \
    BaseResponse
from ed_optimization.application.contracts.infrastructure.cache.abc_cache import \
    ABCCache
from ed_optimization.application.contracts.infrastructure.google.abc_google_maps_route_api import \
    ABCGoogleMapsRoutesAPI
from ed_optimization.application.features.order.requests.commands import \
    ProcessOrderCommand
from ed_optimization.application.services.order_processing_service import \
    OrderProcessingService
from ed_optimization.common.logging_helpers import get_logger

LOG = get_logger()


@request_handler(ProcessOrderCommand, BaseResponse[None])
class ProcessOrderCommandHandler(RequestHandler):
    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
        cache: ABCCache[list[Order]],
        google_maps_api: ABCGoogleMapsRoutesAPI,
    ):
        self._order_processing_service = OrderProcessingService(
            uow, cache, google_maps_api
        )

    async def handle(self, request: ProcessOrderCommand) -> BaseResponse[None]:
        LOG.info(
            f"Handler received command for order ID: {request.model['id']}")
        await self._order_processing_service.process_incoming_order(request.model)
        return BaseResponse[None].success(
            message="Order processing request received successfully",
            data=None,
        )
