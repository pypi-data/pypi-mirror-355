from abc import ABCMeta, abstractmethod

from ed_domain.documentation.api.definitions import ApiResponse

from ed_optimization.application.features.order.dtos import (
    CalculateOrderDetailsDto, CreateOrderDto, RouteInformationDto)


class ABCOptimizationApiClient(metaclass=ABCMeta):
    @abstractmethod
    async def create_order(
        self, create_order_dto: CreateOrderDto
    ) -> ApiResponse[None]: ...

    @abstractmethod
    async def calcualte_order_details(
        self, calculate_order_details_dto: CalculateOrderDetailsDto
    ) -> ApiResponse[RouteInformationDto]: ...
