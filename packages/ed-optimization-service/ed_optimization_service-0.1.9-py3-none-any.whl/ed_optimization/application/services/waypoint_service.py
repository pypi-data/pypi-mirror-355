from datetime import UTC, datetime
from uuid import UUID

from ed_core.application.features.common.dtos.waypoint_dto import WaypointDto
from ed_core.common.generic_helpers import get_new_id
from ed_domain.common.logging import get_logger
from ed_domain.core.entities.waypoint import (Waypoint, WaypointStatus,
                                              WaypointType)
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from pydantic import BaseModel

from ed_optimization.application.services.abc_service import ABCService

LOG = get_logger()


class CreateWaypointModel(BaseModel):
    delivery_job_id: UUID
    order_id: UUID
    expected_arrival_time: datetime
    sequence: int
    waypoint_type: WaypointType
    waypoint_status: WaypointStatus


class WaypointService(ABCService[Waypoint, CreateWaypointModel, None, WaypointDto]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Waypoint", uow.waypoint_repository)

        LOG.info("WaypointService initialized with UnitOfWork.")

    async def create_waypoint(self, dto: CreateWaypointModel) -> Waypoint:
        waypoint = Waypoint(
            id=get_new_id(),
            delivery_job_id=dto.delivery_job_id,
            order_id=dto.order_id,
            expected_arrival_time=dto.expected_arrival_time,
            actual_arrival_time=datetime.now(UTC),
            sequence=dto.sequence,
            waypoint_type=dto.waypoint_type,
            waypoint_status=dto.waypoint_status,
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        waypoint = await self._repository.create(waypoint)
        LOG.info(f"Waypoint created with ID: {waypoint.id}")
        return waypoint
