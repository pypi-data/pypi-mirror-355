from typing import TypedDict
from uuid import UUID


class CalculateOrderDetailsDto(TypedDict):
    business_location_id: UUID
    consumer_location_id: UUID
