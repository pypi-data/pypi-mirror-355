from ed_domain.documentation.api.definitions import ApiResponse
from ed_infrastructure.documentation.api.endpoint_client import EndpointClient

from ed_optimization.application.features.order.dtos import (
    CalculateOrderDetailsDto, CreateOrderDto, RouteInformationDto)
from ed_optimization.documentation.api.abc_optimization_api_client import \
    ABCOptimizationApiClient
from ed_optimization.documentation.api.optimization_endpoint_descriptions import \
    OptimizationEndpointDescriptions


class OptimizationApiClient(ABCOptimizationApiClient):
    def __init__(self, core_api: str) -> None:
        self._endpoints = OptimizationEndpointDescriptions(core_api)

    async def create_order(self, create_order_dto: CreateOrderDto) -> ApiResponse[None]:
        endpoint = self._endpoints.get_description("create_order")
        api_client = EndpointClient[None](endpoint)

        return await api_client({"request": create_order_dto})

    async def calcualte_order_details(
        self, calculate_order_details_dto: CalculateOrderDetailsDto
    ) -> ApiResponse[RouteInformationDto]:
        endpoint = self._endpoints.get_description("calculate_order_details")
        api_client = EndpointClient[RouteInformationDto](endpoint)

        return await api_client({"request": calculate_order_details_dto})
