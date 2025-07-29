from ed_domain.documentation.api.abc_endpoint_descriptions import \
    ABCEndpointDescriptions
from ed_domain.documentation.api.definitions import (EndpointDescription,
                                                     HttpMethod)

from ed_optimization.application.features.order.dtos import (
    CalculateOrderDetailsDto, RouteInformationDto)
from ed_optimization.application.features.order.dtos.create_order_dto import \
    CreateOrderDto


class OptimizationEndpointDescriptions(ABCEndpointDescriptions):
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._descriptions: list[EndpointDescription] = [
            {
                "name": "create_order",
                "method": HttpMethod.POST,
                "path": f"{self._base_url}/orders",
                "request_model": CreateOrderDto,
            },
            {
                "name": "calculate_order_details",
                "method": HttpMethod.POST,
                "path": f"{self._base_url}/orders/calculate",
                "request_model": CalculateOrderDetailsDto,
                "response_model": RouteInformationDto,
            },
        ]

    @property
    def descriptions(self) -> list[EndpointDescription]:
        return self._descriptions
