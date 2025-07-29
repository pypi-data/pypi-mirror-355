from dataclasses import dataclass

from rmediator.decorators import request
from rmediator.mediator import Request

from ed_optimization.application.common.responses.base_response import \
    BaseResponse
from ed_optimization.application.features.order.dtos import (
    CalculateOrderDetailsDto, RouteInformationDto)


@request(BaseResponse[RouteInformationDto])
@dataclass
class CalculateOrderDetailsCommand(Request):
    dto: CalculateOrderDetailsDto
