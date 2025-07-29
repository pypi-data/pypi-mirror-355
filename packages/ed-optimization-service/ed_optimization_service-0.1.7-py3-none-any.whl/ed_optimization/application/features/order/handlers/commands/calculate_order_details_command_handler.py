from ed_domain.core.aggregate_roots import Order
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_optimization.application.common.responses.base_response import \
    BaseResponse
from ed_optimization.application.contracts.infrastructure.api.abc_api import \
    ABCApi
from ed_optimization.application.contracts.infrastructure.cache.abc_cache import \
    ABCCache
from ed_optimization.application.contracts.infrastructure.google.abc_google_maps_route_api import \
    ABCGoogleMapsRoutesAPI
from ed_optimization.application.features.order.dtos.route_information_dto import \
    RouteInformationDto
from ed_optimization.application.features.order.requests.commands import \
    CalculateOrderDetailsCommand
from ed_optimization.application.services.location_service import \
    LocationService
from ed_optimization.common.logging_helpers import get_logger

LOG = get_logger()


@request_handler(CalculateOrderDetailsCommand, BaseResponse[RouteInformationDto])
class CalculateOrderDetailsCommandHandler(RequestHandler):
    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
        google_maps_api: ABCGoogleMapsRoutesAPI,
    ):
        self._uow = uow
        self._google_maps_api = google_maps_api
        self._location_service = LocationService(uow)

        self._success_message = "Order details calculated succesfully."

    async def handle(
        self, request: CalculateOrderDetailsCommand
    ) -> BaseResponse[RouteInformationDto]:
        async with self._uow.transaction():
            business = await self._location_service.get(
                request.dto["business_location_id"]
            )
            assert business is not None

            consumer = await self._location_service.get(
                request.dto["consumer_location_id"]
            )
            assert consumer is not None

        route_information = await self._google_maps_api.get_route(business, consumer)
        dto: RouteInformationDto = {
            "distance_kms": round(
                (
                    route_information["distance_meters"]
                    if "distance_meters" in route_information
                    else 0
                )
                / 1000,
                2,
            ),
            "duration_minutes": round(route_information["duration_seconds"] / 60),
        }

        return BaseResponse[RouteInformationDto].success(self._success_message, dto)
