from datetime import UTC, datetime

from ed_core.common.generic_helpers import get_new_id
from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import DeliveryJob
from ed_domain.core.aggregate_roots.delivery_job import DeliveryJobStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_optimization.application.services.abc_service import ABCService
from ed_optimization.application.services.waypoint_service import \
    WaypointService

LOG = get_logger()


class DeliveryJobService(
    ABCService[
        DeliveryJob,
        None,
        None,
        None,
    ]
):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("DeliveryJob", uow.delivery_job_repository)

        self._uow = uow
        self._waypoint_service = WaypointService(uow)

        LOG.info("DeliveryJobService initialized with UnitOfWork.")

    async def create_default(self) -> DeliveryJob:
        delivery_job = DeliveryJob(
            id=get_new_id(),
            waypoints=[],
            estimated_distance_in_kms=0,
            estimated_time_in_minutes=0,
            status=DeliveryJobStatus.AVAILABLE,
            estimated_payment_in_birr=0,
            estimated_completion_time=datetime.now(UTC),
            create_datetime=datetime.now(UTC),
            update_datetime=datetime.now(UTC),
            deleted=False,
            deleted_datetime=None,
        )
        delivery_job = await self._repository.create(delivery_job)
        LOG.info(f"DeliveryJob created with ID: {delivery_job.id}")
        return delivery_job
